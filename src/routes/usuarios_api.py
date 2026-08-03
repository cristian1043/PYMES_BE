from flask import Blueprint, request, jsonify
from src.controllers.usuarios_controller import UsuariosController
from src.models import session

usuarios_bp = Blueprint("usuarios", __name__)


# ===========================
# Obtener todos los usuarios
# ===========================
@usuarios_bp.route("/", methods=["GET"])
def get_usuarios():
    try:
        usuarios = UsuariosController.get()
        return jsonify([c.to_dict() for c in usuarios]), 200
    except Exception as e:
        session.rollback()
        print(f"Error en GET usuarios: {str(e)}")
        return jsonify([]), 200


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