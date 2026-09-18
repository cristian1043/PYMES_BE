from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt, get_jwt_identity
from src.controllers.facturas_controller import FacturasController
from src.models.facturas import Facturas
from src.utils.pagination import get_pagination_params
from src.utils.security import roles_required, tenant_required

facturas_bp = Blueprint("facturas", __name__)

def validar_acceso_factura(factura_id, claims):
    """Verifica que el usuario tenga acceso a la empresa de la factura solicitada."""
    rol_usuario = claims.get("rol", "")
    id_rol = claims.get("id_rol", 0)
    if id_rol == 1 or rol_usuario == "Administrador":
        return True, None

    factura = Facturas.get_by_id(factura_id)
    if not factura:
        return False, jsonify({"mensaje": "Factura no encontrada"}), 404

    empresas_usuario = [int(e) for e in claims.get("empresas", []) if str(e).isdigit()]
    if factura.id_empresa is not None and int(factura.id_empresa) not in empresas_usuario:
        return False, jsonify({"mensaje": "Acceso denegado: No tienes acceso a los registros de esta empresa."}), 403

    return True, factura

# ===========================
# Obtener todas las facturas (paginado)
# ===========================
@facturas_bp.route("/", methods=["GET"])
@jwt_required()
@tenant_required(allow_global_admin=True)
def get_facturas():
    page, per_page = get_pagination_params()
    empresa_id = request.args.get("empresa_id") or request.args.get("id_empresa")
    resultado = FacturasController.get_paginated(page, per_page, empresa_id=empresa_id)
    return jsonify(resultado), 200

# ===========================
# Obtener el siguiente número consecutivo de factura
# ===========================
@facturas_bp.route("/siguiente_numero", methods=["GET"])
@jwt_required()
def get_siguiente_numero():
    num = FacturasController.obtener_siguiente_numero()
    return jsonify({"siguiente_numero": num}), 200

# ===========================
# Obtener una factura por ID
# ===========================
@facturas_bp.route("/<int:id>", methods=["GET"])
@jwt_required()
def get_factura(id):
    claims = get_jwt() or {}
    permitido, err_res, *code = validar_acceso_factura(id, claims)
    if not permitido:
        return err_res, (code[0] if code else 403)

    factura = FacturasController.get_by_id(id)
    if factura:
        if isinstance(factura, dict):
            return jsonify(factura), 200
        elif hasattr(factura, "to_dict"):
            return jsonify(factura.to_dict()), 200
    return jsonify({"mensaje": "Factura no encontrada"}), 404

# ===========================
# Crear factura
# ===========================
@facturas_bp.route("/", methods=["POST"])
@jwt_required()
@roles_required("Administrador", "Vendedor", "Contador")
@tenant_required(allow_global_admin=True)
def create_factura():
    data = request.get_json() or {}
    identity = get_jwt_identity()
    if identity and not data.get("id_usuario"):
        try:
            data["id_usuario"] = int(identity)
        except (ValueError, TypeError):
            pass

    try:
        factura = FacturasController.create(data)
        return jsonify(factura.to_dict()), 201
    except ValueError as ve:
        return jsonify({"mensaje": str(ve)}), 400
    except Exception as e:
        return jsonify({"mensaje": f"Error al emitir factura: {str(e)}"}), 400

# ===========================
# Actualizar factura
# ===========================
@facturas_bp.route("/<int:id>", methods=["PUT"])
@jwt_required()
@roles_required("Administrador", "Vendedor", "Contador")
def update_factura(id):
    claims = get_jwt() or {}
    permitido, err_res, *code = validar_acceso_factura(id, claims)
    if not permitido:
        return err_res, (code[0] if code else 403)

    data = request.get_json() or {}
    factura = FacturasController.update(id, data)
    if factura and hasattr(factura, "to_dict"):
        return jsonify(factura.to_dict()), 200
    return jsonify({"mensaje": "Factura no encontrada"}), 404

# ===========================
# Cancelar factura
# ===========================
@facturas_bp.route("/<int:id>/cancelar", methods=["POST"])
@jwt_required()
@roles_required("Administrador", "Vendedor")
def cancelar_factura(id):
    claims = get_jwt() or {}
    permitido, err_res, *code = validar_acceso_factura(id, claims)
    if not permitido:
        return err_res, (code[0] if code else 403)

    factura = FacturasController.cancelar(id)
    if factura:
        return jsonify({"mensaje": "Factura cancelada correctamente", "factura": factura.to_dict()}), 200
    return jsonify({"mensaje": "Factura no encontrada"}), 404

# ===========================
# Eliminar factura
# ===========================
@facturas_bp.route("/<int:id>", methods=["DELETE"])
@jwt_required()
@roles_required("Administrador")
def delete_factura(id):
    claims = get_jwt() or {}
    permitido, err_res, *code = validar_acceso_factura(id, claims)
    if not permitido:
        return err_res, (code[0] if code else 403)

    eliminado = FacturasController.delete(id)
    if eliminado:
        return jsonify({"mensaje": "Factura eliminada correctamente"}), 200
    return jsonify({"mensaje": "Factura no encontrada"}), 404

# ===========================
# Registrar Pago de Pasarela
# ===========================
@facturas_bp.route("/<int:id>/pagar", methods=["POST"])
@jwt_required()
@roles_required("Administrador", "Vendedor", "Contador")
def pagar_factura(id):
    claims = get_jwt() or {}
    permitido, err_res, *code = validar_acceso_factura(id, claims)
    if not permitido:
        return err_res, (code[0] if code else 403)

    data = request.get_json() or {}
    pasarela = data.get("pasarela", "wompi")
    referencia = data.get("referencia_pago") or data.get("referencia")
    id_metodo = data.get("id_metodo_pago")

    factura = FacturasController.registrar_pago_pasarela(id, pasarela=pasarela, referencia_pago=referencia, id_metodo_pago=id_metodo)
    if factura:
        return jsonify({
            "mensaje": "Pago procesado y liquidado con éxito",
            "factura": factura.to_dict()
        }), 200
    return jsonify({"mensaje": "Factura no encontrada"}), 404