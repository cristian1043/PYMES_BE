import os
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt
from src.models.facturas import Facturas
from src.models.transacciones_pago import TransaccionesPago
from src.services.pagos.cobros_service import CobrosService, ErrorCobro
from src.utils.security import roles_required

cobros_bp = Blueprint("cobros", __name__)


def url_publica_base():
    """URL pública del backend (para redirecciones de pasarela). Configurable con PUBLIC_BASE_URL."""
    base = os.environ.get("PUBLIC_BASE_URL")
    if base:
        return base.rstrip("/")
    try:
        return request.host_url.rstrip("/")
    except RuntimeError:
        return None


def _cargar_cobro_con_acceso(id):
    from src.routes.facturas_api import validar_acceso_factura
    tx = TransaccionesPago.get_by_id(id)
    if not tx:
        return None, (jsonify({"mensaje": "Cobro no encontrado"}), 404)
    permitido, err_res, *code = validar_acceso_factura(tx.id_factura, get_jwt() or {})
    if not permitido:
        return None, (err_res, code[0] if code else 403)
    return tx, None


def _respuesta(tx, status=200):
    factura = Facturas.get_by_id(tx.id_factura)
    return jsonify({"cobro": tx.to_dict(), "factura": factura.to_dict() if factura else None}), status


# ===========================
# Estado de un cobro (la app lo consulta periódicamente mientras está PENDIENTE)
# ===========================
@cobros_bp.route("/<int:id>", methods=["GET"])
@jwt_required()
def get_cobro(id):
    tx, err = _cargar_cobro_con_acceso(id)
    if err:
        return err
    CobrosService.refrescar(tx)
    return _respuesta(tx)


# ===========================
# Cancelar un cobro pendiente
# ===========================
@cobros_bp.route("/<int:id>/cancelar", methods=["POST"])
@jwt_required()
@roles_required("Administrador", "Vendedor", "Almacenista", "Contador", 1, 2, 3)
def cancelar_cobro(id):
    tx, err = _cargar_cobro_con_acceso(id)
    if err:
        return err
    try:
        CobrosService.cancelar(tx)
    except ErrorCobro as ec:
        return jsonify({"mensaje": str(ec)}), 400
    return _respuesta(tx)


# ===========================
# Simular resultado (modo sandbox / simulado)
# ===========================
@cobros_bp.route("/<int:id>/simular", methods=["POST"])
@jwt_required()
@roles_required("Administrador", "Vendedor", "Almacenista", "Contador", 1, 2, 3)
def simular_cobro(id):
    tx, err = _cargar_cobro_con_acceso(id)
    if err:
        return err
    data = request.get_json() or {}
    try:
        CobrosService.simular(tx, data.get("resultado"))
    except ErrorCobro as ec:
        return jsonify({"mensaje": str(ec)}), 400
    return _respuesta(tx)


# ===========================
# Conciliación manual / programada (solo Administrador)
# ===========================
@cobros_bp.route("/conciliar", methods=["POST"])
@jwt_required()
@roles_required("Administrador")
def conciliar_cobros():
    data = request.get_json(silent=True) or {}
    try:
        minutos = int(data["minutos_expiracion"]) if data.get("minutos_expiracion") else None
        horas = int(data.get("horas_facturas_sin_pago") or 24)
    except (ValueError, TypeError):
        return jsonify({"mensaje": "Parámetros numéricos inválidos."}), 400
    resumen = CobrosService.conciliar(minutos_expiracion=minutos, horas_facturas_sin_pago=horas,
                                      id_empresa=data.get("empresa_id") or data.get("id_empresa"))
    return jsonify(resumen), 200
