from flask import Blueprint, request, jsonify
from src.controllers.roles_controller import RolesController

roles_bp = Blueprint("roles", __name__)


# ===========================
# Obtener todos los roles
# ===========================
@roles_bp.route("/", methods=["GET"])
def get_roles():
    roles = RolesController.get()
    return jsonify(roles), 200


# ===========================
# Obtener un rol
# ===========================
@roles_bp.route("/<int:id>", methods=["GET"])
def get_rol(id):
    rol = RolesController.get_by_id(id)

    if rol:
        return jsonify(rol), 200

    return jsonify({
        "mensaje": "Rol no encontrado"
    }), 404


# ===========================
# Crear rol
# ===========================
@roles_bp.route("/", methods=["POST"])
def create_rol():
    data = request.get_json()

    rol = RolesController.create(data)

    return jsonify(rol), 201


# ===========================
# Actualizar rol
# ===========================
@roles_bp.route("/<int:id>", methods=["PUT"])
def update_rol(id):
    data = request.get_json()

    rol = RolesController.update(id, data)

    if rol:
        return jsonify(rol), 200

    return jsonify({
        "mensaje": "Rol no encontrado"
    }), 404


# ===========================
# Eliminar rol
# ===========================
@roles_bp.route("/<int:id>", methods=["DELETE"])
def delete_rol(id):

    eliminado = RolesController.delete(id)

    if eliminado:
        return jsonify({
            "mensaje": "Rol eliminado correctamente"
        }), 200

    return jsonify({
        "mensaje": "Rol no encontrado"
    }), 404