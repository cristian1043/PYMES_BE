from flask import Blueprint, request, jsonify
from src.controllers.detalle_compras_controller import DetalleComprasController

detalle_compras_bp = Blueprint("detalle_compras", __name__)


# ===========================
# Obtener todos los detalles
# ===========================
@detalle_compras_bp.route("/", methods=["GET"])
def get_detalles():
    detalles = DetalleComprasController.get()
    return jsonify(detalles), 200


# ===========================
# Obtener un detalle por ID
# ===========================
@detalle_compras_bp.route("/<int:id>", methods=["GET"])
def get_detalle(id):
    detalle = DetalleComprasController.get_by_id(id)

    if detalle:
        return jsonify(detalle), 200

    return jsonify({
        "mensaje": "Detalle de compra no encontrado"
    }), 404


# ===========================
# Crear un detalle
# ===========================
@detalle_compras_bp.route("/", methods=["POST"])
def create_detalle():
    data = request.get_json()

    detalle = DetalleComprasController.create(data)

    return jsonify(detalle), 201


# ===========================
# Actualizar un detalle
# ===========================
@detalle_compras_bp.route("/<int:id>", methods=["PUT"])
def update_detalle(id):
    data = request.get_json()

    detalle = DetalleComprasController.update(id, data)

    if detalle:
        return jsonify(detalle), 200

    return jsonify({
        "mensaje": "Detalle de compra no encontrado"
    }), 404


# ===========================
# Eliminar un detalle
# ===========================
@detalle_compras_bp.route("/<int:id>", methods=["DELETE"])
def delete_detalle(id):

    eliminado = DetalleComprasController.delete(id)

    if eliminado:
        return jsonify({
            "mensaje": "Detalle de compra eliminado correctamente"
        }), 200

    return jsonify({
        "mensaje": "Detalle de compra no encontrado"
    }), 404