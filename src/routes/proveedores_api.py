from flask import Blueprint, request, jsonify
from src.controllers.proveedores_controller import ProveedoresController

proveedores_bp = Blueprint("proveedores", __name__)


# ===========================
# Obtener todos los proveedores
# ===========================
@proveedores_bp.route("/", methods=["GET"])
def get_proveedores():
    proveedores = ProveedoresController.get()
    return jsonify(proveedores), 200


# ===========================
# Obtener un proveedor
# ===========================
@proveedores_bp.route("/<int:id>", methods=["GET"])
def get_proveedor(id):
    proveedor = ProveedoresController.get_by_id(id)

    if proveedor:
        return jsonify(proveedor), 200

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

    return jsonify(proveedor), 201


# ===========================
# Actualizar proveedor
# ===========================
@proveedores_bp.route("/<int:id>", methods=["PUT"])
def update_proveedor(id):
    data = request.get_json()

    proveedor = ProveedoresController.update(id, data)

    if proveedor:
        return jsonify(proveedor), 200

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