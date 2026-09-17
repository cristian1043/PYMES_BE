from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required
from src.controllers.metodos_pago_controller import MetodosPagoController
from src.utils.security import roles_required

metodos_pago_bp = Blueprint("metodos_pago", __name__)

# ===========================
# Obtener todos los métodos de pago
# ===========================
@metodos_pago_bp.route("/", methods=["GET"])
@jwt_required(optional=True)
def get_metodos_pago():
    metodos_pago = MetodosPagoController.get()
    return jsonify([m.to_dict() for m in metodos_pago]), 200

# ===========================
# Obtener un método de pago por ID 
# ===========================
@metodos_pago_bp.route("/<int:id>", methods=["GET"])
@jwt_required(optional=True)
def get_metodo_pago_by_id(id):
    metodos_pago = MetodosPagoController.get_by_id(id)
    if metodos_pago:  
        return jsonify(metodos_pago.to_dict()), 200
    return jsonify({"error": "Método de pago no encontrado"}), 404

# ===========================
# Crear un nuevo método de pago
# ===========================
@metodos_pago_bp.route("/", methods=["POST"])
@jwt_required()
@roles_required("Administrador", 1)
def create_metodo_pago():
    data = request.get_json() or {}
    metodos_pago = MetodosPagoController.create(data)
    return jsonify(metodos_pago.to_dict()), 201

# ===========================
# Actualizar un método de pago
# ===========================
@metodos_pago_bp.route("/<int:id>", methods=["PUT"])
@jwt_required()
@roles_required("Administrador", 1)
def update_metodo_pago(id):
    data = request.get_json() or {}
    metodos_pago = MetodosPagoController.update(id, data)
    if metodos_pago:
        return jsonify(metodos_pago.to_dict()), 200
    return jsonify({"error": "Método de pago no encontrado"}), 404
    
# ===========================
# Eliminar un método de pago
# ===========================
@metodos_pago_bp.route("/<int:id>", methods=["DELETE"])
@jwt_required()
@roles_required("Administrador", 1)
def delete_metodo_pago(id):
    eliminado = MetodosPagoController.delete(id)
    if eliminado:
        return jsonify({"mensaje": "Método de pago eliminado correctamente"}), 200
    return jsonify({"error": "Método de pago no encontrado"}), 404