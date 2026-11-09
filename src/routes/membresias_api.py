import os
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt, get_jwt_identity
from src.models import session
from src.models.empresas import Empresas
from src.models.pagos_membresia import PagosMembresia
from src.models.usuario_empresas import UsuarioEmpresas
from src.services.pagos.membresias_service import MembresiasService
from src.services.pagos.cobros_service import ErrorCobro

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
        or request.args.get("id_empresa")
        or request.args.get("empresa_id")
        or request.headers.get("X-Empresa-ID")
    )
    if emp_id and str(emp_id).isdigit():
        return int(emp_id)
    return 1


def _verificar_acceso_empresa(empresa_id):
    claims = get_jwt() or {}
    id_rol = claims.get("id_rol", 0)
    rol_usuario = claims.get("rol", "")
    identity = get_jwt_identity()

    if id_rol == 1 or rol_usuario == "Administrador":
        return True

    if identity and str(identity).isdigit():
        vinc = UsuarioEmpresas.get_by_usuario_empresa(int(identity), int(empresa_id))
        if vinc and (vinc.estado or "Activo") == "Activo":
            return True
    return False


@membresias_bp.route("/plan", methods=["GET"])
def get_plan_membresia():
    """Catálogo público del plan de membresía PYMEsoft ($19.900 COP / mes)."""
    return jsonify(MembresiasService.obtener_catalogo_plan()), 200


@membresias_bp.route("/estado", methods=["GET"])
@jwt_required()
def get_estado_membresia_activa():
    """Obtiene el estado de la membresía de la empresa activa en sesión."""
    try:
        empresa_id = _resolver_empresa_id()
        if not _verificar_acceso_empresa(empresa_id):
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
    """Obtiene el estado de la membresía e historial de cobros de una empresa específica."""
    try:
        if not _verificar_acceso_empresa(empresa_id):
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
    """
    Inicia un cobro de membresía de $19.900 COP (link Wompi/PSE/Nequi, datáfono Bold o pago directo).
    """
    try:
        data = request.get_json(silent=True) or {}
        target_empresa_id = empresa_id or _resolver_empresa_id(data)
        if not _verificar_acceso_empresa(target_empresa_id):
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
    """Consulta y refresca el estado de un cobro de membresía ($19.900 COP)."""
    pago = PagosMembresia.get_by_id(cobro_id)
    if not pago:
        return jsonify({"mensaje": "Transacción de membresía no encontrada."}), 404
    if not _verificar_acceso_empresa(pago.id_empresa):
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
    """Simula la aprobación o rechazo de un cobro de membresía en modo Sandbox / Simulado."""
    pago = PagosMembresia.get_by_id(cobro_id)
    if not pago:
        return jsonify({"mensaje": "Transacción de membresía no encontrada."}), 404
    if not _verificar_acceso_empresa(pago.id_empresa):
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
    """Cancela un cobro de membresía que aún esté PENDIENTE."""
    pago = PagosMembresia.get_by_id(cobro_id)
    if not pago:
        return jsonify({"mensaje": "Transacción de membresía no encontrada."}), 404
    if not _verificar_acceso_empresa(pago.id_empresa):
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
