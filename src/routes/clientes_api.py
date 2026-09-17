from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required
from src.controllers.clientes_controller import ClientesController
from src.utils.pagination import get_pagination_params
from src.utils.security import roles_required, tenant_required

clientes_bp = Blueprint("clientes", __name__)

# ===========================
# Obtener clientes (con paginación)
# ===========================
@clientes_bp.route("/", methods=["GET"])
@jwt_required()
@tenant_required(allow_global_admin=True)
def get_clientes():
    page, per_page = get_pagination_params()
    empresa_id = (
        request.args.get("empresa_id") or 
        request.args.get("id_empresa") or 
        request.headers.get("X-Empresa-ID") or 
        request.environ.get('tenant_empresa_id')
    )
    resultado = ClientesController.get_paginated(page, per_page, empresa_id=empresa_id)
    return jsonify(resultado), 200

# ===========================
# Buscar cliente por documento
# ===========================
@clientes_bp.route("/buscar", methods=["GET"])
@jwt_required()
@tenant_required(allow_global_admin=True)
def buscar_cliente():
    documento = request.args.get("documento")
    empresa_id = (
        request.args.get("empresa_id") or 
        request.args.get("id_empresa") or 
        request.headers.get("X-Empresa-ID") or 
        request.environ.get('tenant_empresa_id')
    )
    if not documento:
        return jsonify({"mensaje": "Parámetro 'documento' es requerido"}), 400
    cliente = ClientesController.buscar_por_documento(documento, empresa_id=empresa_id)
    if cliente and hasattr(cliente, "to_dict"):
        return jsonify(cliente.to_dict()), 200
    return jsonify({"mensaje": "Cliente no encontrado"}), 404

# ===========================
# Obtener un cliente por ID
# ===========================
@clientes_bp.route("/<int:id>", methods=["GET"])
@jwt_required()
def get_cliente(id):
    cliente = ClientesController.get_by_id(id)
    if cliente and hasattr(cliente, "to_dict"):
        return jsonify(cliente.to_dict()), 200
    return jsonify({"mensaje": "Cliente no encontrado"}), 404

# ===========================
# Crear cliente
# ===========================
@clientes_bp.route("/", methods=["POST"])
@jwt_required()
@roles_required("Administrador", "Vendedor", 1, 2)
@tenant_required(allow_global_admin=True)
def create_cliente():
    data = request.get_json() or {}
    if not data.get("id_empresa"):
        emp_id = (
            request.headers.get("X-Empresa-ID") or 
            request.args.get("empresa_id") or 
            request.args.get("id_empresa") or 
            request.environ.get('tenant_empresa_id')
        )
        if emp_id:
            data["id_empresa"] = emp_id
    cliente = ClientesController.create(data)
    return jsonify(cliente.to_dict()), 201

# ===========================
# Actualizar cliente
# ===========================
@clientes_bp.route("/<int:id>", methods=["PUT"])
@jwt_required()
@roles_required("Administrador", "Vendedor", 1, 2)
def update_cliente(id):
    data = request.get_json() or {}
    cliente = ClientesController.update(id, data)
    if cliente and hasattr(cliente, "to_dict"):
        return jsonify(cliente.to_dict()), 200
    return jsonify({"mensaje": "Cliente no encontrado"}), 404

# ===========================
# Cambiar estado del cliente (Activar / Desactivar)
# ===========================
@clientes_bp.route("/<int:id>/estado", methods=["PATCH"])
@jwt_required()
@roles_required("Administrador", 1)
def toggle_estado_cliente(id):
    data = request.get_json() or {}
    nuevo_estado = data.get("estado", "Inactivo")
    cliente = ClientesController.desactivar(id, estado=nuevo_estado)
    if cliente and hasattr(cliente, "to_dict"):
        return jsonify({"mensaje": f"Cliente actualizado a estado {nuevo_estado}", "cliente": cliente.to_dict()}), 200
    return jsonify({"mensaje": "Cliente no encontrado"}), 404

# ===========================
# Eliminar cliente
# ===========================
@clientes_bp.route("/<int:id>", methods=["DELETE"])
@jwt_required()
@roles_required("Administrador", 1)
def delete_cliente(id):
    eliminado = ClientesController.delete(id)
    if eliminado:
        return jsonify({"mensaje": "Cliente desactivado correctamente"}), 200
    return jsonify({"mensaje": "Cliente no encontrado"}), 404