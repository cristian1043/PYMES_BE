from flask import Blueprint, request, jsonify
from src.controllers.metodos_pago_controller import MetodosPagoController

metodos_pago_bp = Blueprint("metodos_pago", __name__)

# ===========================
# Obtener todos los métodos de pago
# ===========================
@metodos_pago_bp.route("/", methods=["GET"])
def get_metodos_pago():
    metodos_pago = MetodosPagoController.get()
    return jsonify([m.to_dict() for m in metodos_pago]), 200

#============================
# Obtener un método de pago por ID 
#============================
@metodos_pago_bp.route("/<int:id>", methods=["GET"])
def get_metodo_pago_by_id(id):
    metodos_pago = MetodosPagoController.get_by_id(id)
    if metodos_pago:  
        return jsonify(metodos_pago.to_dict()), 200
    return jsonify({
        "error": "Método de pago no encontrado"
    }), 404

#==========================
# Crear un nuevo método de pago
#==========================
@metodos_pago_bp.route("/", methods=["POST"])
def create_metodo_pago():
    data = request.get_json()
    metodos_pago = MetodosPagoController.save(data)
    return jsonify(metodos_pago.to_dict()), 201

#==========================
# Actualizar un método de pago
#==========================
@metodos_pago_bp.route("/<int:id>", methods=["PUT"])
def update_metodo_pago(id):
    data = request.get_json()
    metodos_pago = MetodosPagoController.update(id, data)
    if metodos_pago:
        return jsonify(metodos_pago.to_dict()), 200
    return jsonify({
        "error": "Método de pago no encontrado"
    }), 404
    
#==========================
# Eliminar un método de pago
#==========================
@metodos_pago_bp.route("/<int:id>", methods=["DELETE"])
def delete_metodo_pago(id):
    eliminado = MetodosPagoController.delete(id)
    if eliminado:
        return jsonify({
            "mensaje": "Método de pago eliminado correctamente"
        }), 200
    return jsonify({
        "error": "Método de pago no encontrado"
    }), 404