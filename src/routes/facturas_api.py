from flask import Blueprint, request, jsonify
from src.controllers.facturas_controller import FacturasController

facturas_bp = Blueprint("facturas", __name__)

# ===========================
# Obtener todas las facturas
# ===========================
@facturas_bp.route("/", methods=["GET"])
def get_facturas():
    facturas = FacturasController.get()
    return jsonify([c.to_dict() for c in facturas]), 200

# ===========================
# Obtener una factura por ID
# ===========================
@facturas_bp.route("/<int:id>", methods=["GET"])
def get_factura(id):
    factura = FacturasController.get_by_id(id)
    if factura:
        return jsonify(factura.to_dict()), 200
    return jsonify({
        "mensaje": "Factura no encontrada"
    }), 404

# ===========================
# Crear factura
# ===========================
@facturas_bp.route("/", methods=["POST"])
def create_factura():
    data = request.get_json()

    factura = FacturasController.create(data)

    return jsonify(factura.to_dict()), 201

# ===========================
# Actualizar factura
# ===========================
@facturas_bp.route("/<int:id>", methods=["PUT"])
def update_factura(id):
    data = request.get_json()
    factura = FacturasController.update(id, data)
    if factura:
        return jsonify(factura.to_dict()), 200
    return jsonify({
        "mensaje": "Factura no encontrada"
    }), 404

# ===========================
# Eliminar factura
# ===========================
@facturas_bp.route("/<int:id>", methods=["DELETE"])
def delete_factura(id):

    eliminado = FacturasController.delete(id)

    if eliminado:
        return jsonify({
            "mensaje": "Factura eliminada correctamente"
        }), 200

    return jsonify({
        "mensaje": "Factura no encontrada"
    }), 404