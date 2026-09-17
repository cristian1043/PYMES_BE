from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity, get_jwt, verify_jwt_in_request
from src.controllers.usuarios_controller import UsuariosController
from src.models import session
from src.utils.pagination import get_pagination_params
from src.utils.security import roles_required

usuarios_bp = Blueprint("usuarios", __name__)


# ===========================
# Obtener todos los usuarios (paginado con búsqueda y filtros)
# ===========================
@usuarios_bp.route("/", methods=["GET"])
@jwt_required()
@roles_required("Administrador")
def get_usuarios():
    try:
        page, per_page = get_pagination_params()
        q = request.args.get("q", "").strip()
        filtro = request.args.get("filtro", "").strip()
        empresa_id = request.args.get("empresa_id")
        resultado = UsuariosController.get_paginated(page, per_page, q=q, filtro=filtro, empresa_id=empresa_id)
        return jsonify(resultado), 200
    except Exception as e:
        session.rollback()
        print(f"Error en GET usuarios: {str(e)}")
        return jsonify({"items": [], "total": 0, "page": 1, "per_page": 10, "total_pages": 0}), 200


# ===========================
# Obtener un usuario por ID
# ===========================
@usuarios_bp.route("/<int:id>", methods=["GET"])
@jwt_required()
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
# Obtener un usuario por Username
# ===========================
@usuarios_bp.route("/username/<username>", methods=["GET"])
@jwt_required()
def get_usuario_por_username(username):
    try:
        usuario = UsuariosController.get_by_username(username)
        if usuario:
            return jsonify(usuario.to_dict()), 200
        return jsonify({"mensaje": f"No existe ningún usuario registrado con el identificador @{username.lstrip('@')}"}), 404
    except Exception as e:
        session.rollback()
        return jsonify({"mensaje": str(e)}), 500


# ===========================
# Obtener un usuario por Documento
# ===========================
@usuarios_bp.route("/documento/<doc>", methods=["GET"])
@jwt_required()
def get_usuario_por_documento(doc):
    try:
        usuario = UsuariosController.get_by_documento(doc)
        if usuario:
            return jsonify(usuario.to_dict()), 200
        return jsonify({"mensaje": "Usuario no encontrado"}), 404
    except Exception as e:
        session.rollback()
        return jsonify({"mensaje": str(e)}), 500


# ===========================
# Validar disponibilidad de username (Público para formulario de registro)
# ===========================
@usuarios_bp.route("/check-username/<username>", methods=["GET"])
def check_username(username):
    try:
        usuario = UsuariosController.get_by_username(username)
        return jsonify({"disponible": usuario is None}), 200
    except Exception as e:
        return jsonify({"disponible": True}), 200


# ===========================
# Crear usuario (Registro público o creación por Administrador)
# ===========================
@usuarios_bp.route("/", methods=["POST"])
def create_usuario():
    try:
        data = request.get_json()
        if not data:
            return jsonify({"mensaje": "No se recibieron datos en la petición"}), 400

        # Verificar si la petición proviene de un Administrador autenticado
        es_admin = False
        try:
            verify_jwt_in_request(optional=True)
            claims = get_jwt() or {}
            if claims.get("rol") == "Administrador" or claims.get("id_rol") == 1:
                es_admin = True
        except Exception:
            es_admin = False

        # Si no es un Administrador autenticado, impedir la asignación de rol privilegiado
        if not es_admin:
            data["id_rol"] = 2  # Rol estándar (Vendedor/Empleado)
            data["estado"] = "Activo"

        usuario = UsuariosController.create(data)
        return jsonify(usuario.to_dict()), 201
    except ValueError as ve:
        session.rollback()
        return jsonify({"mensaje": str(ve)}), 400
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
@jwt_required()
def update_usuario(id):
    try:
        identity = get_jwt_identity()
        claims = get_jwt() or {}
        es_admin = claims.get("rol") == "Administrador" or claims.get("id_rol") == 1
        es_mismo_usuario = identity and int(identity) == id

        if not es_admin and not es_mismo_usuario:
            return jsonify({"mensaje": "No tienes permiso para modificar la información de otro usuario."}), 403

        data = request.get_json() or {}

        # Si no es Administrador, no puede auto-cambiarse el rol ni el estado de cuenta
        if not es_admin:
            data.pop("id_rol", None)
            data.pop("estado", None)

        usuario = UsuariosController.update(id, data)
        if usuario:
            return jsonify(usuario.to_dict()), 200
        return jsonify({"mensaje": "Usuario no encontrado"}), 404
    except Exception as e:
        session.rollback()
        return jsonify({"mensaje": str(e)}), 400


# ===========================
# Cambiar estado del usuario (Activar / Desactivar)
# ===========================
@usuarios_bp.route("/<int:id>/estado", methods=["PATCH"])
@jwt_required()
@roles_required("Administrador")
def toggle_estado_usuario(id):
    try:
        data = request.get_json() or {}
        nuevo_estado = data.get("estado", "Inactivo")
        usuario = UsuariosController.desactivar(id, estado=nuevo_estado)
        if usuario:
            return jsonify({"mensaje": f"Usuario actualizado a estado {nuevo_estado}", "usuario": usuario.to_dict()}), 200
        return jsonify({"mensaje": "Usuario no encontrado"}), 404
    except Exception as e:
        session.rollback()
        return jsonify({"mensaje": str(e)}), 400


# ===========================
# Eliminar usuario
# ===========================
@usuarios_bp.route("/<int:id>", methods=["DELETE"])
@jwt_required()
@roles_required("Administrador")
def delete_usuario(id):
    try:
        eliminado = UsuariosController.delete(id)
        if eliminado:
            return jsonify({"mensaje": "Usuario desactivado correctamente"}), 200
        return jsonify({"mensaje": "Usuario no encontrado"}), 404
    except Exception as e:
        session.rollback()
        return jsonify({"mensaje": str(e)}), 400