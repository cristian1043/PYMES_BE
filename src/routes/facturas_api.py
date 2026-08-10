from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required
from src.controllers.facturas_controller import FacturasController
from src.utils.pagination import get_pagination_params
from src.utils.security import roles_required, tenant_required

facturas_bp = Blueprint("facturas", __name__)

# ===========================
# Obtener todas las facturas (paginado)
# ===========================
@facturas_bp.route("/", methods=["GET"])
@jwt_required(optional=True)
def get_facturas():
    page, per_page = get_pagination_params()
    resultado = FacturasController.get_paginated(page, per_page)
    return jsonify(resultado), 200

# ===========================
# Obtener una factura por ID
# ===========================
@facturas_bp.route("/<int:id>", methods=["GET"])
@jwt_required(optional=True)
def get_factura(id):
    factura = FacturasController.get_by_id(id)
    if factura and hasattr(factura, "to_dict"):
        return jsonify(factura.to_dict()), 200
    return jsonify({"mensaje": "Factura no encontrada"}), 404

# ===========================
# Crear factura
# ===========================
@facturas_bp.route("/", methods=["POST"])
@jwt_required()
@roles_required("Administrador", "Vendedor", "Contador")
def create_factura():
    data = request.get_json()
    factura = FacturasController.create(data)
    return jsonify(factura.to_dict()), 201

# ===========================
# Actualizar factura
# ===========================
@facturas_bp.route("/<int:id>", methods=["PUT"])
@jwt_required()
@roles_required("Administrador", "Vendedor", "Contador")
def update_factura(id):
    data = request.get_json()
    factura = FacturasController.update(id, data)
    if factura and hasattr(factura, "to_dict"):
        return jsonify(factura.to_dict()), 200
    return jsonify({"mensaje": "Factura no encontrada"}), 404

# ===========================
# Eliminar factura
# ===========================
@facturas_bp.route("/<int:id>", methods=["DELETE"])
@jwt_required()
@roles_required("Administrador")
def delete_factura(id):
    eliminado = FacturasController.delete(id)
    if eliminado:
        return jsonify({"mensaje": "Factura eliminada correctamente"}), 200
    return jsonify({"mensaje": "Factura no encontrada"}), 404