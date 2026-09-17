from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt, get_jwt_identity
from src.controllers.usuario_empresas_controller import UsuarioEmpresasController
from src.models.usuario_empresas import UsuarioEmpresas
from src.models import session

usuario_empresas_bp = Blueprint("usuario_empresas", __name__)

@usuario_empresas_bp.route("/", methods=["GET"])
@jwt_required()
def get_vinculaciones():
    try:
        vinculaciones = UsuarioEmpresasController.get()
        return jsonify([v.to_dict() for v in vinculaciones]), 200
    except Exception as e:
        session.rollback()
        return jsonify([]), 200

@usuario_empresas_bp.route("/vinculacion", methods=["GET"])
@jwt_required()
def get_vinculacion():
    try:
        usuario_id = int(request.args.get("usuario_id"))
        empresa_id = int(request.args.get("empresa_id"))
        data = UsuarioEmpresasController.get_by_usuario_empresa(usuario_id, empresa_id)
        return jsonify(data), 200
    except Exception as e:
        session.rollback()
        print(f"Error en get_vinculacion: {str(e)}")
        return jsonify({"estado": "No Vinculado", "rol_id": 2}), 200

@usuario_empresas_bp.route("/vinculacion", methods=["PUT"])
@jwt_required()
def actualizar_vinculacion():
    try:
        claims = get_jwt() or {}
        id_rol = claims.get("id_rol", 0)
        rol_usuario = claims.get("rol", "")
        identity = get_jwt_identity()

        data = request.get_json() or {}
        usuario_id = int(data["usuario_id"])
        empresa_id = int(data["empresa_id"])
        estado = data.get("estado")
        rol_id = data.get("rol_id")

        es_super_admin = (id_rol == 1 or rol_usuario == "Administrador")
        es_admin_empresa = False

        if not es_super_admin and identity:
            vinc_caller = UsuarioEmpresas.get_by_usuario_empresa(int(identity), empresa_id)
            if vinc_caller and vinc_caller.rol_id == 1 and vinc_caller.estado == "Activo":
                es_admin_empresa = True

        # Permitir si es SuperAdmin, Administrador de la empresa, o el usuario inicial vinculándose a la empresa que acaba de crear
        es_auto_vinculacion_inicial = (identity and int(identity) == usuario_id and rol_id == 1)
        if not es_super_admin and not es_admin_empresa and not es_auto_vinculacion_inicial:
            return jsonify({"mensaje": "Acceso denegado: Se requieren permisos de Administrador en esta empresa para gestionar vinculaciones."}), 403

        res = UsuarioEmpresasController.actualizar_vinculacion(usuario_id, empresa_id, estado, rol_id)
        return jsonify(res), 200
    except Exception as e:
        session.rollback()
        return jsonify({"mensaje": str(e)}), 400
