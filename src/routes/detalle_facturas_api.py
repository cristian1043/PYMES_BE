from flask import Blueprint, request, jsonify
from src.controllers.detalle_facturas_controller import DetalleFacturasController

detalle_facturas_bp = Blueprint("detalle_facturas", __name__)

# ===========================
# Obtener todos los detalles
# ===========================
@detalle_facturas_bp.route("/", methods=["GET"])
def get_detalles():
    detalles = DetalleFacturasController.get()
    return jsonify([c.to_dict() for c in detalles]), 200

# ===========================
# Obtener un detalle
# ===========================
@detalle_facturas_bp.route("/<int:id>", methods=["GET"])
def get_detalle(id):
    detalle = DetalleFacturasController.get_by_id(id)
    if detalle:
        return jsonify(detalle.to_dict()), 200
    return jsonify({
        "mensaje": "Detalle de factura no encontrado"
    }), 404

# ===========================
# Crear detalle
# ===========================
@detalle_facturas_bp.route("/", methods=["POST"])
def create_detalle():
    data = request.get_json()
    detalle = DetalleFacturasController.create(data)
    return jsonify(detalle.to_dict()), 201

# ===========================
# Actualizar detalle
# ===========================
@detalle_facturas_bp.route("/<int:id>", methods=["PUT"])
def update_detalle(id):
    data = request.get_json()
    detalle = DetalleFacturasController.update(id, data)
    if detalle:
        return jsonify(detalle.to_dict()), 200
    return jsonify({
        "mensaje": "Detalle de factura no encontrado"
    }), 404
 
# ===========================
# Eliminar detalle
# ===========================
@detalle_facturas_bp.route("/<int:id>", methods=["DELETE"])
def delete_detalle(id):
    eliminado = DetalleFacturasController.delete(id)
    if eliminado:
        return jsonify({
            "mensaje": "Detalle de factura eliminado correctamente"
        }), 200
    return jsonify({
        "mensaje": "Detalle de factura no encontrado"
    }), 404