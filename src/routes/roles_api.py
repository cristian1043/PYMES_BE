from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required
from src.controllers.roles_controller import RolesController
from src.utils.security import roles_required

roles_bp = Blueprint("roles", __name__)

# ===========================
# Obtener todos los roles
# ===========================
@roles_bp.route("/", methods=["GET"])
@jwt_required()
def get_roles():
    roles = RolesController.get()
    return jsonify([rol.to_dict() for rol in roles]), 200

# ===========================
# Obtener un rol
# ===========================
@roles_bp.route("/<int:id>", methods=["GET"])
@jwt_required()
def get_rol(id):
    rol = RolesController.get_by_id(id)
    if rol:
        return jsonify(rol.to_dict()), 200
    return jsonify({"mensaje": "Rol no encontrado"}), 404

# ===========================
# Crear rol
# ===========================
@roles_bp.route("/", methods=["POST"])
@jwt_required()
@roles_required("Administrador", 1)
def create_rol():
    data = request.get_json() or {}
    rol = RolesController.create(data)
    return jsonify(rol.to_dict()), 201

# ===========================
# Actualizar rol
# ===========================
@roles_bp.route("/<int:id>", methods=["PUT"])
@jwt_required()
@roles_required("Administrador", 1)
def update_rol(id):
    data = request.get_json() or {}
    rol = RolesController.update(id, data)
    if rol:
        return jsonify(rol.to_dict()), 200
    return jsonify({"mensaje": "Rol no encontrado"}), 404

# ===========================
# Eliminar rol
# ===========================
@roles_bp.route("/<int:id>", methods=["DELETE"])
@jwt_required()
@roles_required("Administrador", 1)
def delete_rol(id):
    eliminado = RolesController.delete(id)
    if eliminado:
        return jsonify({"mensaje": "Rol eliminado correctamente"}), 200
    return jsonify({"mensaje": "Rol no encontrado"}), 404