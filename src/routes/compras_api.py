from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required
from src.controllers.compras_controller import ComprasController
from src.utils.pagination import get_pagination_params
from src.utils.security import roles_required

compras_bp = Blueprint("compras", __name__)
  
# ===========================
# Obtener todas las compras (paginado)
# ===========================
@compras_bp.route("/", methods=["GET"])
@jwt_required(optional=True)
def get_compras():
    page, per_page = get_pagination_params()
    resultado = ComprasController.get_paginated(page, per_page)
    return jsonify(resultado), 200

# ===========================
# Obtener una compra por ID
# ===========================
@compras_bp.route("/<int:id>", methods=["GET"])
def get_compra(id):
    compra = ComprasController.get_by_id(id)
    if compra:
        if isinstance(compra, dict):
            return jsonify(compra), 200
        elif hasattr(compra, "to_dict"):
            return jsonify(compra.to_dict()), 200
    return jsonify({
        "mensaje": "Compra no encontrada"
    }), 404

# ===========================
# Crear una compra
# ===========================
@compras_bp.route("/", methods=["POST"])
def create_compra():
    data = request.get_json()
    compra = ComprasController.create(data)
    return jsonify(compra.to_dict()), 201

# ===========================
# Actualizar una compra
# ===========================
@compras_bp.route("/<int:id>", methods=["PUT"])
def update_compra(id):
    data = request.get_json()
    compra = ComprasController.update(id, data)
    if compra:
        return jsonify(compra.to_dict()), 200
    return jsonify({
        "mensaje": "Compra no encontrada"
    }), 404

# ===========================
# Eliminar una compra
# ===========================
@compras_bp.route("/<int:id>", methods=["DELETE"])
def delete_compra(id):
    eliminado = ComprasController.delete(id)
    if eliminado:
        return jsonify({
            "mensaje": "Compra eliminada correctamente"
        }), 200
    return jsonify({
        "mensaje": "Compra no encontrada"
    }), 404 