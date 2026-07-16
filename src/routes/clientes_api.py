from flask import Blueprint, request, jsonify
from src.controllers.clientes_controller import ClientesController

clientes_bp = Blueprint("clientes", __name__)


# ===========================
# Obtener todos los clientes
# ===========================
@clientes_bp.route("/", methods=["GET"])
def get_clientes():
    clientes = ClientesController.get()
    return jsonify([c.to_dict() for c in clientes]), 200


# ===========================
# Obtener un cliente
# ===========================
@clientes_bp.route("/<int:id>", methods=["GET"])
def get_cliente(id):
    cliente = ClientesController.get_by_id(id)

    if cliente:
        return jsonify(cliente.to_dict()), 200

    return jsonify({
        "mensaje": "Cliente no encontrado"
    }), 404


# ===========================
# Crear cliente
# ===========================
@clientes_bp.route("/", methods=["POST"])
def create_cliente():
    data = request.get_json()

    cliente = ClientesController.save(data)

    return jsonify(cliente.to_dict()), 


# ===========================
# Actualizar cliente
# ===========================
@clientes_bp.route("/<int:id>", methods=["PUT"])
def update_cliente(id):

    data = request.get_json()

    return jsonify(data), 200


# ===========================
# Eliminar cliente
# ===========================
@clientes_bp.route("/<int:id>", methods=["DELETE"])
def delete_cliente(id):

    eliminado = ClientesController.delete(id)

    if eliminado:
        return jsonify({
            "mensaje": "Cliente eliminado correctamente"
        }), 200

    return jsonify({
        "mensaje": "Cliente no encontrado"
    }), 404