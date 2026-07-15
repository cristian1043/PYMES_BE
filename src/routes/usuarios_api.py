from flask import Blueprint, request, jsonify
from src.controllers.usuarios_controller import UsuariosController

usuarios_bp = Blueprint("usuarios", __name__)


# ===========================
# Obtener todos los usuarios
# ===========================
@usuarios_bp.route("/", methods=["GET"])
def get_usuarios():
    usuarios = UsuariosController.get()
    return jsonify(usuarios), 200


# ===========================
# Obtener un usuario
# ===========================
@usuarios_bp.route("/<int:id>", methods=["GET"])
def get_usuario(id):
    usuario = UsuariosController.get_by_id(id)

    if usuario:
        return jsonify(usuario), 200

    return jsonify({
        "mensaje": "Usuario no encontrado"
    }), 404


# ===========================
# Crear usuario
# ===========================
@usuarios_bp.route("/", methods=["POST"])
def create_usuario():
    data = request.get_json()

    usuario = UsuariosController.create(data)

    return jsonify(usuario), 201


# ===========================
# Actualizar usuario
# ===========================
@usuarios_bp.route("/<int:id>", methods=["PUT"])
def update_usuario(id):
    data = request.get_json()

    usuario = UsuariosController.update(id, data)

    if usuario:
        return jsonify(usuario), 200

    return jsonify({
        "mensaje": "Usuario no encontrado"
    }), 404


# ===========================
# Eliminar usuario
# ===========================
@usuarios_bp.route("/<int:id>", methods=["DELETE"])
def delete_usuario(id):

    eliminado = UsuariosController.delete(id)

    if eliminado:
        return jsonify({
            "mensaje": "Usuario eliminado correctamente"
        }), 200

    return jsonify({
        "mensaje": "Usuario no encontrado"
    }), 404