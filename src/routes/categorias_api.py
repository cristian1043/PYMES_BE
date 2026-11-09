from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required
from src.controllers.categorias_controller import CategoriasController
from src.utils.security import (
    roles_required,
    verificar_acceso_empresa,
    obtener_empresa_id_request,
    es_super_admin_actual,
)

categorias_bp = Blueprint("categorias", __name__)


@categorias_bp.route("/", methods=["GET"])
@categorias_bp.route("", methods=["GET"])
@jwt_required(optional=True)
def get_categorias():
    empresa_id = obtener_empresa_id_request()
    categorias = CategoriasController.get(empresa_id=empresa_id, include_global=True)
    return jsonify([c.to_dict() for c in categorias]), 200


@categorias_bp.route("/<int:id>", methods=["GET"])
@jwt_required(optional=True)
def get_categoria(id):
    categoria = CategoriasController.get_by_id(id)
    if not categoria:
        return jsonify({"mensaje": "Categoría no encontrada"}), 404
    if categoria.id_empresa is not None:
        emp_req = obtener_empresa_id_request()
        if emp_req and int(emp_req) != int(categoria.id_empresa):
            return jsonify({"mensaje": "La categoría no pertenece a la empresa activa."}), 403
    return jsonify(categoria.to_dict()), 200


@categorias_bp.route("/", methods=["POST"])
@categorias_bp.route("", methods=["POST"])
@jwt_required()
@roles_required("Administrador", "Almacenista", 1, 3)
def create_categoria():
    data = request.get_json() or {}
    emp_id = data.get("id_empresa") or data.get("empresa_id") or obtener_empresa_id_request()
    if emp_id:
        if not verificar_acceso_empresa(emp_id):
            return jsonify({"mensaje": "No tienes permisos en la empresa indicada para crear categorías."}), 403
        data["id_empresa"] = int(emp_id)
    elif not es_super_admin_actual():
        return jsonify({"mensaje": "Se requiere 'id_empresa' para crear una categoría."}), 400

    try:
        categoria = CategoriasController.create(data)
        return jsonify(categoria.to_dict()), 201
    except ValueError as ve:
        return jsonify({"mensaje": str(ve)}), 400


@categorias_bp.route("/<int:id>", methods=["PUT"])
@jwt_required()
@roles_required("Administrador", "Almacenista", 1, 3)
def update_categoria(id):
    categoria_actual = CategoriasController.get_by_id(id)
    if not categoria_actual:
        return jsonify({"mensaje": "Categoría no encontrada"}), 404

    if categoria_actual.id_empresa is None:
        if not es_super_admin_actual():
            return jsonify({"mensaje": "No se pueden modificar las categorías globales base del sistema."}), 403
    elif not verificar_acceso_empresa(categoria_actual.id_empresa):
        return jsonify({"mensaje": "No tienes permisos sobre categorías de otra empresa."}), 403

    data = request.get_json() or {}
    categoria = CategoriasController.update(id, data)
    return jsonify(categoria.to_dict()), 200


@categorias_bp.route("/<int:id>", methods=["DELETE"])
@jwt_required()
@roles_required("Administrador", 1)
def delete_categoria(id):
    categoria_actual = CategoriasController.get_by_id(id)
    if not categoria_actual:
        return jsonify({"mensaje": "Categoría no encontrada"}), 404

    if categoria_actual.id_empresa is None:
        if not es_super_admin_actual():
            return jsonify({"mensaje": "No se pueden eliminar las categorías globales base del sistema."}), 403
    elif not verificar_acceso_empresa(categoria_actual.id_empresa):
        return jsonify({"mensaje": "No tienes permisos sobre categorías de otra empresa."}), 403

    eliminado = CategoriasController.delete(id)
    if eliminado:
        return jsonify({"mensaje": "Categoría eliminada correctamente"}), 200
    return jsonify({"mensaje": "Categoría no encontrada"}), 404
