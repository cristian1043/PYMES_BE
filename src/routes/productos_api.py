from flask import Blueprint, request, jsonify
from src.controllers.productos_controller import ProductosController

productos_bp = Blueprint("productos", __name__)


# ===========================
# Obtener todos los productos
# ===========================
@productos_bp.route("/", methods=["GET"])
def get_productos():
    productos = ProductosController.get()
    return jsonify(productos), 200


# ===========================
# Obtener un producto
# ===========================
@productos_bp.route("/<int:id>", methods=["GET"])
def get_producto(id):
    producto = ProductosController.get_by_id(id)

    if producto:
        return jsonify(producto), 200

    return jsonify({
        "mensaje": "Producto no encontrado"
    }), 404


# ===========================
# Crear producto
# ===========================
@productos_bp.route("/", methods=["POST"])
def create_producto():
    data = request.get_json()

    producto = ProductosController.create(data)

    return jsonify(producto), 201


# ===========================
# Actualizar producto
# ===========================
@productos_bp.route("/<int:id>", methods=["PUT"])
def update_producto(id):
    data = request.get_json()

    producto = ProductosController.update(id, data)

    if producto:
        return jsonify(producto), 200

    return jsonify({
        "mensaje": "Producto no encontrado"
    }), 404


# ===========================
# Eliminar producto
# ===========================
@productos_bp.route("/<int:id>", methods=["DELETE"])
def delete_producto(id):

    eliminado = ProductosController.delete(id)

    if eliminado:
        return jsonify({
            "mensaje": "Producto eliminado correctamente"
        }), 200

    return jsonify({
        "mensaje": "Producto no encontrado"
    }), 404