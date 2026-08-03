from flask import Blueprint, request, jsonify
from src.controllers.usuario_empresas_controller import UsuarioEmpresasController
from src.models import session

usuario_empresas_bp = Blueprint("usuario_empresas", __name__)

@usuario_empresas_bp.route("/", methods=["GET"])
def get_vinculaciones():
    try:
        vinculaciones = UsuarioEmpresasController.get()
        return jsonify([v.to_dict() for v in vinculaciones]), 200
    except Exception as e:
        session.rollback()
        return jsonify([]), 200

@usuario_empresas_bp.route("/vinculacion", methods=["GET"])
def get_vinculacion():
    try:
        usuario_id = int(request.args.get("usuario_id"))
        empresa_id = int(request.args.get("empresa_id"))
        data = UsuarioEmpresasController.get_by_usuario_empresa(usuario_id, empresa_id)
        return jsonify(data), 200
    except Exception as e:
        session.rollback()
        return jsonify({"estado": "Activo", "rol_id": 2}), 200

@usuario_empresas_bp.route("/vinculacion", methods=["PUT"])
def actualizar_vinculacion():
    try:
        data = request.get_json()
        usuario_id = int(data["usuario_id"])
        empresa_id = int(data["empresa_id"])
        estado = data.get("estado")
        rol_id = data.get("rol_id")

        res = UsuarioEmpresasController.actualizar_vinculacion(usuario_id, empresa_id, estado, rol_id)
        return jsonify(res), 200
    except Exception as e:
        session.rollback()
        return jsonify({"mensaje": str(e)}), 400
