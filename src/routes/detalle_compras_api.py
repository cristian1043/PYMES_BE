from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt
from src.controllers.detalle_compras_controller import DetalleComprasController
from src.routes.compras_api import validar_acceso_compra
from src.utils.security import roles_required

detalle_compras_bp = Blueprint("detalle_compras", __name__)

# ===========================
# Obtener todos los detalles (filtrados por acceso a la compra)
# ===========================
@detalle_compras_bp.route("/", methods=["GET"])
@jwt_required()
def get_detalles():
    claims = get_jwt() or {}
    id_compra = request.args.get("id_compra")
    detalles = DetalleComprasController.get()
    if id_compra and str(id_compra).isdigit():
        detalles = [d for d in detalles if d.id_compra == int(id_compra)]
    permitidos = [c.to_dict() for c in detalles if validar_acceso_compra(c.id_compra, claims)[0]]
    return jsonify(permitidos), 200

# ===========================
# Obtener un detalle por ID
# ===========================
@detalle_compras_bp.route("/<int:id>", methods=["GET"])
@jwt_required()
def get_detalle(id):
    detalle = DetalleComprasController.get_by_id(id)
    if not detalle:
        return jsonify({"mensaje": "Detalle de compra no encontrado"}), 404
    permitido, err_res, *code = validar_acceso_compra(detalle.id_compra, get_jwt() or {})
    if not permitido:
        return err_res, (code[0] if code else 403)
    return jsonify(detalle.to_dict()), 200

# ===========================
# Crear un detalle
# ===========================
@detalle_compras_bp.route("/", methods=["POST"])
@jwt_required()
@roles_required("Administrador", "Almacenista", 1, 3)
def create_detalle():
    data = request.get_json() or {}
    id_compra = data.get("id_compra")
    if not id_compra:
        return jsonify({"mensaje": "Se requiere 'id_compra'"}), 400
    permitido, err_res, *code = validar_acceso_compra(int(id_compra), get_jwt() or {})
    if not permitido:
        return err_res, (code[0] if code else 403)
    detalle = DetalleComprasController.create(data)
    return jsonify(detalle.to_dict()), 201

# ===========================
# Actualizar un detalle
# ===========================
@detalle_compras_bp.route("/<int:id>", methods=["PUT"])
@jwt_required()
@roles_required("Administrador", 1)
def update_detalle(id):
    existente = DetalleComprasController.get_by_id(id)
    if not existente:
        return jsonify({"mensaje": "Detalle de compra no encontrado"}), 404
    permitido, err_res, *code = validar_acceso_compra(existente.id_compra, get_jwt() or {})
    if not permitido:
        return err_res, (code[0] if code else 403)
    data = request.get_json() or {}
    detalle = DetalleComprasController.update(id, data)
    return jsonify(detalle.to_dict()), 200

# ===========================
# Eliminar un detalle
# ===========================
@detalle_compras_bp.route("/<int:id>", methods=["DELETE"])
@jwt_required()
@roles_required("Administrador", 1)
def delete_detalle(id):
    existente = DetalleComprasController.get_by_id(id)
    if not existente:
        return jsonify({"mensaje": "Detalle de compra no encontrado"}), 404
    permitido, err_res, *code = validar_acceso_compra(existente.id_compra, get_jwt() or {})
    if not permitido:
        return err_res, (code[0] if code else 403)
    eliminado = DetalleComprasController.delete(id)
    if eliminado:
        return jsonify({"mensaje": "Detalle de compra eliminado correctamente"}), 200
    return jsonify({"mensaje": "Detalle de compra no encontrado"}), 404
