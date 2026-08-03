from flask import Blueprint, request, jsonify
from src.controllers.empresas_controller import EmpresasController
from src.models import session

empresas_bp = Blueprint("empresas", __name__)

@empresas_bp.route("/", methods=["GET"])
def get_empresas():
    try:
        empresas = EmpresasController.get()
        return jsonify([e.to_dict() for e in empresas]), 200
    except Exception as e:
        session.rollback()
        return jsonify([]), 200

@empresas_bp.route("/<int:id>", methods=["GET"])
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
def create_empresa():
    try:
        data = request.get_json()
        empresa = EmpresasController.create(data)
        return jsonify(empresa.to_dict()), 201
    except Exception as e:
        session.rollback()
        return jsonify({"mensaje": str(e)}), 400

@empresas_bp.route("/<int:id>", methods=["PUT"])
def update_empresa(id):
    try:
        data = request.get_json()
        empresa = EmpresasController.update(id, data)
        if empresa:
            return jsonify(empresa.to_dict()), 200
        return jsonify({"mensaje": "Empresa no encontrada"}), 404
    except Exception as e:
        session.rollback()
        return jsonify({"mensaje": str(e)}), 400
