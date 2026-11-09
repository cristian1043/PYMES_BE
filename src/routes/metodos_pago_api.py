from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required
from src.controllers.metodos_pago_controller import MetodosPagoController
from src.utils.security import (
    roles_required,
    verificar_acceso_empresa,
    obtener_empresa_id_request,
    obtener_rol_en_empresa,
    es_super_admin_actual,
)

metodos_pago_bp = Blueprint("metodos_pago", __name__)


def validar_acceso_metodo(metodo):
    if not metodo:
        return False
    if not metodo.id_empresa:
        return True
    return verificar_acceso_empresa(metodo.id_empresa)


@metodos_pago_bp.route("/", methods=["GET"])
@jwt_required(optional=True)
def get_metodos_pago():
    empresa_id = obtener_empresa_id_request()
    metodos = MetodosPagoController.get(empresa_id=empresa_id)
    return jsonify([m.to_dict() for m in metodos]), 200


@metodos_pago_bp.route("/<int:id>", methods=["GET"])
@jwt_required(optional=True)
def get_metodo_pago_by_id(id):
    metodo = MetodosPagoController.get_by_id(id)
    if not metodo or metodo.estado != "Activo":
        return jsonify({"error": "Método de pago no encontrado"}), 404
    if not validar_acceso_metodo(metodo):
        return jsonify({"error": "Acceso denegado: El método de pago no corresponde a su empresa."}), 403

    incluir_privadas = False
    if request.args.get("incluir_claves") == "true":
        if es_super_admin_actual():
            incluir_privadas = True
        elif metodo.id_empresa:
            rol_id, _ = obtener_rol_en_empresa(metodo.id_empresa)
            if rol_id == 1:
                incluir_privadas = True

    return jsonify(metodo.to_dict(incluir_privadas=incluir_privadas)), 200


@metodos_pago_bp.route("/", methods=["POST"])
@jwt_required()
@roles_required("Administrador", 1)
def create_metodo_pago():
    data = request.get_json() or {}
    emp_id = data.get("id_empresa") or data.get("empresa_id") or obtener_empresa_id_request()
    if emp_id:
        if not verificar_acceso_empresa(emp_id):
            return jsonify({"exito": False, "mensaje": "No tienes permisos en esta empresa."}), 403
        data["id_empresa"] = int(emp_id)

    try:
        metodo = MetodosPagoController.create(data)
        return jsonify(metodo.to_dict(incluir_privadas=True)), 201
    except ValueError as ve:
        return jsonify({"exito": False, "mensaje": str(ve)}), 400


@metodos_pago_bp.route("/<int:id>", methods=["PUT"])
@jwt_required()
@roles_required("Administrador", 1)
def update_metodo_pago(id):
    metodo = MetodosPagoController.get_by_id(id)
    if not metodo:
        return jsonify({"error": "Método de pago no encontrado"}), 404
    if metodo.id_empresa is None and not es_super_admin_actual():
        return jsonify({"error": "No se puede modificar un método de pago global del sistema."}), 403
    if not validar_acceso_metodo(metodo):
        return jsonify({"error": "Acceso denegado: No tiene permisos sobre este método de pago."}), 403

    data = request.get_json() or {}
    metodo_actualizado = MetodosPagoController.update(id, data)
    return jsonify(metodo_actualizado.to_dict(incluir_privadas=True)), 200


@metodos_pago_bp.route("/<int:id>", methods=["DELETE"])
@jwt_required()
@roles_required("Administrador", 1)
def delete_metodo_pago(id):
    metodo = MetodosPagoController.get_by_id(id)
    if not metodo:
        return jsonify({"error": "Método de pago no encontrado"}), 404
    if metodo.id_empresa is None and not es_super_admin_actual():
        return jsonify({"error": "No se puede eliminar un método de pago global del sistema"}), 400
    if not validar_acceso_metodo(metodo):
        return jsonify({"error": "Acceso denegado: No tiene permisos sobre este método de pago."}), 403

    eliminado = MetodosPagoController.delete(id)
    if eliminado:
        return jsonify({"mensaje": "Método de pago desactivado correctamente"}), 200
    return jsonify({"error": "No se puede eliminar un método de pago global del sistema"}), 400
