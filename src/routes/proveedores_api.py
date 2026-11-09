from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required
from src.controllers.proveedores_controller import ProveedoresController
from src.utils.pagination import get_pagination_params
from src.utils.security import roles_required, tenant_required, verificar_acceso_empresa, obtener_empresa_id_request

proveedores_bp = Blueprint("proveedores", __name__)


def _validar_acceso_proveedor(proveedor):
    if not proveedor:
        return jsonify({"mensaje": "Proveedor no encontrado"}), 404
    if not getattr(proveedor, "id_empresa", None) or not verificar_acceso_empresa(proveedor.id_empresa):
        return jsonify({"mensaje": "No tienes permisos para acceder a proveedores de otra empresa"}), 403
    return None


@proveedores_bp.route("/", methods=["GET"])
@jwt_required()
@tenant_required(allow_global_admin=True)
def get_proveedores():
    page, per_page = get_pagination_params()
    empresa_id = obtener_empresa_id_request()
    resultado = ProveedoresController.get_paginated(page, per_page, empresa_id=empresa_id)
    return jsonify(resultado), 200


@proveedores_bp.route("/siguiente-codigo", methods=["GET"])
@jwt_required()
@tenant_required(allow_global_admin=True)
def get_siguiente_codigo():
    empresa_id = obtener_empresa_id_request()
    codigo = ProveedoresController.obtener_siguiente_codigo(empresa_id)
    return jsonify({"siguiente_codigo": codigo}), 200


@proveedores_bp.route("/<int:id>", methods=["GET"])
@jwt_required()
def get_proveedor(id):
    proveedor = ProveedoresController.get_by_id(id)
    err = _validar_acceso_proveedor(proveedor)
    if err:
        return err
    return jsonify(proveedor.to_dict()), 200


@proveedores_bp.route("/", methods=["POST"])
@jwt_required()
@roles_required("Administrador", "Vendedor", "Almacenista", 1, 2, 3)
@tenant_required(allow_global_admin=True)
def create_proveedor():
    data = request.get_json() or {}
    emp_id = data.get("id_empresa") or data.get("empresa_id") or obtener_empresa_id_request()
    if not emp_id or not verificar_acceso_empresa(emp_id):
        return jsonify({"mensaje": "No tienes permisos para registrar proveedores en esta empresa."}), 403
    data["id_empresa"] = int(emp_id)
    try:
        proveedor = ProveedoresController.create(data)
        return jsonify(proveedor.to_dict()), 201
    except ValueError as ve:
        return jsonify({"mensaje": str(ve)}), 400


@proveedores_bp.route("/<int:id>", methods=["PUT"])
@jwt_required()
@roles_required("Administrador", "Vendedor", "Almacenista", 1, 2, 3)
def update_proveedor(id):
    proveedor_actual = ProveedoresController.get_by_id(id)
    err = _validar_acceso_proveedor(proveedor_actual)
    if err:
        return err
    data = request.get_json() or {}
    try:
        proveedor = ProveedoresController.update(id, data)
        if proveedor:
            return jsonify(proveedor.to_dict()), 200
        return jsonify({"mensaje": "Proveedor no encontrado"}), 404
    except ValueError as ve:
        return jsonify({"mensaje": str(ve)}), 400


@proveedores_bp.route("/<int:id>/estado", methods=["PATCH"])
@jwt_required()
@roles_required("Administrador", 1)
def toggle_estado_proveedor(id):
    proveedor_actual = ProveedoresController.get_by_id(id)
    err = _validar_acceso_proveedor(proveedor_actual)
    if err:
        return err
    data = request.get_json() or {}
    nuevo_estado = data.get("estado", "Inactivo")
    proveedor = ProveedoresController.desactivar(id, estado=nuevo_estado)
    if proveedor and hasattr(proveedor, "to_dict"):
        return jsonify({"mensaje": f"Proveedor actualizado a estado {nuevo_estado}", "proveedor": proveedor.to_dict()}), 200
    return jsonify({"mensaje": "Proveedor no encontrado"}), 404


@proveedores_bp.route("/<int:id>", methods=["DELETE"])
@jwt_required()
@roles_required("Administrador", 1)
def delete_proveedor(id):
    proveedor_actual = ProveedoresController.get_by_id(id)
    err = _validar_acceso_proveedor(proveedor_actual)
    if err:
        return err
    eliminado = ProveedoresController.delete(id)
    if eliminado:
        return jsonify({"mensaje": "Proveedor desactivado correctamente"}), 200
    return jsonify({"mensaje": "Proveedor no encontrado"}), 404
