from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity, get_jwt, verify_jwt_in_request
from src.controllers.usuarios_controller import UsuariosController
from src.models import session
from src.models.usuario_empresas import UsuarioEmpresas
from src.utils.pagination import get_pagination_params
from src.utils.security import (
    roles_required,
    es_identidad_cliente,
    es_super_admin_actual,
    verificar_acceso_empresa,
    obtener_empresas_autorizadas_usuario,
)

usuarios_bp = Blueprint("usuarios", __name__)


def _comparte_empresa_como_admin(caller_id, target_user_id) -> bool:
    if not caller_id or not str(caller_id).isdigit():
        return False
    vincs_caller = UsuarioEmpresas.get_by_usuario(int(caller_id))
    empresas_admin = {v.empresa_id for v in vincs_caller if v.estado == "Activo" and v.rol_id == 1}
    if not empresas_admin:
        return False
    vincs_target = UsuarioEmpresas.get_by_usuario(int(target_user_id))
    empresas_target = {v.empresa_id for v in vincs_target if v.estado != "No Vinculado"}
    return bool(empresas_admin.intersection(empresas_target))


@usuarios_bp.route("/", methods=["GET"])
@jwt_required()
@roles_required("Administrador", 1)
def get_usuarios():
    try:
        page, per_page = get_pagination_params()
        q = request.args.get("q", "").strip()
        filtro = request.args.get("filtro", "").strip()
        empresa_id = (
            request.args.get("empresa_id")
            or request.args.get("id_empresa")
            or request.headers.get("X-Empresa-ID")
        )
        if not es_super_admin_actual():
            if not empresa_id:
                empresas_aut = obtener_empresas_autorizadas_usuario()
                empresa_id = empresas_aut[0] if empresas_aut else -1
            elif not verificar_acceso_empresa(empresa_id):
                return jsonify({"mensaje": "No tienes permisos para listar usuarios de otra empresa."}), 403

        resultado = UsuariosController.get_paginated(page, per_page, q=q, filtro=filtro, empresa_id=empresa_id)
        return jsonify(resultado), 200
    except Exception:
        session.rollback()
        return jsonify({"items": [], "total": 0, "page": 1, "per_page": 10, "total_pages": 0}), 200


@usuarios_bp.route("/<int:id>", methods=["GET"])
@jwt_required()
def get_usuario(id):
    if es_identidad_cliente():
        return jsonify({"mensaje": "Acceso denegado."}), 403
    try:
        usuario = UsuariosController.get_by_id(id)
        if not usuario:
            return jsonify({"mensaje": "Usuario no encontrado"}), 404

        caller_id = get_jwt_identity()
        es_mismo = caller_id and str(caller_id) == str(id)
        if es_mismo or es_super_admin_actual() or _comparte_empresa_como_admin(caller_id, id):
            return jsonify(usuario.to_dict()), 200
        return jsonify(usuario.to_safe_dict()), 200
    except Exception as e:
        session.rollback()
        return jsonify({"mensaje": str(e)}), 500


@usuarios_bp.route("/username/<username>", methods=["GET"])
@jwt_required()
def get_usuario_por_username(username):
    if es_identidad_cliente():
        return jsonify({"mensaje": "Acceso denegado."}), 403
    try:
        usuario = UsuariosController.get_by_username(username)
        if usuario:
            return jsonify(usuario.to_safe_dict()), 200
        return jsonify({"mensaje": f"No existe ningún usuario registrado con el identificador @{username.lstrip('@')}"}), 404
    except Exception as e:
        session.rollback()
        return jsonify({"mensaje": str(e)}), 500


@usuarios_bp.route("/documento/<doc>", methods=["GET"])
@jwt_required()
def get_usuario_por_documento(doc):
    if es_identidad_cliente():
        return jsonify({"mensaje": "Acceso denegado."}), 403
    try:
        usuario = UsuariosController.get_by_documento(doc)
        if usuario:
            return jsonify(usuario.to_safe_dict()), 200
        return jsonify({"mensaje": "Usuario no encontrado"}), 404
    except Exception as e:
        session.rollback()
        return jsonify({"mensaje": str(e)}), 500


@usuarios_bp.route("/check-username/<username>", methods=["GET"])
def check_username(username):
    try:
        usuario = UsuariosController.get_by_username(username)
        return jsonify({"disponible": usuario is None}), 200
    except Exception:
        return jsonify({"disponible": True}), 200


@usuarios_bp.route("/", methods=["POST"])
def create_usuario():
    try:
        data = request.get_json()
        if not data:
            return jsonify({"mensaje": "No se recibieron datos en la petición"}), 400

        es_admin = False
        try:
            verify_jwt_in_request(optional=True)
            claims = get_jwt() or {}
            if claims.get("identity_type") != "cliente" and (
                claims.get("es_super_admin") or claims.get("rol") == "Administrador" or claims.get("id_rol") == 1
            ):
                es_admin = True
        except Exception:
            es_admin = False

        if not es_admin:
            # En el registro inicial de dueño de empresa o empleado se respeta rol 1 o 2, pero nunca super_admin
            rol_sol = int(data.get("id_rol", 2) or 2)
            data["id_rol"] = rol_sol if rol_sol in (1, 2, 3) else 2
            data["estado"] = "Activo"

        usuario = UsuariosController.create(data)
        return jsonify(usuario.to_dict()), 201
    except ValueError as ve:
        session.rollback()
        return jsonify({"mensaje": str(ve)}), 400
    except Exception as e:
        session.rollback()
        return jsonify({"mensaje": f"No se pudo guardar el usuario: {str(e)}"}), 400


@usuarios_bp.route("/<int:id>", methods=["PUT"])
@jwt_required()
def update_usuario(id):
    if es_identidad_cliente():
        return jsonify({"mensaje": "Acceso denegado."}), 403
    try:
        identity = get_jwt_identity()
        es_mismo_usuario = identity and int(identity) == id
        es_admin_autorizado = es_super_admin_actual() or _comparte_empresa_como_admin(identity, id)

        if not es_admin_autorizado and not es_mismo_usuario:
            return jsonify({"mensaje": "No tienes permiso para modificar la información de otro usuario."}), 403

        data = request.get_json() or {}
        for campo_inmutable in ("id", "documento", "tipo_documento", "username", "es_super_admin"):
            data.pop(campo_inmutable, None)

        usuario = UsuariosController.update(id, data, allow_role_change=es_admin_autorizado)
        if usuario:
            return jsonify(usuario.to_dict()), 200
        return jsonify({"mensaje": "Usuario no encontrado"}), 404
    except ValueError as ve:
        session.rollback()
        return jsonify({"mensaje": str(ve)}), 400
    except Exception as e:
        session.rollback()
        return jsonify({"mensaje": str(e)}), 400


@usuarios_bp.route("/<int:id>/estado", methods=["PATCH"])
@jwt_required()
@roles_required("Administrador", 1)
def toggle_estado_usuario(id):
    try:
        identity = get_jwt_identity()
        if not es_super_admin_actual() and not _comparte_empresa_como_admin(identity, id):
            return jsonify({"mensaje": "No tienes permisos sobre este usuario."}), 403
        data = request.get_json() or {}
        nuevo_estado = data.get("estado", "Inactivo")
        usuario = UsuariosController.desactivar(id, estado=nuevo_estado)
        if usuario:
            return jsonify({"mensaje": f"Usuario actualizado a estado {nuevo_estado}", "usuario": usuario.to_dict()}), 200
        return jsonify({"mensaje": "Usuario no encontrado"}), 404
    except Exception as e:
        session.rollback()
        return jsonify({"mensaje": str(e)}), 400


@usuarios_bp.route("/<int:id>", methods=["DELETE"])
@jwt_required()
@roles_required("Administrador", 1)
def delete_usuario(id):
    try:
        identity = get_jwt_identity()
        if not es_super_admin_actual() and not _comparte_empresa_como_admin(identity, id):
            return jsonify({"mensaje": "No tienes permisos sobre este usuario."}), 403
        eliminado = UsuariosController.delete(id)
        if eliminado:
            return jsonify({"mensaje": "Usuario desactivado correctamente"}), 200
        return jsonify({"mensaje": "Usuario no encontrado"}), 404
    except Exception as e:
        session.rollback()
        return jsonify({"mensaje": str(e)}), 400
