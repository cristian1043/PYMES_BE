from flask import Blueprint, request, jsonify
from src.models import session
from src.models.cuentas_clientes import CuentasClientes, DireccionesClientes
from src.models.pedidos import Pedidos
from src.models.reservas import Reservas
from src.models.notificaciones import Notificaciones, SolicitudesCliente
from src.models.transacciones_pago import TransaccionesPago
from src.controllers.portal_controller import PortalController
from src.controllers.facturas_controller import FacturasController
from src.services.pagos.cobros_service import CobrosService, ErrorCobro
from src.utils.security import cliente_jwt_required, verify_password, hash_password, validar_politica_password

portal_clientes_bp = Blueprint("portal_clientes", __name__)


def _cuenta_actual() -> CuentasClientes:
    return request.environ.get("cuenta_cliente_actual")


# =========================================================================
# 1. AUTENTICACIÓN Y GESTIÓN DE CUENTA DEL CLIENTE EXTERNO
# =========================================================================
@portal_clientes_bp.route("/auth/register", methods=["POST"])
def register_cliente():
    data = request.get_json(silent=True) or {}
    if data.get("slug") and not data.get("id_empresa"):
        emp, _, _, _ = PortalController.obtener_portal_publico(data.get("slug"))
        if emp:
            data["id_empresa"] = emp.id
    try:
        cuenta = PortalController.registrar_cuenta_cliente(data)
        res, code = PortalController.login_cuenta_cliente(
            cuenta.email, data.get("password"), id_empresa=data.get("id_empresa")
        )
        res["mensaje"] = "Cuenta de cliente creada exitosamente."
        return jsonify(res), 201
    except ValueError as ve:
        session.rollback()
        return jsonify({"exito": False, "mensaje": str(ve)}), 400
    except Exception as e:
        session.rollback()
        return jsonify({"exito": False, "mensaje": f"No se pudo completar el registro: {str(e)}"}), 400


@portal_clientes_bp.route("/auth/login", methods=["POST"])
def login_cliente():
    data = request.get_json(silent=True) or {}
    email = data.get("email") or data.get("username")
    password = data.get("password")
    emp_id = data.get("id_empresa")
    if data.get("slug") and not emp_id:
        emp, _, _, _ = PortalController.obtener_portal_publico(data.get("slug"))
        if emp:
            emp_id = emp.id
    res, code = PortalController.login_cuenta_cliente(email, password, id_empresa=emp_id)
    return jsonify(res), code


@portal_clientes_bp.route("/auth/recuperar-solicitar", methods=["POST"])
def recuperar_solicitar_cliente():
    data = request.get_json(silent=True) or {}
    res, code = PortalController.solicitar_recuperacion_cliente(data.get("email") or data.get("identificador"))
    return jsonify(res), code


@portal_clientes_bp.route("/auth/recuperar-confirmar", methods=["POST"])
def recuperar_confirmar_cliente():
    data = request.get_json(silent=True) or {}
    res, code = PortalController.confirmar_recuperacion_cliente(
        token_o_codigo=data.get("token") or data.get("codigo"),
        password_nueva=data.get("password_nueva"),
        email=data.get("email")
    )
    return jsonify(res), code


@portal_clientes_bp.route("/auth/logout-global", methods=["POST"])
@cliente_jwt_required()
def logout_global_cliente():
    cuenta = _cuenta_actual()
    cuenta.sesion_version = (cuenta.sesion_version or 1) + 1
    cuenta.update()
    return jsonify({"exito": True, "mensaje": "Sesión cerrada en todos los dispositivos."}), 200


@portal_clientes_bp.route("/perfil", methods=["GET"])
@cliente_jwt_required()
def obtener_perfil_cliente():
    cuenta = _cuenta_actual()
    direcciones = session.query(DireccionesClientes).filter_by(id_cuenta_cliente=cuenta.id).all()
    data = cuenta.to_dict()
    data["direcciones"] = [d.to_dict() for d in direcciones]
    return jsonify({"exito": True, "cliente": data}), 200


@portal_clientes_bp.route("/perfil", methods=["PUT"])
@cliente_jwt_required()
def actualizar_perfil_cliente():
    cuenta = _cuenta_actual()
    data = request.get_json(silent=True) or {}
    if "nombre" in data and str(data["nombre"]).strip():
        cuenta.nombre = str(data["nombre"]).strip()
    if "apellido" in data:
        cuenta.apellido = str(data["apellido"] or "").strip()
    if "telefono" in data and str(data["telefono"]).strip():
        cuenta.telefono = str(data["telefono"]).strip()
    if "direccion_principal" in data:
        cuenta.direccion_principal = str(data["direccion_principal"] or "").strip()
    if "ciudad" in data:
        cuenta.ciudad = str(data["ciudad"] or "").strip()
    cuenta.update()
    return jsonify({"exito": True, "mensaje": "Perfil actualizado correctamente.", "cliente": cuenta.to_dict()}), 200


@portal_clientes_bp.route("/cambiar-password", methods=["POST"])
@cliente_jwt_required()
def cambiar_password_cliente():
    cuenta = _cuenta_actual()
    data = request.get_json(silent=True) or {}
    pwd_actual = data.get("password_actual")
    pwd_nueva = data.get("password_nueva")
    if not pwd_actual or not pwd_nueva:
        return jsonify({"exito": False, "mensaje": "Debes ingresar tu contraseña actual y la nueva contraseña."}), 400
    if not verify_password(cuenta.password_hash, pwd_actual):
        return jsonify({"exito": False, "mensaje": "La contraseña actual es incorrecta."}), 400
    ok, msg = validar_politica_password(pwd_nueva)
    if not ok:
        return jsonify({"exito": False, "mensaje": msg}), 400
    cuenta.password_hash = hash_password(pwd_nueva)
    cuenta.sesion_version = (cuenta.sesion_version or 1) + 1
    cuenta.update()
    return jsonify({"exito": True, "mensaje": "Contraseña actualizada exitosamente."}), 200


@portal_clientes_bp.route("/direcciones", methods=["GET"])
@cliente_jwt_required()
def listar_direcciones_cliente():
    cuenta = _cuenta_actual()
    dirs = session.query(DireccionesClientes).filter_by(id_cuenta_cliente=cuenta.id).all()
    return jsonify({"exito": True, "direcciones": [d.to_dict() for d in dirs]}), 200


@portal_clientes_bp.route("/direcciones", methods=["POST"])
@cliente_jwt_required()
def crear_direccion_cliente():
    cuenta = _cuenta_actual()
    data = request.get_json(silent=True) or {}
    direccion = str(data.get("direccion") or "").strip()
    if not direccion:
        return jsonify({"exito": False, "mensaje": "La dirección es obligatoria."}), 400
    es_princ = 1 if data.get("es_principal") in (True, 1, "1", "true", "on") else 0
    if es_princ:
        for prev in session.query(DireccionesClientes).filter_by(id_cuenta_cliente=cuenta.id).all():
            prev.es_principal = 0
        cuenta.direccion_principal = direccion
        if data.get("ciudad"):
            cuenta.ciudad = str(data["ciudad"]).strip()
    nueva = DireccionesClientes(
        id_cuenta_cliente=cuenta.id,
        alias=str(data.get("alias") or "Dirección").strip(),
        direccion=direccion,
        ciudad=str(data.get("ciudad") or "").strip(),
        departamento=str(data.get("departamento") or "").strip(),
        referencia=str(data.get("referencia") or "").strip(),
        telefono_contacto=str(data.get("telefono_contacto") or cuenta.telefono or "").strip(),
        es_principal=es_princ
    )
    nueva.save()
    return jsonify({"exito": True, "direccion": nueva.to_dict()}), 201


@portal_clientes_bp.route("/direcciones/<int:dir_id>", methods=["DELETE"])
@cliente_jwt_required()
def eliminar_direccion_cliente(dir_id):
    cuenta = _cuenta_actual()
    d = session.query(DireccionesClientes).filter_by(id=dir_id, id_cuenta_cliente=cuenta.id).first()
    if not d:
        return jsonify({"exito": False, "mensaje": "Dirección no encontrada."}), 404
    d.delete()
    return jsonify({"exito": True, "mensaje": "Dirección eliminada."}), 200


# =========================================================================
# 2. OPERACIONES DEL CLIENTE DENTRO DE UNA EMPRESA ESPECÍFICA (<slug_o_id>)
# =========================================================================
@portal_clientes_bp.route("/<slug_o_id>/vincular-solicitar", methods=["POST"])
@cliente_jwt_required()
def solicitar_vinculacion_ficha(slug_o_id):
    empresa, _, err, code = PortalController.obtener_portal_publico(slug_o_id)
    if err:
        return jsonify({"exito": False, "mensaje": err}), code
    res, st = PortalController.solicitar_otp_vinculacion_ficha(_cuenta_actual(), empresa.id)
    return jsonify(res), st


@portal_clientes_bp.route("/<slug_o_id>/vincular-confirmar", methods=["POST"])
@cliente_jwt_required()
def confirmar_vinculacion_ficha(slug_o_id):
    empresa, _, err, code = PortalController.obtener_portal_publico(slug_o_id)
    if err:
        return jsonify({"exito": False, "mensaje": err}), code
    data = request.get_json(silent=True) or {}
    res, st = PortalController.confirmar_otp_vinculacion_ficha(_cuenta_actual(), empresa.id, data.get("codigo"))
    return jsonify(res), st


@portal_clientes_bp.route("/<slug_o_id>/pedidos", methods=["POST"])
@cliente_jwt_required()
def crear_pedido_cliente(slug_o_id):
    empresa, _, err, code = PortalController.obtener_portal_publico(slug_o_id)
    if err:
        return jsonify({"exito": False, "mensaje": err}), code
    data = request.get_json(silent=True) or {}
    try:
        pedido = PortalController.crear_pedido(_cuenta_actual(), empresa.id, data)
        return jsonify({
            "exito": True,
            "mensaje": f"Pedido {pedido.numero} creado exitosamente.",
            "pedido": pedido.to_dict(include_detalles=True, include_historial=True)
        }), 201
    except ValueError as ve:
        session.rollback()
        return jsonify({"exito": False, "mensaje": str(ve)}), 400
    except Exception as e:
        session.rollback()
        return jsonify({"exito": False, "mensaje": f"Error al procesar el pedido: {str(e)}"}), 400


@portal_clientes_bp.route("/<slug_o_id>/pedidos", methods=["GET"])
@cliente_jwt_required()
def listar_pedidos_cliente(slug_o_id):
    empresa, _, err, code = PortalController.obtener_portal_publico(slug_o_id)
    if err:
        return jsonify({"exito": False, "mensaje": err}), code
    cuenta = _cuenta_actual()
    pedidos = session.query(Pedidos).filter_by(
        id_empresa=empresa.id,
        id_cuenta_cliente=cuenta.id
    ).order_by(Pedidos.id.desc()).all()
    return jsonify({
        "exito": True,
        "pedidos": [p.to_dict(include_detalles=True, include_historial=False) for p in pedidos]
    }), 200


@portal_clientes_bp.route("/<slug_o_id>/pedidos/<int:pedido_id>", methods=["GET"])
@cliente_jwt_required()
def detalle_pedido_cliente(slug_o_id, pedido_id):
    empresa, _, err, code = PortalController.obtener_portal_publico(slug_o_id)
    if err:
        return jsonify({"exito": False, "mensaje": err}), code
    cuenta = _cuenta_actual()
    pedido = Pedidos.get_by_id(pedido_id)
    if not pedido or pedido.id_empresa != empresa.id or pedido.id_cuenta_cliente != cuenta.id:
        return jsonify({"exito": False, "mensaje": "Pedido no encontrado o no pertenece a tu cuenta en esta empresa."}), 404

    cobros = CobrosService.listar_por_pedido(pedido.id)
    data = pedido.to_dict(include_detalles=True, include_historial=True)
    data["cobros"] = [c.to_dict() for c in cobros]
    return jsonify({"exito": True, "pedido": data}), 200


@portal_clientes_bp.route("/<slug_o_id>/pedidos/<int:pedido_id>/cancelar", methods=["POST"])
@cliente_jwt_required()
def cancelar_pedido_cliente(slug_o_id, pedido_id):
    empresa, _, err, code = PortalController.obtener_portal_publico(slug_o_id)
    if err:
        return jsonify({"exito": False, "mensaje": err}), code
    cuenta = _cuenta_actual()
    pedido = Pedidos.get_by_id(pedido_id)
    if not pedido or pedido.id_empresa != empresa.id or pedido.id_cuenta_cliente != cuenta.id:
        return jsonify({"exito": False, "mensaje": "Pedido no encontrado."}), 404

    data = request.get_json(silent=True) or {}
    motivo = data.get("motivo") or "Cancelado por el cliente desde el portal."
    try:
        actualizado = PortalController.actualizar_estado_pedido(
            empresa.id,
            pedido.id,
            nuevo_estado="Cancelado",
            comentario=motivo,
            actor_tipo="cliente",
            actor_id=cuenta.id
        )
        return jsonify({
            "exito": True,
            "mensaje": f"El pedido {actualizado.numero} ha sido cancelado.",
            "pedido": actualizado.to_dict(include_detalles=True, include_historial=True)
        }), 200
    except ValueError as ve:
        return jsonify({"exito": False, "mensaje": str(ve)}), 400


@portal_clientes_bp.route("/<slug_o_id>/pedidos/<int:pedido_id>/cobros", methods=["POST"])
@cliente_jwt_required()
def iniciar_cobro_pedido_cliente(slug_o_id, pedido_id):
    empresa, _, err, code = PortalController.obtener_portal_publico(slug_o_id)
    if err:
        return jsonify({"exito": False, "mensaje": err}), code
    cuenta = _cuenta_actual()
    pedido = Pedidos.get_by_id(pedido_id)
    if not pedido or pedido.id_empresa != empresa.id or pedido.id_cuenta_cliente != cuenta.id:
        return jsonify({"exito": False, "mensaje": "Pedido no encontrado."}), 404

    data = request.get_json(silent=True) or {}
    try:
        tx, ped = CobrosService.crear_cobro_pedido(pedido.id, data=data, base_url=request.host_url.rstrip("/"))
        return jsonify({
            "exito": True,
            "cobro": tx.to_dict(),
            "pedido": ped.to_dict()
        }), 201
    except ErrorCobro as ec:
        return jsonify({"exito": False, "mensaje": str(ec)}), 400


@portal_clientes_bp.route("/<slug_o_id>/pedidos/<int:pedido_id>/cobros/<int:cobro_id>/simular", methods=["POST"])
@cliente_jwt_required()
def simular_cobro_pedido_cliente(slug_o_id, pedido_id, cobro_id):
    empresa, _, err, code = PortalController.obtener_portal_publico(slug_o_id)
    if err:
        return jsonify({"exito": False, "mensaje": err}), code
    cuenta = _cuenta_actual()
    pedido = Pedidos.get_by_id(pedido_id)
    if not pedido or pedido.id_empresa != empresa.id or pedido.id_cuenta_cliente != cuenta.id:
        return jsonify({"exito": False, "mensaje": "Pedido no encontrado."}), 404

    tx = TransaccionesPago.get_by_id(cobro_id)
    if not tx or getattr(tx, "id_pedido", None) != pedido.id:
        return jsonify({"exito": False, "mensaje": "Transacción de pago no encontrada para este pedido."}), 404

    data = request.get_json(silent=True) or {}
    try:
        tx_act = CobrosService.simular(tx, data.get("resultado", "APROBADA"))
        ped_act = Pedidos.get_by_id(pedido.id)
        return jsonify({
            "exito": True,
            "cobro": tx_act.to_dict(),
            "pedido": ped_act.to_dict(include_detalles=True, include_historial=True)
        }), 200
    except ErrorCobro as ec:
        return jsonify({"exito": False, "mensaje": str(ec)}), 400


@portal_clientes_bp.route("/<slug_o_id>/reservas", methods=["POST"])
@cliente_jwt_required()
def crear_reserva_cliente(slug_o_id):
    empresa, _, err, code = PortalController.obtener_portal_publico(slug_o_id)
    if err:
        return jsonify({"exito": False, "mensaje": err}), code
    data = request.get_json(silent=True) or {}
    try:
        reserva = PortalController.crear_reserva(_cuenta_actual(), empresa.id, data)
        return jsonify({
            "exito": True,
            "mensaje": f"Reserva {reserva.numero} registrada exitosamente.",
            "reserva": reserva.to_dict()
        }), 201
    except ValueError as ve:
        session.rollback()
        return jsonify({"exito": False, "mensaje": str(ve)}), 400


@portal_clientes_bp.route("/<slug_o_id>/reservas", methods=["GET"])
@cliente_jwt_required()
def listar_reservas_cliente(slug_o_id):
    empresa, _, err, code = PortalController.obtener_portal_publico(slug_o_id)
    if err:
        return jsonify({"exito": False, "mensaje": err}), code
    cuenta = _cuenta_actual()
    reservas = session.query(Reservas).filter_by(
        id_empresa=empresa.id,
        id_cuenta_cliente=cuenta.id
    ).order_by(Reservas.fecha_reserva.desc(), Reservas.hora_inicio.desc()).all()
    return jsonify({"exito": True, "reservas": [r.to_dict() for r in reservas]}), 200


@portal_clientes_bp.route("/<slug_o_id>/reservas/<int:reserva_id>", methods=["PUT"])
@portal_clientes_bp.route("/<slug_o_id>/reservas/<int:reserva_id>/cancelar", methods=["POST"])
@cliente_jwt_required()
def actualizar_o_cancelar_reserva_cliente(slug_o_id, reserva_id):
    empresa, _, err, code = PortalController.obtener_portal_publico(slug_o_id)
    if err:
        return jsonify({"exito": False, "mensaje": err}), code
    cuenta = _cuenta_actual()
    reserva = Reservas.get_by_id(reserva_id)
    if not reserva or reserva.id_empresa != empresa.id or reserva.id_cuenta_cliente != cuenta.id:
        return jsonify({"exito": False, "mensaje": "Reserva no encontrada o no pertenece a tu cuenta."}), 404

    data = request.get_json(silent=True) or {}
    if request.path.endswith("/cancelar"):
        data["estado"] = "Cancelada"

    try:
        actualizada = PortalController.actualizar_reserva(empresa.id, reserva.id, data, actor_tipo="cliente")
        return jsonify({
            "exito": True,
            "mensaje": f"Reserva {actualizada.numero} actualizada a '{actualizada.estado}'.",
            "reserva": actualizada.to_dict()
        }), 200
    except ValueError as ve:
        session.rollback()
        return jsonify({"exito": False, "mensaje": str(ve)}), 400


@portal_clientes_bp.route("/<slug_o_id>/facturas", methods=["GET"])
@cliente_jwt_required()
def listar_facturas_cliente(slug_o_id):
    empresa, _, err, code = PortalController.obtener_portal_publico(slug_o_id)
    if err:
        return jsonify({"exito": False, "mensaje": err}), code
    facturas = PortalController.obtener_facturas_cliente_en_empresa(_cuenta_actual(), empresa.id)
    return jsonify({"exito": True, "facturas": facturas}), 200


@portal_clientes_bp.route("/<slug_o_id>/facturas/<int:factura_id>", methods=["GET"])
@cliente_jwt_required()
def detalle_factura_cliente(slug_o_id, factura_id):
    empresa, _, err, code = PortalController.obtener_portal_publico(slug_o_id)
    if err:
        return jsonify({"exito": False, "mensaje": err}), code
    facturas_autorizadas = PortalController.obtener_facturas_cliente_en_empresa(_cuenta_actual(), empresa.id)
    ids_aut = {f["id"] for f in facturas_autorizadas}
    if int(factura_id) not in ids_aut:
        return jsonify({"exito": False, "mensaje": "No tienes autorización para consultar esta factura."}), 403

    detalle = FacturasController.get_by_id(factura_id)
    return jsonify({"exito": True, "factura": detalle}), 200


@portal_clientes_bp.route("/<slug_o_id>/solicitudes", methods=["GET"])
@cliente_jwt_required()
def listar_solicitudes_cliente(slug_o_id):
    empresa, _, err, code = PortalController.obtener_portal_publico(slug_o_id)
    if err:
        return jsonify({"exito": False, "mensaje": err}), code
    cuenta = _cuenta_actual()
    sols = session.query(SolicitudesCliente).filter_by(
        id_empresa=empresa.id,
        id_cuenta_cliente=cuenta.id
    ).order_by(SolicitudesCliente.id.desc()).all()
    return jsonify({"exito": True, "solicitudes": [s.to_dict() for s in sols]}), 200


@portal_clientes_bp.route("/<slug_o_id>/solicitudes", methods=["POST"])
@cliente_jwt_required()
def crear_solicitud_autenticada(slug_o_id):
    empresa, _, err, code = PortalController.obtener_portal_publico(slug_o_id)
    if err:
        return jsonify({"exito": False, "mensaje": err}), code
    data = request.get_json(silent=True) or {}
    try:
        sol = PortalController.crear_solicitud_cliente(empresa.id, data, cuenta=_cuenta_actual())
        return jsonify({
            "exito": True,
            "mensaje": f"Solicitud {sol.radicado} enviada a {empresa.nombre}.",
            "solicitud": sol.to_dict()
        }), 201
    except ValueError as ve:
        session.rollback()
        return jsonify({"exito": False, "mensaje": str(ve)}), 400


@portal_clientes_bp.route("/<slug_o_id>/notificaciones", methods=["GET"])
@cliente_jwt_required()
def listar_notificaciones_cliente(slug_o_id):
    empresa, _, err, code = PortalController.obtener_portal_publico(slug_o_id)
    if err:
        return jsonify({"exito": False, "mensaje": err}), code
    cuenta = _cuenta_actual()
    notifs = session.query(Notificaciones).filter_by(
        id_empresa=empresa.id,
        destinatario_tipo="cliente",
        id_cuenta_cliente=cuenta.id
    ).order_by(Notificaciones.id.desc()).limit(50).all()
    return jsonify({
        "exito": True,
        "notificaciones": [n.to_dict() for n in notifs],
        "no_leidas": sum(1 for n in notifs if not n.leida)
    }), 200


@portal_clientes_bp.route("/<slug_o_id>/notificaciones/leer", methods=["POST"])
@cliente_jwt_required()
def marcar_notificaciones_leidas_cliente(slug_o_id):
    empresa, _, err, code = PortalController.obtener_portal_publico(slug_o_id)
    if err:
        return jsonify({"exito": False, "mensaje": err}), code
    cuenta = _cuenta_actual()
    for n in session.query(Notificaciones).filter_by(
        id_empresa=empresa.id, destinatario_tipo="cliente", id_cuenta_cliente=cuenta.id, leida=0
    ).all():
        n.leida = 1
    session.commit()
    return jsonify({"exito": True, "mensaje": "Notificaciones marcadas como leídas."}), 200
