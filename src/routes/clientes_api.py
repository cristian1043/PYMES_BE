from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required
from src.controllers.clientes_controller import ClientesController
from src.utils.pagination import get_pagination_params
from src.utils.security import roles_required

clientes_bp = Blueprint("clientes", __name__)

# ===========================
# Obtener clientes (con paginación)
# ===========================
@clientes_bp.route("/", methods=["GET"])
@jwt_required(optional=True)
def get_clientes():
    page, per_page = get_pagination_params()
    resultado = ClientesController.get_paginated(page, per_page)
    return jsonify(resultado), 200

# ===========================
# Obtener un cliente por ID
# ===========================
@clientes_bp.route("/<int:id>", methods=["GET"])
@jwt_required(optional=True)
def get_cliente(id):
    cliente = ClientesController.get_by_id(id)
    if cliente and hasattr(cliente, "to_dict"):
        return jsonify(cliente.to_dict()), 200
    return jsonify({"mensaje": "Cliente no encontrado"}), 404

# ===========================
# Crear cliente
# ===========================
@clientes_bp.route("/", methods=["POST"])
@jwt_required(optional=True)
@roles_required("Administrador", "Vendedor")
def create_cliente():
    data = request.get_json() or {}
    cliente = ClientesController.create(data)
    return jsonify(cliente.to_dict()), 201

# ===========================
# Actualizar cliente
# ===========================
@clientes_bp.route("/<int:id>", methods=["PUT"])
@jwt_required(optional=True)
@roles_required("Administrador", "Vendedor")
def update_cliente(id):
    data = request.get_json() or {}
    cliente = ClientesController.update(id, data)
    if cliente and hasattr(cliente, "to_dict"):
        return jsonify(cliente.to_dict()), 200
    return jsonify({"mensaje": "Cliente no encontrado"}), 404

# ===========================
# Eliminar cliente
# ===========================
@clientes_bp.route("/<int:id>", methods=["DELETE"])
@jwt_required()
@roles_required("Administrador")
def delete_cliente(id):
    eliminado = ClientesController.delete(id)
    if eliminado:
        return jsonify({"mensaje": "Cliente eliminado correctamente"}), 200
    return jsonify({"mensaje": "Cliente no encontrado"}), 404