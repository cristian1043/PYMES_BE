from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt, get_jwt_identity
from src.controllers.metodos_pago_controller import MetodosPagoController
from src.utils.security import roles_required

metodos_pago_bp = Blueprint("metodos_pago", __name__)

def validar_acceso_metodo(metodo):
    if not metodo or not metodo.id_empresa:
        return True
    claims = get_jwt() or {}
    id_rol = claims.get("id_rol", 0)
    rol = claims.get("rol", "")
    if id_rol == 1 or rol == "Administrador":
        return True
    empresas = [int(e) for e in claims.get("empresas", []) if str(e).isdigit()]
    if int(metodo.id_empresa) in empresas:
        return True
    user_id = get_jwt_identity()
    from src.models.usuario_empresas import UsuarioEmpresas
    vinc = UsuarioEmpresas.get_by_usuario_empresa(user_id, metodo.id_empresa) if user_id else None
    return vinc is not None and vinc.estado == "Activo"

# ===========================
# Obtener métodos de pago (Globales + Empresa Activa)
# ===========================
@metodos_pago_bp.route("/", methods=["GET"])
@jwt_required(optional=True)
def get_metodos_pago():
    empresa_id = (
        request.args.get("empresa_id") or 
        request.args.get("id_empresa") or 
        request.headers.get("X-Empresa-ID") or 
        request.environ.get('tenant_empresa_id')
    )
    metodos = MetodosPagoController.get(empresa_id=empresa_id)
    return jsonify([m.to_dict() for m in metodos]), 200

# ===========================
# Obtener un método de pago por ID 
# ===========================
@metodos_pago_bp.route("/<int:id>", methods=["GET"])
@jwt_required(optional=True)
def get_metodo_pago_by_id(id):
    metodo = MetodosPagoController.get_by_id(id)
    if not metodo or metodo.estado != "Activo":
        return jsonify({"error": "Método de pago no encontrado"}), 404
    if not validar_acceso_metodo(metodo):
        return jsonify({"error": "Acceso denegado: El método de pago no corresponde a su empresa."}), 403
    
    # Permitir ver claves privadas solo a administradores con token válido
    incluir_privadas = False
    claims = get_jwt() or {}
    if claims and (claims.get("id_rol") == 1 or claims.get("rol") == "Administrador"):
        incluir_privadas = request.args.get("incluir_claves") == "true"

    return jsonify(metodo.to_dict(incluir_privadas=incluir_privadas)), 200

# ===========================
# Crear un nuevo método de pago (para la empresa activa)
# ===========================
@metodos_pago_bp.route("/", methods=["POST"])
@jwt_required()
@roles_required("Administrador", 1)
def create_metodo_pago():
    data = request.get_json() or {}
    if not data.get("id_empresa"):
        emp_id = (
            request.headers.get("X-Empresa-ID") or 
            request.args.get("empresa_id") or 
            request.args.get("id_empresa") or 
            request.environ.get('tenant_empresa_id')
        )
        if emp_id:
            data["id_empresa"] = emp_id

    try:
        metodo = MetodosPagoController.create(data)
        return jsonify(metodo.to_dict(incluir_privadas=True)), 201
    except ValueError as ve:
        return jsonify({"exito": False, "mensaje": str(ve)}), 400

# ===========================
# Actualizar un método de pago
# ===========================
@metodos_pago_bp.route("/<int:id>", methods=["PUT"])
@jwt_required()
@roles_required("Administrador", 1)
def update_metodo_pago(id):
    metodo = MetodosPagoController.get_by_id(id)
    if not metodo:
        return jsonify({"error": "Método de pago no encontrado"}), 404
    if not validar_acceso_metodo(metodo):
        return jsonify({"error": "Acceso denegado: No tiene permisos sobre este método de pago."}), 403

    data = request.get_json() or {}
    metodo_actualizado = MetodosPagoController.update(id, data)
    return jsonify(metodo_actualizado.to_dict(incluir_privadas=True)), 200

# ===========================
# Eliminar un método de pago
# ===========================
@metodos_pago_bp.route("/<int:id>", methods=["DELETE"])
@jwt_required()
@roles_required("Administrador", 1)
def delete_metodo_pago(id):
    metodo = MetodosPagoController.get_by_id(id)
    if not metodo:
        return jsonify({"error": "Método de pago no encontrado"}), 404
    if not validar_acceso_metodo(metodo):
        return jsonify({"error": "Acceso denegado: No tiene permisos sobre este método de pago."}), 403

    eliminado = MetodosPagoController.delete(id)
    if eliminado:
        return jsonify({"mensaje": "Método de pago desactivado correctamente"}), 200
    return jsonify({"error": "No se puede eliminar un método de pago global del sistema"}), 400