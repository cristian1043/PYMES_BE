from flask import Blueprint, request, jsonify
from src.controllers.compras_controller import ComprasController

compras_bp = Blueprint("compras", __name__)


# ===========================
# Obtener todas las compras
# ===========================
@compras_bp.route("/", methods=["GET"])
def get_compras():
    compras = ComprasController.get()
    return jsonify(compras), 200


# ===========================
# Obtener una compra por ID
# ===========================
@compras_bp.route("/<int:id>", methods=["GET"])
def get_compra(id):
    compra = ComprasController.get_by_id(id)

    if compra:
        return jsonify(compra), 200

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

    return jsonify(compra), 201


# ===========================
# Actualizar una compra
# ===========================
@compras_bp.route("/<int:id>", methods=["PUT"])
def update_compra(id):
    data = request.get_json()

    compra = ComprasController.update(id, data)

    if compra:
        return jsonify(compra), 200

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