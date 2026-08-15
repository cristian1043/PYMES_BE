from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required
from src.controllers.proveedores_controller import ProveedoresController
from src.utils.pagination import get_pagination_params
from src.utils.security import roles_required

proveedores_bp = Blueprint("proveedores", __name__)


# ===========================
# Obtener proveedores (paginado)
# ===========================
@proveedores_bp.route("/", methods=["GET"])
@jwt_required(optional=True)
def get_proveedores():
    page, per_page = get_pagination_params()
    resultado = ProveedoresController.get_paginated(page, per_page)
    return jsonify(resultado), 200


# ===========================
# Obtener un proveedor
# ===========================
@proveedores_bp.route("/<int:id>", methods=["GET"])
def get_proveedor(id):
    proveedor = ProveedoresController.get_by_id(id)

    if proveedor:
        return jsonify(proveedor.to_dict()), 200

    return jsonify({
        "mensaje": "Proveedor no encontrado"
    }), 404


# ===========================
# Crear proveedor
# ===========================
@proveedores_bp.route("/", methods=["POST"])
def create_proveedor():
    data = request.get_json()
    proveedor = ProveedoresController.create(data)
    return jsonify(proveedor.to_dict()), 201


# ===========================
# Actualizar proveedor
# ===========================
@proveedores_bp.route("/<int:id>", methods=["PUT"])
def update_proveedor(id):
    data = request.get_json()
    proveedor = ProveedoresController.update(id, data)
    if proveedor:
        return jsonify(proveedor.to_dict()), 200
    return jsonify({
        "mensaje": "Proveedor no encontrado"
    }), 404


# ===========================
# Eliminar proveedor
# ===========================
@proveedores_bp.route("/<int:id>", methods=["DELETE"])
def delete_proveedor(id):
    eliminado = ProveedoresController.delete(id)
    if eliminado:
        return jsonify({
            "mensaje": "Proveedor eliminado correctamente"
        }), 200
    return jsonify({
        "mensaje": "Proveedor no encontrado"
    }), 404