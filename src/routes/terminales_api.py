from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required
from src.models.metodos_pago import MetodosPago
from src.models.terminales import Terminales
from src.services.pagos import CANALES, obtener_proveedor
from src.services.pagos.base import ErrorPasarela
from src.utils.security import roles_required, verificar_acceso_empresa, obtener_empresa_id_request

terminales_bp = Blueprint("terminales", __name__)

PROVEEDORES_DATAFONO = CANALES["datafono"]  # ('bold', 'simulado')


def _empresa_solicitada(data=None):
    data = data or {}
    emp_id = (
        data.get("id_empresa")
        or data.get("empresa_id")
        or obtener_empresa_id_request()
    )
    return int(emp_id) if emp_id and str(emp_id).isdigit() else None


def _tiene_acceso_empresa(id_empresa):
    return verificar_acceso_empresa(id_empresa)


def _validar_metodo(id_metodo, id_empresa):
    metodo = MetodosPago.get_by_id(int(id_metodo)) if str(id_metodo or "").isdigit() else None
    if not metodo or (metodo.estado or "Activo") != "Activo":
        raise ValueError("Selecciona un método de pago activo.")
    if metodo.id_empresa is not None and int(metodo.id_empresa) != int(id_empresa):
        raise ValueError("El método de pago no pertenece a esta empresa.")
    if (metodo.pasarela or "").lower() not in PROVEEDORES_DATAFONO:
        raise ValueError("El método de pago debe tener pasarela 'bold' o 'simulado' para usarse con datáfono.")
    return metodo


def _aplicar_campos(terminal, data, id_empresa):
    if "nombre" in data or terminal.nombre is None:
        nombre = str(data.get("nombre") or "").strip()
        if not nombre:
            raise ValueError("El nombre de la terminal es obligatorio (ej. 'Caja 1').")
        terminal.nombre = nombre[:100]
    if "id_metodo_pago" in data or terminal.id_metodo_pago is None:
        metodo = _validar_metodo(data.get("id_metodo_pago"), id_empresa)
        terminal.id_metodo_pago = metodo.id
        terminal.proveedor = metodo.pasarela.lower()
    for campo, largo in (("terminal_serial", 100), ("terminal_model", 50), ("email_usuario", 255)):
        if campo in data:
            valor = str(data.get(campo) or "").strip()
            setattr(terminal, campo, valor[:largo] or None)
    if "estado" in data and data["estado"] in ("Activo", "Inactivo"):
        terminal.estado = data["estado"]
    if terminal.proveedor == "bold":
        if not terminal.terminal_serial or not terminal.terminal_model:
            raise ValueError("Para Bold debes indicar el serial y el modelo del datáfono.")
        if not terminal.email_usuario:
            raise ValueError("Para Bold debes indicar el email del usuario Bold que opera el datáfono.")


@terminales_bp.route("/", methods=["GET"])
@jwt_required()
def get_terminales():
    empresa_id = _empresa_solicitada()
    if not empresa_id:
        return jsonify([]), 200
    if not _tiene_acceso_empresa(empresa_id):
        return jsonify({"mensaje": "Acceso denegado a las terminales de esta empresa."}), 403
    q = Terminales.get_query().filter(Terminales.id_empresa == int(empresa_id))
    if str(request.args.get("solo_activas") or "").lower() in ("true", "1", "yes"):
        q = q.filter((Terminales.estado == "Activo") | (Terminales.estado == None))
    return jsonify([t.to_dict() for t in q.order_by(Terminales.nombre.asc()).all()]), 200


@terminales_bp.route("/disponibles", methods=["GET"])
@jwt_required()
@roles_required("Administrador", 1)
def get_disponibles():
    id_metodo = request.args.get("id_metodo_pago")
    empresa_id = _empresa_solicitada()
    metodo = MetodosPago.get_by_id(int(id_metodo)) if str(id_metodo or "").isdigit() else None
    if not metodo:
        return jsonify({"mensaje": "Método de pago no encontrado."}), 404
    if metodo.id_empresa is not None and not _tiene_acceso_empresa(metodo.id_empresa):
        return jsonify({"mensaje": "Acceso denegado al método de pago."}), 403
    if empresa_id and metodo.id_empresa is not None and int(metodo.id_empresa) != int(empresa_id):
        return jsonify({"mensaje": "El método de pago no pertenece a esta empresa."}), 400
    if (metodo.pasarela or "").lower() not in PROVEEDORES_DATAFONO:
        return jsonify({"mensaje": "Este método de pago no maneja datáfonos."}), 400
    try:
        terminales = obtener_proveedor(metodo.pasarela).listar_terminales(metodo)
    except ErrorPasarela as e:
        return jsonify({"mensaje": str(e)}), 502
    return jsonify({"terminales": terminales}), 200


@terminales_bp.route("/", methods=["POST"])
@jwt_required()
@roles_required("Administrador", 1)
def create_terminal():
    data = request.get_json() or {}
    empresa_id = _empresa_solicitada(data)
    if not empresa_id:
        return jsonify({"mensaje": "Se requiere 'id_empresa'."}), 400
    if not _tiene_acceso_empresa(empresa_id):
        return jsonify({"mensaje": "Acceso denegado a esta empresa."}), 403
    terminal = Terminales()
    terminal.id_empresa = int(empresa_id)
    terminal.estado = "Activo"
    try:
        _aplicar_campos(terminal, data, terminal.id_empresa)
    except ValueError as ve:
        return jsonify({"mensaje": str(ve)}), 400
    terminal.create()
    return jsonify(terminal.to_dict()), 201


@terminales_bp.route("/<int:id>", methods=["PUT"])
@jwt_required()
@roles_required("Administrador", 1)
def update_terminal(id):
    terminal = Terminales.get_by_id(id)
    if not terminal:
        return jsonify({"mensaje": "Terminal no encontrada."}), 404
    if not _tiene_acceso_empresa(terminal.id_empresa):
        return jsonify({"mensaje": "Acceso denegado a esta terminal."}), 403
    data = request.get_json() or {}
    try:
        _aplicar_campos(terminal, data, terminal.id_empresa)
    except ValueError as ve:
        from src.models import session
        session.rollback()
        return jsonify({"mensaje": str(ve)}), 400
    terminal.update()
    return jsonify(terminal.to_dict()), 200


@terminales_bp.route("/<int:id>", methods=["DELETE"])
@jwt_required()
@roles_required("Administrador", 1)
def delete_terminal(id):
    terminal = Terminales.get_by_id(id)
    if not terminal:
        return jsonify({"mensaje": "Terminal no encontrada."}), 404
    if not _tiene_acceso_empresa(terminal.id_empresa):
        return jsonify({"mensaje": "Acceso denegado a esta terminal."}), 403
    terminal.estado = "Inactivo"
    terminal.update()
    return jsonify({"mensaje": "Terminal desactivada correctamente.", "terminal": terminal.to_dict()}), 200
