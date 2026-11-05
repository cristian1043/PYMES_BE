from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt, get_jwt_identity
from src.controllers.facturas_controller import FacturasController
from src.models.facturas import Facturas
from src.utils.pagination import get_pagination_params
from src.utils.security import roles_required, tenant_required

facturas_bp = Blueprint("facturas", __name__)

def _resolver_empresa_id(data=None):
    """Resuelve id_empresa desde body JSON, header X-Empresa-ID, query params, entorno tenant o JWT."""
    emp_id = None
    if isinstance(data, dict):
        emp_id = data.get("id_empresa") or data.get("empresa_id")
    if not emp_id:
        emp_id = (
            request.headers.get("X-Empresa-ID")
            or request.args.get("empresa_id")
            or request.args.get("id_empresa")
            or request.environ.get("tenant_empresa_id")
        )
    if not emp_id:
        try:
            claims = get_jwt() or {}
            empresas_jwt = [int(e) for e in claims.get("empresas", []) if str(e).isdigit()]
            if empresas_jwt:
                emp_id = empresas_jwt[0]
        except Exception:
            pass
    return emp_id

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
    empresa_id = _resolver_empresa_id()
    resultado = FacturasController.get_paginated(page, per_page, empresa_id=empresa_id)
    return jsonify(resultado), 200

# ===========================
# Obtener el siguiente número consecutivo de factura
# ===========================
@facturas_bp.route("/siguiente_numero", methods=["GET"])
@jwt_required()
def get_siguiente_numero():
    emp_id = _resolver_empresa_id()
    num = FacturasController.obtener_siguiente_numero(empresa_id=emp_id)
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
@roles_required("Administrador", "Vendedor", "Almacenista", "Contador", 1, 2, 3)
@tenant_required(allow_global_admin=True)
def create_factura():
    data = request.get_json() or {}
    emp_id = _resolver_empresa_id(data)
    if emp_id and not data.get("id_empresa"):
        data["id_empresa"] = emp_id

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
@roles_required("Administrador", "Vendedor", "Almacenista", "Contador", 1, 2, 3)
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
@roles_required("Administrador", "Vendedor", "Almacenista", 1, 2, 3)
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
# Registrar pago manual (métodos SIN pasarela integrada: efectivo, transferencia, datáfono no integrado...)
# ===========================
@facturas_bp.route("/<int:id>/pagar", methods=["POST"])
@jwt_required()
@roles_required("Administrador", "Vendedor", "Almacenista", "Contador", 1, 2, 3)
def pagar_factura(id):
    claims = get_jwt() or {}
    permitido, err_res, *code = validar_acceso_factura(id, claims)
    if not permitido:
        return err_res, (code[0] if code else 403)

    data = request.get_json() or {}
    pasarela = data.get("pasarela", "manual")
    referencia = data.get("referencia_pago") or data.get("referencia")
    id_metodo = data.get("id_metodo_pago")

    try:
        factura = FacturasController.registrar_pago_pasarela(id, pasarela=pasarela, referencia_pago=referencia, id_metodo_pago=id_metodo)
    except ValueError as ve:
        return jsonify({"mensaje": str(ve)}), 400
    if factura:
        return jsonify({
            "mensaje": "Pago procesado y liquidado con éxito",
            "factura": factura.to_dict()
        }), 200
    return jsonify({"mensaje": "Factura no encontrada"}), 404

# ===========================
# Cobros con pasarela / terminal integrada (Bold datáfono, Wompi link, Simulado)
# ===========================
@facturas_bp.route("/<int:id>/cobros", methods=["POST"])
@jwt_required()
@roles_required("Administrador", "Vendedor", "Almacenista", "Contador", 1, 2, 3)
def crear_cobro_factura(id):
    claims = get_jwt() or {}
    permitido, err_res, *code = validar_acceso_factura(id, claims)
    if not permitido:
        return err_res, (code[0] if code else 403)

    from src.services.pagos.cobros_service import CobrosService, ErrorCobro
    from src.routes.cobros_api import url_publica_base
    data = request.get_json() or {}
    id_usuario = None
    try:
        id_usuario = int(get_jwt_identity())
    except (ValueError, TypeError):
        pass
    try:
        tx, factura = CobrosService.crear_cobro(id, data, id_usuario=id_usuario, base_url=url_publica_base())
    except ErrorCobro as ec:
        return jsonify({"mensaje": str(ec)}), 400
    return jsonify({"cobro": tx.to_dict(), "factura": factura.to_dict()}), 201

@facturas_bp.route("/<int:id>/cobros", methods=["GET"])
@jwt_required()
def listar_cobros_factura(id):
    claims = get_jwt() or {}
    permitido, err_res, *code = validar_acceso_factura(id, claims)
    if not permitido:
        return err_res, (code[0] if code else 403)

    from src.services.pagos.cobros_service import CobrosService
    return jsonify([tx.to_dict() for tx in CobrosService.listar_por_factura(id)]), 200
