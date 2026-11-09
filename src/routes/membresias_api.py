import os
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from src.models import session
from src.models.empresas import Empresas
from src.models.pagos_membresia import PagosMembresia
from src.services.pagos.membresias_service import MembresiasService
from src.services.pagos.cobros_service import ErrorCobro
from src.utils.security import verificar_acceso_empresa, obtener_empresa_id_request

membresias_bp = Blueprint("membresias", __name__)


def _url_publica_base():
    base = os.environ.get("PUBLIC_BASE_URL")
    if base:
        return base.rstrip("/")
    try:
        return request.host_url.rstrip("/")
    except RuntimeError:
        return None


def _resolver_empresa_id(data=None):
    data = data or {}
    emp_id = (
        data.get("id_empresa")
        or data.get("empresa_id")
        or obtener_empresa_id_request()
    )
    if emp_id and str(emp_id).isdigit():
        return int(emp_id)
    return None


@membresias_bp.route("/plan", methods=["GET"])
def get_plan_membresia():
    return jsonify(MembresiasService.obtener_catalogo_plan()), 200


@membresias_bp.route("/estado", methods=["GET"])
@jwt_required()
def get_estado_membresia_activa():
    try:
        empresa_id = _resolver_empresa_id()
        if not empresa_id or not verificar_acceso_empresa(empresa_id, allow_inactivo=True):
            return jsonify({"mensaje": "No tienes acceso a esta empresa."}), 403
        res = MembresiasService.obtener_estado_empresa(empresa_id)
        return jsonify(res), 200
    except ErrorCobro as ec:
        return jsonify({"mensaje": str(ec)}), 404
    except Exception as e:
        session.rollback()
        return jsonify({"mensaje": str(e)}), 400


@membresias_bp.route("/empresa/<int:empresa_id>", methods=["GET"])
@jwt_required()
def get_estado_membresia_por_empresa(empresa_id):
    try:
        if not verificar_acceso_empresa(empresa_id, allow_inactivo=True):
            return jsonify({"mensaje": "No tienes acceso a esta empresa."}), 403
        res = MembresiasService.obtener_estado_empresa(empresa_id)
        return jsonify(res), 200
    except ErrorCobro as ec:
        return jsonify({"mensaje": str(ec)}), 404
    except Exception as e:
        session.rollback()
        return jsonify({"mensaje": str(e)}), 400


@membresias_bp.route("/cobrar", methods=["POST"])
@membresias_bp.route("/empresa/<int:empresa_id>/cobrar", methods=["POST"])
@jwt_required()
def iniciar_cobro_membresia(empresa_id=None):
    try:
        data = request.get_json(silent=True) or {}
        target_empresa_id = empresa_id or _resolver_empresa_id(data)
        if not target_empresa_id or not verificar_acceso_empresa(target_empresa_id, allow_inactivo=True):
            return jsonify({"mensaje": "No tienes permisos para gestionar la membresía de esta empresa."}), 403

        identity = get_jwt_identity()
        id_usuario = int(identity) if identity and str(identity).isdigit() else None

        pago, empresa = MembresiasService.crear_cobro_membresia(
            empresa_id=target_empresa_id,
            data=data,
            id_usuario=id_usuario,
            base_url=_url_publica_base(),
        )
        return jsonify({
            "cobro": pago.to_dict(),
            "empresa": empresa.to_dict() if empresa else None,
            "mensaje": pago.mensaje or "Cobro de membresía iniciado correctamente.",
        }), 201
    except ErrorCobro as ec:
        session.rollback()
        return jsonify({"mensaje": str(ec)}), 400
    except Exception as e:
        session.rollback()
        return jsonify({"mensaje": str(e)}), 400


@membresias_bp.route("/cobros/<int:cobro_id>", methods=["GET"])
@jwt_required()
def consultar_cobro_membresia(cobro_id):
    pago = PagosMembresia.get_by_id(cobro_id)
    if not pago:
        return jsonify({"mensaje": "Transacción de membresía no encontrada."}), 404
    if not verificar_acceso_empresa(pago.id_empresa, allow_inactivo=True):
        return jsonify({"mensaje": "No tienes acceso a esta transacción."}), 403

    MembresiasService.refrescar(pago)
    empresa = Empresas.get_by_id(pago.id_empresa)
    return jsonify({
        "cobro": pago.to_dict(),
        "empresa": empresa.to_dict() if empresa else None,
    }), 200


@membresias_bp.route("/cobros/<int:cobro_id>/simular", methods=["POST"])
@jwt_required()
def simular_cobro_membresia(cobro_id):
    pago = PagosMembresia.get_by_id(cobro_id)
    if not pago:
        return jsonify({"mensaje": "Transacción de membresía no encontrada."}), 404
    if not verificar_acceso_empresa(pago.id_empresa, allow_inactivo=True):
        return jsonify({"mensaje": "No tienes acceso a esta transacción."}), 403

    data = request.get_json(silent=True) or {}
    try:
        MembresiasService.simular(pago, data.get("resultado", "APROBADA"))
    except ErrorCobro as ec:
        return jsonify({"mensaje": str(ec)}), 400

    empresa = Empresas.get_by_id(pago.id_empresa)
    return jsonify({
        "cobro": pago.to_dict(),
        "empresa": empresa.to_dict() if empresa else None,
    }), 200


@membresias_bp.route("/cobros/<int:cobro_id>/cancelar", methods=["POST"])
@jwt_required()
def cancelar_cobro_membresia(cobro_id):
    pago = PagosMembresia.get_by_id(cobro_id)
    if not pago:
        return jsonify({"mensaje": "Transacción de membresía no encontrada."}), 404
    if not verificar_acceso_empresa(pago.id_empresa, allow_inactivo=True):
        return jsonify({"mensaje": "No tienes acceso a esta transacción."}), 403

    try:
        MembresiasService.cancelar(pago)
    except ErrorCobro as ec:
        return jsonify({"mensaje": str(ec)}), 400

    empresa = Empresas.get_by_id(pago.id_empresa)
    return jsonify({
        "cobro": pago.to_dict(),
        "empresa": empresa.to_dict() if empresa else None,
    }), 200
