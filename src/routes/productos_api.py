from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required
from src.controllers.productos_controller import ProductosController
from src.utils.pagination import get_pagination_params
from src.utils.security import roles_required

productos_bp = Blueprint("productos", __name__)

# ===========================
# Obtener productos (con paginación)
# ===========================
@productos_bp.route("/", methods=["GET"])
@jwt_required(optional=True)
def get_productos():
    page, per_page = get_pagination_params()
    # Si se especifican parámetros de paginación o por defecto
    if request.args.get("page") or request.args.get("per_page") or True:
        resultado = ProductosController.get_paginated(page, per_page)
        return jsonify(resultado), 200
    
    productos = ProductosController.get()
    return jsonify([c.to_dict() for c in productos]), 200

# ===========================
# Obtener un producto por ID
# ===========================
@productos_bp.route("/<int:id>", methods=["GET"])
@jwt_required(optional=True)
def get_producto(id):
    producto = ProductosController.get_by_id(id)
    if producto and hasattr(producto, "to_dict"):
        return jsonify(producto.to_dict()), 200
    return jsonify({"mensaje": "Producto no encontrado"}), 404

# ===========================
# Crear producto
# ===========================
@productos_bp.route("/", methods=["POST"])
@jwt_required()
@roles_required("Administrador", "Vendedor")
def create_producto():
    data = request.get_json()
    producto = ProductosController.create(data)
    return jsonify(producto.to_dict()), 201

# ===========================
# Actualizar producto
# ===========================
@productos_bp.route("/<int:id>", methods=["PUT"])
@jwt_required()
@roles_required("Administrador", "Vendedor")
def update_producto(id):
    data = request.get_json()
    producto = ProductosController.update(id, data)
    if producto and hasattr(producto, "to_dict"):
        return jsonify(producto.to_dict()), 200
    return jsonify({"mensaje": "Producto no encontrado"}), 404

# ===========================
# Eliminar producto
# ===========================
@productos_bp.route("/<int:id>", methods=["DELETE"])
@jwt_required()
@roles_required("Administrador")
def delete_producto(id):
    eliminado = ProductosController.delete(id)
    if eliminado:
        return jsonify({"mensaje": "Producto eliminado correctamente"}), 200
    return jsonify({"mensaje": "Producto no encontrado"}), 404