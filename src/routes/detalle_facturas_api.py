from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt
from src.controllers.detalle_facturas_controller import DetalleFacturasController
from src.routes.facturas_api import validar_acceso_factura
from src.utils.security import roles_required

detalle_facturas_bp = Blueprint("detalle_facturas", __name__)

# ===========================
# Obtener todos los detalles (filtrados por acceso a la factura)
# ===========================
@detalle_facturas_bp.route("/", methods=["GET"])
@jwt_required()
def get_detalles():
    claims = get_jwt() or {}
    id_factura = request.args.get("id_factura")
    detalles = DetalleFacturasController.get()
    if id_factura and str(id_factura).isdigit():
        detalles = [d for d in detalles if d.id_factura == int(id_factura)]
    permitidos = [d.to_dict() for d in detalles if validar_acceso_factura(d.id_factura, claims)[0]]
    return jsonify(permitidos), 200

# ===========================
# Obtener un detalle
# ===========================
@detalle_facturas_bp.route("/<int:id>", methods=["GET"])
@jwt_required()
def get_detalle(id):
    detalle = DetalleFacturasController.get_by_id(id)
    if not detalle:
        return jsonify({"mensaje": "Detalle de factura no encontrado"}), 404
    permitido, err_res, *code = validar_acceso_factura(detalle.id_factura, get_jwt() or {})
    if not permitido:
        return err_res, (code[0] if code else 403)
    return jsonify(detalle.to_dict()), 200

# ===========================
# Crear detalle
# ===========================
@detalle_facturas_bp.route("/", methods=["POST"])
@jwt_required()
@roles_required("Administrador", "Vendedor", 1, 2)
def create_detalle():
    data = request.get_json() or {}
    id_factura = data.get("id_factura")
    if not id_factura:
        return jsonify({"mensaje": "Se requiere 'id_factura'"}), 400
    permitido, err_res, *code = validar_acceso_factura(int(id_factura), get_jwt() or {})
    if not permitido:
        return err_res, (code[0] if code else 403)
    detalle = DetalleFacturasController.create(data)
    return jsonify(detalle.to_dict()), 201

# ===========================
# Actualizar detalle
# ===========================
@detalle_facturas_bp.route("/<int:id>", methods=["PUT"])
@jwt_required()
@roles_required("Administrador", 1)
def update_detalle(id):
    existente = DetalleFacturasController.get_by_id(id)
    if not existente:
        return jsonify({"mensaje": "Detalle de factura no encontrado"}), 404
    permitido, err_res, *code = validar_acceso_factura(existente.id_factura, get_jwt() or {})
    if not permitido:
        return err_res, (code[0] if code else 403)
    data = request.get_json() or {}
    detalle = DetalleFacturasController.update(id, data)
    return jsonify(detalle.to_dict()), 200

# ===========================
# Eliminar detalle
# ===========================
@detalle_facturas_bp.route("/<int:id>", methods=["DELETE"])
@jwt_required()
@roles_required("Administrador", 1)
def delete_detalle(id):
    existente = DetalleFacturasController.get_by_id(id)
    if not existente:
        return jsonify({"mensaje": "Detalle de factura no encontrado"}), 404
    permitido, err_res, *code = validar_acceso_factura(existente.id_factura, get_jwt() or {})
    if not permitido:
        return err_res, (code[0] if code else 403)
    eliminado = DetalleFacturasController.delete(id)
    if eliminado:
        return jsonify({"mensaje": "Detalle de factura eliminado correctamente"}), 200
    return jsonify({"mensaje": "Detalle de factura no encontrado"}), 404
