from flask import Blueprint, request, jsonify
from src.controllers.categorias_controller import CategoriasController

categorias_bp = Blueprint("categorias", __name__)

# ===========================
# Obtener todas las categorías
# ===========================
@categorias_bp.route("/", methods=["GET"])
def get_categorias():
    categorias = CategoriasController.get()
    return jsonify([c.to_dict() for c in categorias]), 200


# ===========================
# Obtener una categoría
# ===========================
@categorias_bp.route("/<int:id>", methods=["GET"])
def get_categoria(id):
    categoria = CategoriasController.get_by_id(id)

    if categoria:
        return jsonify(categoria.to_dict()), 200

    return jsonify({
        "mensaje": "Categoría no encontrada"
    }), 404


# ===========================
# Crear categoría
# ===========================
@categorias_bp.route("/", methods=["POST"])
def create_categoria():
    data = request.get_json()

    categoria = CategoriasController.save(data)
    
    print(data)

    return jsonify(categoria.to_dict()), 201


# ===========================
# Actualizar categoría
# ===========================
@categorias_bp.route("/<int:id>", methods=["PUT"])
def update_categoria(id):
    data = request.get_json()

    categoria = CategoriasController.update(id, data)

    if categoria:
        return jsonify(categoria.to_dict()), 200

    return jsonify({
        "mensaje": "Categoría no encontrada"
    }), 404


# ===========================
# Eliminar categoría
# ===========================
@categorias_bp.route("/<int:id>", methods=["DELETE"])
def delete_categoria(id):

    eliminado = CategoriasController.delete(id)

    if eliminado:
        return jsonify({
            "mensaje": "Categoría eliminada correctamente"
        }), 200

    return jsonify({
        "mensaje": "Categoría no encontrada"
    }), 404