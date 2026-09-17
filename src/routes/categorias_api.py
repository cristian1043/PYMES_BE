from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required
from src.controllers.categorias_controller import CategoriasController
from src.utils.security import roles_required

categorias_bp = Blueprint("categorias", __name__)

# ===========================
# Obtener todas las categorías
# ===========================
@categorias_bp.route("/", methods=["GET"])
@jwt_required(optional=True)
def get_categorias():
    categorias = CategoriasController.get()
    return jsonify([c.to_dict() for c in categorias]), 200

# ===========================
# Obtener una categoría
# ===========================
@categorias_bp.route("/<int:id>", methods=["GET"])
@jwt_required(optional=True)
def get_categoria(id):
    categoria = CategoriasController.get_by_id(id)
    if categoria:
        return jsonify(categoria.to_dict()), 200
    return jsonify({"mensaje": "Categoría no encontrada"}), 404

# ===========================
# Crear categoría
# ===========================
@categorias_bp.route("/", methods=["POST"])
@jwt_required()
@roles_required("Administrador", 1)
def create_categoria():
    data = request.get_json() or {}
    categoria = CategoriasController.create(data)
    return jsonify(categoria.to_dict()), 201

# ===========================
# Actualizar categoría
# ===========================
@categorias_bp.route("/<int:id>", methods=["PUT"])
@jwt_required()
@roles_required("Administrador", 1)
def update_categoria(id):
    data = request.get_json() or {}
    categoria = CategoriasController.update(id, data)
    if categoria:
        return jsonify(categoria.to_dict()), 200
    return jsonify({"mensaje": "Categoría no encontrada"}), 404

# ===========================
# Eliminar categoría
# ===========================
@categorias_bp.route("/<int:id>", methods=["DELETE"])
@jwt_required()
@roles_required("Administrador", 1)
def delete_categoria(id):
    eliminado = CategoriasController.delete(id)
    if eliminado:
        return jsonify({"mensaje": "Categoría eliminada correctamente"}), 200
    return jsonify({"mensaje": "Categoría no encontrada"}), 404