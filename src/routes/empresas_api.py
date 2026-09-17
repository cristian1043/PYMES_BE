from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt, get_jwt_identity
from src.controllers.empresas_controller import EmpresasController
from src.models.usuario_empresas import UsuarioEmpresas
from src.models import session

empresas_bp = Blueprint("empresas", __name__)

@empresas_bp.route("/", methods=["GET"])
@jwt_required()
def get_empresas():
    try:
        empresas = EmpresasController.get()
        return jsonify([e.to_dict() for e in empresas]), 200
    except Exception as e:
        session.rollback()
        return jsonify([]), 200

@empresas_bp.route("/<int:id>", methods=["GET"])
@jwt_required()
def get_empresa(id):
    try:
        empresa = EmpresasController.get_by_id(id)
        if empresa:
            return jsonify(empresa.to_dict()), 200
        return jsonify({"mensaje": "Empresa no encontrada"}), 404
    except Exception as e:
        session.rollback()
        return jsonify({"mensaje": str(e)}), 400

@empresas_bp.route("/", methods=["POST"])
@jwt_required()
def create_empresa():
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
    try:
        claims = get_jwt() or {}
        id_rol = claims.get("id_rol", 0)
        rol_usuario = claims.get("rol", "")
        identity = get_jwt_identity()

        es_super_admin = (id_rol == 1 or rol_usuario == "Administrador")
        es_admin_empresa = False

        if not es_super_admin and identity:
            vinc = UsuarioEmpresas.get_by_usuario_empresa(int(identity), id)
            if vinc and vinc.rol_id == 1 and vinc.estado == "Activo":
                es_admin_empresa = True

        if not es_super_admin and not es_admin_empresa:
            return jsonify({"mensaje": "No tienes permisos de Administrador para modificar esta empresa."}), 403

        data = request.get_json() or {}
        empresa = EmpresasController.update(id, data)
        if empresa:
            return jsonify(empresa.to_dict()), 200
        return jsonify({"mensaje": "Empresa no encontrada"}), 404
    except Exception as e:
        session.rollback()
        return jsonify({"mensaje": str(e)}), 400
