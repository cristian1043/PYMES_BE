from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required
from src.controllers.usuarios_controller import UsuariosController
from src.models import session
from src.utils.pagination import get_pagination_params
from src.utils.security import roles_required

usuarios_bp = Blueprint("usuarios", __name__)


# ===========================
# Obtener todos los usuarios (paginado)
# ===========================
@usuarios_bp.route("/", methods=["GET"])
@jwt_required(optional=True)
def get_usuarios():
    try:
        page, per_page = get_pagination_params()
        resultado = UsuariosController.get_paginated(page, per_page)
        return jsonify(resultado), 200
    except Exception as e:
        session.rollback()
        print(f"Error en GET usuarios: {str(e)}")
        return jsonify({"items": [], "total": 0, "page": 1, "per_page": 10, "total_pages": 0}), 200


# ===========================
# Obtener un usuario
# ===========================
@usuarios_bp.route("/<int:id>", methods=["GET"])
def get_usuario(id):
    try:
        usuario = UsuariosController.get_by_id(id)
        if usuario:
            return jsonify(usuario.to_dict()), 200
        return jsonify({"mensaje": "Usuario no encontrado"}), 404
    except Exception as e:
        session.rollback()
        return jsonify({"mensaje": str(e)}), 500


# ===========================
# Crear usuario
# ===========================
@usuarios_bp.route("/", methods=["POST"])
def create_usuario():
    try:
        data = request.get_json()
        if not data:
            return jsonify({"mensaje": "No se recibieron datos en la petición"}), 400

        usuario = UsuariosController.create(data)
        return jsonify(usuario.to_dict()), 201
    except Exception as e:
        session.rollback()
        print(f"=== ERROR EN BACKEND AL CREAR USUARIO ===")
        print(str(e))
        return jsonify({
            "mensaje": f"No se pudo guardar el usuario: {str(e)}"
        }), 400


# ===========================
# Actualizar usuario
# ===========================
@usuarios_bp.route("/<int:id>", methods=["PUT"])
def update_usuario(id):
    try:
        data = request.get_json()
        usuario = UsuariosController.update(id, data)
        if usuario:
            return jsonify(usuario.to_dict()), 200
        return jsonify({"mensaje": "Usuario no encontrado"}), 404
    except Exception as e:
        session.rollback()
        return jsonify({"mensaje": str(e)}), 400


# ===========================
# Eliminar usuario
# ===========================
@usuarios_bp.route("/<int:id>", methods=["DELETE"])
def delete_usuario(id):
    try:
        eliminado = UsuariosController.delete(id)
        if eliminado:
            return jsonify({"mensaje": "Usuario eliminado correctamente"}), 200
        return jsonify({"mensaje": "Usuario no encontrado"}), 404
    except Exception as e:
        session.rollback()
        return jsonify({"mensaje": str(e)}), 400