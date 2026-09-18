from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt, get_jwt_identity
from src.controllers.compras_controller import ComprasController
from src.models.compras import Compras
from src.utils.pagination import get_pagination_params
from src.utils.security import roles_required, tenant_required

compras_bp = Blueprint("compras", __name__)

def validar_acceso_compra(compra_id, claims):
    """Verifica que el usuario tenga acceso a la empresa de la orden de compra solicitada."""
    rol_usuario = claims.get("rol", "")
    id_rol = claims.get("id_rol", 0)
    if id_rol == 1 or rol_usuario == "Administrador":
        return True, None

    compra = Compras.get_by_id(compra_id)
    if not compra:
        return False, jsonify({"mensaje": "Compra no encontrada"}), 404

    empresas_usuario = [int(e) for e in claims.get("empresas", []) if str(e).isdigit()]
    if compra.id_empresa is not None and int(compra.id_empresa) not in empresas_usuario:
        return False, jsonify({"mensaje": "Acceso denegado: No tienes acceso a los registros de esta empresa."}), 403

    return True, compra

# ===========================
# Obtener todas las compras (paginado)
# ===========================
@compras_bp.route("/", methods=["GET"])
@jwt_required()
@roles_required("Administrador", "Almacenista", 1, 3)
@tenant_required(allow_global_admin=True)
def get_compras():
    page, per_page = get_pagination_params()
    empresa_id = request.args.get("empresa_id") or request.args.get("id_empresa")
    resultado = ComprasController.get_paginated(page, per_page, empresa_id=empresa_id)
    return jsonify(resultado), 200

# ===========================
# Obtener siguiente número de compra
# ===========================
@compras_bp.route("/siguiente_numero", methods=["GET"])
@jwt_required()
def get_siguiente_numero():
    empresa_id = request.args.get("empresa_id") or request.args.get("id_empresa")
    numero = ComprasController.obtener_siguiente_numero(empresa_id=empresa_id)
    return jsonify({"siguiente_numero": numero}), 200

# ===========================
# Cancelar una compra
# ===========================
@compras_bp.route("/<int:id>/cancelar", methods=["POST"])
@jwt_required()
@roles_required("Administrador", "Almacenista", 1, 3)
def cancelar_compra(id):
    claims = get_jwt() or {}
    permitido, err_res, *code = validar_acceso_compra(id, claims)
    if not permitido:
        return err_res, (code[0] if code else 403)

    compra = ComprasController.cancelar(id)
    if compra:
        return jsonify(compra.to_dict()), 200
    return jsonify({"mensaje": "Compra no encontrada"}), 404

# ===========================
# Obtener una compra por ID
# ===========================
@compras_bp.route("/<int:id>", methods=["GET"])
@jwt_required()
@roles_required("Administrador", "Almacenista", 1, 3)
def get_compra(id):
    claims = get_jwt() or {}
    permitido, err_res, *code = validar_acceso_compra(id, claims)
    if not permitido:
        return err_res, (code[0] if code else 403)

    compra = ComprasController.get_by_id(id)
    if compra:
        if isinstance(compra, dict):
            return jsonify(compra), 200
        elif hasattr(compra, "to_dict"):
            return jsonify(compra.to_dict()), 200
    return jsonify({"mensaje": "Compra no encontrada"}), 404

# ===========================
# Crear una compra
# ===========================
@compras_bp.route("/", methods=["POST"])
@jwt_required()
@roles_required("Administrador", "Almacenista", 1, 3)
@tenant_required(allow_global_admin=True)
def create_compra():
    data = request.get_json() or {}
    identity = get_jwt_identity()
    if identity and not data.get("id_usuario"):
        try:
            data["id_usuario"] = int(identity)
        except (ValueError, TypeError):
            pass

    try:
        compra = ComprasController.create(data)
        return jsonify(compra.to_dict()), 201
    except ValueError as ve:
        return jsonify({"mensaje": str(ve)}), 400
    except Exception as e:
        return jsonify({"mensaje": f"Error al registrar compra: {str(e)}"}), 400

# ===========================
# Actualizar una compra
# ===========================
@compras_bp.route("/<int:id>", methods=["PUT"])
@jwt_required()
@roles_required("Administrador", "Almacenista", 1, 3)
def update_compra(id):
    claims = get_jwt() or {}
    permitido, err_res, *code = validar_acceso_compra(id, claims)
    if not permitido:
        return err_res, (code[0] if code else 403)

    data = request.get_json() or {}
    compra = ComprasController.update(id, data)
    if compra:
        return jsonify(compra.to_dict()), 200
    return jsonify({"mensaje": "Compra no encontrada"}), 404

# ===========================
# Eliminar una compra
# ===========================
@compras_bp.route("/<int:id>", methods=["DELETE"])
@jwt_required()
@roles_required("Administrador")
def delete_compra(id):
    claims = get_jwt() or {}
    permitido, err_res, *code = validar_acceso_compra(id, claims)
    if not permitido:
        return err_res, (code[0] if code else 403)

    eliminado = ComprasController.delete(id)
    if eliminado:
        return jsonify({"mensaje": "Compra eliminada correctamente"}), 200
    return jsonify({"mensaje": "Compra no encontrada"}), 404 