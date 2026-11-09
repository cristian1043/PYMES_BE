from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from src.controllers.empresas_controller import EmpresasController
from src.models import session
from src.utils.security import (
    es_identidad_cliente,
    es_super_admin_actual,
    verificar_acceso_empresa,
    obtener_rol_en_empresa,
)

empresas_bp = Blueprint("empresas", __name__)


@empresas_bp.route("/", methods=["GET"])
@jwt_required()
def get_empresas():
    if es_identidad_cliente():
        return jsonify({"mensaje": "Acceso denegado."}), 403
    try:
        identity = get_jwt_identity()
        empresas = EmpresasController.get(user_id=identity, es_super_admin=es_super_admin_actual())
        return jsonify([e.to_dict() for e in empresas]), 200
    except Exception:
        session.rollback()
        return jsonify([]), 200


@empresas_bp.route("/<int:id>", methods=["GET"])
@jwt_required()
def get_empresa(id):
    if es_identidad_cliente():
        return jsonify({"mensaje": "Acceso denegado."}), 403
    try:
        empresa = EmpresasController.get_by_id(id)
        if not empresa:
            return jsonify({"mensaje": "Empresa no encontrada"}), 404
        if not verificar_acceso_empresa(id, allow_inactivo=True):
            return jsonify({"mensaje": "No tienes autorización para consultar esta empresa."}), 403
        return jsonify(empresa.to_dict()), 200
    except Exception as e:
        session.rollback()
        return jsonify({"mensaje": str(e)}), 400


@empresas_bp.route("/", methods=["POST"])
@jwt_required()
def create_empresa():
    if es_identidad_cliente():
        return jsonify({"mensaje": "Acceso denegado."}), 403
    try:
        data = request.get_json() or {}
        identity = get_jwt_identity()
        if identity and not data.get("usuario_id"):
            try:
                data["usuario_id"] = int(identity)
            except (ValueError, TypeError):
                pass
        empresa = EmpresasController.create(data)
        return jsonify(empresa.to_dict()), 201
    except Exception as e:
        session.rollback()
        return jsonify({"mensaje": str(e)}), 400


@empresas_bp.route("/<int:id>", methods=["PUT"])
@jwt_required()
def update_empresa(id):
    if es_identidad_cliente():
        return jsonify({"mensaje": "Acceso denegado."}), 403
    try:
        empresa_actual = EmpresasController.get_by_id(id)
        if not empresa_actual:
            return jsonify({"mensaje": "Empresa no encontrada"}), 404

        rol_id_emp, _ = obtener_rol_en_empresa(id)
        if not es_super_admin_actual() and rol_id_emp != 1:
            return jsonify({"mensaje": "No tienes permisos de Administrador en esta empresa para modificarla."}), 403

        data = request.get_json() or {}
        empresa = EmpresasController.update(id, data)
        if empresa:
            return jsonify(empresa.to_dict()), 200
        return jsonify({"mensaje": "Empresa no encontrada"}), 404
    except Exception as e:
        session.rollback()
        return jsonify({"mensaje": str(e)}), 400
