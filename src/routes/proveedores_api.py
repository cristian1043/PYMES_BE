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
    empresa_id = request.args.get("empresa_id") or request.args.get("id_empresa")
    resultado = ProveedoresController.get_paginated(page, per_page, empresa_id=empresa_id)
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
# Cambiar estado del proveedor (Activar / Desactivar)
# ===========================
@proveedores_bp.route("/<int:id>/estado", methods=["PATCH"])
@jwt_required(optional=True)
def toggle_estado_proveedor(id):
    data = request.get_json() or {}
    nuevo_estado = data.get("estado", "Inactivo")
    proveedor = ProveedoresController.desactivar(id, estado=nuevo_estado)
    if proveedor and hasattr(proveedor, "to_dict"):
        return jsonify({"mensaje": f"Proveedor actualizado a estado {nuevo_estado}", "proveedor": proveedor.to_dict()}), 200
    return jsonify({"mensaje": "Proveedor no encontrado"}), 404

# ===========================
# Eliminar proveedor
# ===========================
@proveedores_bp.route("/<int:id>", methods=["DELETE"])
def delete_proveedor(id):
    eliminado = ProveedoresController.delete(id)
    if eliminado:
        return jsonify({
            "mensaje": "Proveedor desactivado correctamente"
        }), 200
    return jsonify({
        "mensaje": "Proveedor no encontrado"
    }), 404