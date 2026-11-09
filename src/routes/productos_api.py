from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required
from src.controllers.productos_controller import ProductosController
from src.utils.pagination import get_pagination_params
from src.utils.security import roles_required, tenant_required, verificar_acceso_empresa, obtener_empresa_id_request

productos_bp = Blueprint("productos", __name__)


def validar_acceso_producto(producto):
    if not producto:
        return False
    if not producto.id_empresa:
        return False
    return verificar_acceso_empresa(producto.id_empresa)


@productos_bp.route("/", methods=["GET"])
@jwt_required()
@tenant_required(allow_global_admin=True)
def get_productos():
    page, per_page = get_pagination_params()
    empresa_id = obtener_empresa_id_request()
    resultado = ProductosController.get_paginated(page, per_page, empresa_id=empresa_id)
    return jsonify(resultado), 200


@productos_bp.route("/siguiente_codigo", methods=["GET"])
@jwt_required()
@tenant_required(allow_global_admin=True)
def get_siguiente_codigo():
    empresa_id = obtener_empresa_id_request()
    codigo = ProductosController.obtener_siguiente_codigo(empresa_id=empresa_id)
    return jsonify({"siguiente_codigo": codigo}), 200


@productos_bp.route("/<int:id>", methods=["GET"])
@jwt_required()
def get_producto(id):
    producto = ProductosController.get_by_id(id)
    if not producto:
        return jsonify({"mensaje": "Producto no encontrado"}), 404
    if not validar_acceso_producto(producto):
        return jsonify({"exito": False, "mensaje": "Acceso denegado: El producto no pertenece a la empresa autorizada."}), 403
    return jsonify(producto.to_dict()), 200


@productos_bp.route("/", methods=["POST"])
@jwt_required()
@roles_required("Administrador", "Vendedor", "Almacenista", 1, 2, 3)
@tenant_required(allow_global_admin=True)
def create_producto():
    data = request.get_json() or {}
    emp_id = data.get("id_empresa") or data.get("empresa_id") or obtener_empresa_id_request()
    if emp_id:
        if not verificar_acceso_empresa(emp_id):
            return jsonify({"exito": False, "mensaje": "No tienes permisos para crear productos en esta empresa."}), 403
        data["id_empresa"] = int(emp_id)
    try:
        producto = ProductosController.create(data)
        return jsonify(producto.to_dict()), 201
    except ValueError as ve:
        return jsonify({"exito": False, "mensaje": str(ve)}), 400


@productos_bp.route("/<int:id>", methods=["PUT"])
@jwt_required()
@roles_required("Administrador", "Vendedor", "Almacenista", 1, 2, 3)
def update_producto(id):
    producto = ProductosController.get_by_id(id)
    if not producto:
        return jsonify({"mensaje": "Producto no encontrado"}), 404
    if not validar_acceso_producto(producto):
        return jsonify({"exito": False, "mensaje": "Acceso denegado: No tiene permisos sobre productos de esta empresa."}), 403
    data = request.get_json() or {}
    try:
        producto_actualizado = ProductosController.update(id, data)
        return jsonify(producto_actualizado.to_dict()), 200
    except ValueError as ve:
        return jsonify({"exito": False, "mensaje": str(ve)}), 400


@productos_bp.route("/<int:id>/estado", methods=["PATCH"])
@jwt_required()
@roles_required("Administrador", 1)
def toggle_estado_producto(id):
    producto = ProductosController.get_by_id(id)
    if not producto:
        return jsonify({"mensaje": "Producto no encontrado"}), 404
    if not validar_acceso_producto(producto):
        return jsonify({"exito": False, "mensaje": "Acceso denegado: No tiene permisos sobre productos de esta empresa."}), 403
    data = request.get_json() or {}
    nuevo_estado = data.get("estado", "Inactivo")
    producto_actualizado = ProductosController.desactivar(id, estado=nuevo_estado)
    return jsonify({"mensaje": f"Producto actualizado a estado {nuevo_estado}", "producto": producto_actualizado.to_dict()}), 200


@productos_bp.route("/<int:id>", methods=["DELETE"])
@jwt_required()
@roles_required("Administrador", 1)
def delete_producto(id):
    producto = ProductosController.get_by_id(id)
    if not producto:
        return jsonify({"mensaje": "Producto no encontrado"}), 404
    if not validar_acceso_producto(producto):
        return jsonify({"exito": False, "mensaje": "Acceso denegado: No tiene permisos sobre productos de esta empresa."}), 403
    eliminado = ProductosController.delete(id)
    if eliminado:
        return jsonify({"mensaje": "Producto desactivado correctamente"}), 200
    return jsonify({"mensaje": "Producto no encontrado"}), 404
