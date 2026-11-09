from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from src.models import session
from src.models.productos import Productos
from src.models.servicios import Servicios
from src.models.pedidos import Pedidos
from src.models.reservas import Reservas
from src.models.cuentas_clientes import CuentasClientes, VinculacionesClientes
from src.models.clientes import Clientes
from src.models.notificaciones import Notificaciones, SolicitudesCliente
from src.controllers.portal_controller import PortalController
from src.controllers.productos_controller import ProductosController
from src.utils.security import roles_required, tenant_required, obtener_empresa_id_request

portal_admin_bp = Blueprint("portal_admin", __name__)


def _empresa_activa_id() -> int:
    emp_id = obtener_empresa_id_request()
    return int(emp_id) if emp_id else 0


# =========================================================================
# 1. RESUMEN Y CONFIGURACIÓN DEL PORTAL DE LA EMPRESA ACTIVA
# =========================================================================
@portal_admin_bp.route("/resumen", methods=["GET"])
@jwt_required()
@tenant_required(allow_global_admin=True)
@roles_required("Administrador", "Vendedor", "Almacenista", 1, 2, 3)
def get_resumen_portal_admin():
    eid = _empresa_activa_id()
    cfg = PortalController.obtener_config_admin(eid)

    total_prod = session.query(Productos).filter_by(id_empresa=eid, estado="Activo").count()
    prod_publicados = session.query(Productos).filter(
        Productos.id_empresa == eid,
        Productos.estado == "Activo",
        (Productos.publicado_portal == 1) | (Productos.publicado_portal == None)
    ).count()

    total_servicios = session.query(Servicios).filter_by(id_empresa=eid, estado="Activo").count()
    pedidos_pendientes = session.query(Pedidos).filter(
        Pedidos.id_empresa == eid,
        Pedidos.estado.in_(["Pendiente", "Confirmado", "En preparación"])
    ).count()
    total_pedidos = session.query(Pedidos).filter_by(id_empresa=eid).count()

    reservas_pendientes = session.query(Reservas).filter(
        Reservas.id_empresa == eid,
        Reservas.estado.in_(["Pendiente", "Confirmada"])
    ).count()
    total_reservas = session.query(Reservas).filter_by(id_empresa=eid).count()

    clientes_portal = session.query(VinculacionesClientes).filter_by(id_empresa=eid).count()
    solicitudes_abiertas = session.query(SolicitudesCliente).filter(
        SolicitudesCliente.id_empresa == eid,
        SolicitudesCliente.estado.in_(["Abierta", "En revisión"])
    ).count()

    notifs_no_leidas = session.query(Notificaciones).filter_by(
        id_empresa=eid, destinatario_tipo="empresa", leida=0
    ).count()

    pedidos_recientes = session.query(Pedidos).filter_by(id_empresa=eid).order_by(Pedidos.id.desc()).limit(5).all()
    reservas_recientes = session.query(Reservas).filter_by(id_empresa=eid).order_by(Reservas.id.desc()).limit(5).all()

    return jsonify({
        "exito": True,
        "configuracion": cfg.to_dict(),
        "metricas": {
            "total_productos": total_prod,
            "productos_publicados": prod_publicados,
            "total_servicios": total_servicios,
            "pedidos_pendientes": pedidos_pendientes,
            "total_pedidos": total_pedidos,
            "reservas_pendientes": reservas_pendientes,
            "total_reservas": total_reservas,
            "clientes_registrados_portal": clientes_portal,
            "solicitudes_abiertas": solicitudes_abiertas,
            "notificaciones_no_leidas": notifs_no_leidas,
        },
        "pedidos_recientes": [p.to_dict() for p in pedidos_recientes],
        "reservas_recientes": [r.to_dict() for r in reservas_recientes],
    }), 200


@portal_admin_bp.route("/configuracion", methods=["GET"])
@jwt_required()
@tenant_required(allow_global_admin=True)
@roles_required("Administrador", "Vendedor", 1, 2)
def get_configuracion_portal():
    eid = _empresa_activa_id()
    cfg = PortalController.obtener_config_admin(eid)
    return jsonify({"exito": True, "configuracion": cfg.to_dict()}), 200


@portal_admin_bp.route("/configuracion", methods=["PUT"])
@jwt_required()
@tenant_required(allow_global_admin=True)
@roles_required("Administrador", 1)
def update_configuracion_portal():
    eid = _empresa_activa_id()
    data = request.get_json(silent=True) or {}
    try:
        cfg = PortalController.actualizar_config_admin(eid, data)
        return jsonify({
            "exito": True,
            "mensaje": "Configuración del Portal de Clientes actualizada correctamente.",
            "configuracion": cfg.to_dict()
        }), 200
    except ValueError as ve:
        session.rollback()
        return jsonify({"exito": False, "mensaje": str(ve)}), 400


# =========================================================================
# 2. GESTIÓN DE PRODUCTOS PUBLICADOS EN EL PORTAL
# =========================================================================
@portal_admin_bp.route("/productos", methods=["GET"])
@jwt_required()
@tenant_required(allow_global_admin=True)
@roles_required("Administrador", "Vendedor", "Almacenista", 1, 2, 3)
def listar_productos_portal_admin():
    eid = _empresa_activa_id()
    productos = ProductosController.get(empresa_id=eid)
    return jsonify({"exito": True, "productos": [p.to_dict() for p in productos]}), 200


@portal_admin_bp.route("/productos/<int:producto_id>/portal", methods=["PUT", "PATCH"])
@jwt_required()
@tenant_required(allow_global_admin=True)
@roles_required("Administrador", "Vendedor", "Almacenista", 1, 2, 3)
def actualizar_publicacion_producto(producto_id):
    eid = _empresa_activa_id()
    prod = Productos.get_by_id(producto_id)
    if not prod or prod.id_empresa != eid:
        return jsonify({"exito": False, "mensaje": "Producto no encontrado en la empresa activa."}), 404

    data = request.get_json(silent=True) or {}
    try:
        actualizado = ProductosController.update(producto_id, data)
        return jsonify({
            "exito": True,
            "mensaje": f"Configuración de portal actualizada para '{actualizado.nombre}'.",
            "producto": actualizado.to_dict()
        }), 200
    except ValueError as ve:
        session.rollback()
        return jsonify({"exito": False, "mensaje": str(ve)}), 400


# =========================================================================
# 3. GESTIÓN DE SERVICIOS PUBLICADOS
# =========================================================================
@portal_admin_bp.route("/servicios", methods=["GET"])
@jwt_required()
@tenant_required(allow_global_admin=True)
@roles_required("Administrador", "Vendedor", "Almacenista", 1, 2, 3)
def listar_servicios_admin():
    eid = _empresa_activa_id()
    servicios = Servicios.get_by_empresa(eid, solo_publicados=False)
    return jsonify({"exito": True, "servicios": [s.to_dict() for s in servicios]}), 200


@portal_admin_bp.route("/servicios", methods=["POST"])
@jwt_required()
@tenant_required(allow_global_admin=True)
@roles_required("Administrador", "Vendedor", 1, 2)
def crear_servicio_admin():
    eid = _empresa_activa_id()
    data = request.get_json(silent=True) or {}
    try:
        srv = PortalController.crear_servicio(eid, data)
        return jsonify({
            "exito": True,
            "mensaje": "Servicio registrado exitosamente.",
            "servicio": srv.to_dict()
        }), 201
    except ValueError as ve:
        session.rollback()
        return jsonify({"exito": False, "mensaje": str(ve)}), 400


@portal_admin_bp.route("/servicios/<int:servicio_id>", methods=["GET"])
@jwt_required()
@tenant_required(allow_global_admin=True)
def detalle_servicio_admin(servicio_id):
    eid = _empresa_activa_id()
    srv = Servicios.get_by_id(servicio_id)
    if not srv or srv.id_empresa != eid:
        return jsonify({"exito": False, "mensaje": "Servicio no encontrado en esta empresa."}), 404
    return jsonify({"exito": True, "servicio": srv.to_dict()}), 200


@portal_admin_bp.route("/servicios/<int:servicio_id>", methods=["PUT", "PATCH"])
@jwt_required()
@tenant_required(allow_global_admin=True)
@roles_required("Administrador", "Vendedor", 1, 2)
def actualizar_servicio_admin(servicio_id):
    eid = _empresa_activa_id()
    data = request.get_json(silent=True) or {}
    try:
        srv = PortalController.actualizar_servicio(eid, servicio_id, data)
        if not srv:
            return jsonify({"exito": False, "mensaje": "Servicio no encontrado en esta empresa."}), 404
        return jsonify({
            "exito": True,
            "mensaje": "Servicio actualizado correctamente.",
            "servicio": srv.to_dict()
        }), 200
    except ValueError as ve:
        session.rollback()
        return jsonify({"exito": False, "mensaje": str(ve)}), 400


@portal_admin_bp.route("/servicios/<int:servicio_id>", methods=["DELETE"])
@jwt_required()
@tenant_required(allow_global_admin=True)
@roles_required("Administrador", 1)
def eliminar_servicio_admin(servicio_id):
    eid = _empresa_activa_id()
    srv = Servicios.get_by_id(servicio_id)
    if not srv or srv.id_empresa != eid:
        return jsonify({"exito": False, "mensaje": "Servicio no encontrado en esta empresa."}), 404
    srv.estado = "Inactivo"
    srv.publicado = 0
    srv.update()
    return jsonify({"exito": True, "mensaje": "Servicio desactivado correctamente."}), 200


# =========================================================================
# 4. GESTIÓN DE PEDIDOS RECIBIDOS Y ACTUALIZACIÓN DE ESTADOS
# =========================================================================
@portal_admin_bp.route("/pedidos", methods=["GET"])
@jwt_required()
@tenant_required(allow_global_admin=True)
@roles_required("Administrador", "Vendedor", "Almacenista", 1, 2, 3)
def listar_pedidos_admin():
    eid = _empresa_activa_id()
    estado = request.args.get("estado", "").strip()
    q = session.query(Pedidos).filter_by(id_empresa=eid)
    if estado:
        q = q.filter(Pedidos.estado == estado)
    pedidos = q.order_by(Pedidos.id.desc()).all()
    return jsonify({
        "exito": True,
        "pedidos": [p.to_dict(include_detalles=True, include_historial=False) for p in pedidos]
    }), 200


@portal_admin_bp.route("/pedidos/<int:pedido_id>", methods=["GET"])
@jwt_required()
@tenant_required(allow_global_admin=True)
@roles_required("Administrador", "Vendedor", "Almacenista", 1, 2, 3)
def detalle_pedido_admin(pedido_id):
    eid = _empresa_activa_id()
    pedido = Pedidos.get_by_id(pedido_id)
    if not pedido or pedido.id_empresa != eid:
        return jsonify({"exito": False, "mensaje": "Pedido no encontrado en la empresa activa."}), 404
    return jsonify({
        "exito": True,
        "pedido": pedido.to_dict(include_detalles=True, include_historial=True)
    }), 200


@portal_admin_bp.route("/pedidos/<int:pedido_id>/estado", methods=["PUT", "PATCH", "POST"])
@jwt_required()
@tenant_required(allow_global_admin=True)
@roles_required("Administrador", "Vendedor", "Almacenista", 1, 2, 3)
def actualizar_estado_pedido_admin(pedido_id):
    eid = _empresa_activa_id()
    data = request.get_json(silent=True) or {}
    uid = get_jwt_identity()
    actor_id = int(uid) if uid and str(uid).isdigit() else 1

    try:
        pedido = PortalController.actualizar_estado_pedido(
            id_empresa=eid,
            pedido_id=pedido_id,
            nuevo_estado=data.get("estado"),
            comentario=data.get("comentario"),
            actor_tipo="admin",
            actor_id=actor_id,
            estado_pago=data.get("estado_pago"),
            notas_internas=data.get("notas_internas"),
            generar_factura=bool(data.get("generar_factura"))
        )
        if not pedido:
            return jsonify({"exito": False, "mensaje": "Pedido no encontrado en la empresa activa."}), 404
        return jsonify({
            "exito": True,
            "mensaje": f"Pedido {pedido.numero} actualizado correctamente.",
            "pedido": pedido.to_dict(include_detalles=True, include_historial=True)
        }), 200
    except ValueError as ve:
        session.rollback()
        return jsonify({"exito": False, "mensaje": str(ve)}), 400


# =========================================================================
# 5. GESTIÓN DE RESERVAS Y CALENDARIO DE ATENCIÓN
# =========================================================================
@portal_admin_bp.route("/reservas", methods=["GET"])
@jwt_required()
@tenant_required(allow_global_admin=True)
@roles_required("Administrador", "Vendedor", "Almacenista", 1, 2, 3)
def listar_reservas_admin():
    eid = _empresa_activa_id()
    fecha = request.args.get("fecha", "").strip()
    estado = request.args.get("estado", "").strip()
    q = session.query(Reservas).filter_by(id_empresa=eid)
    if fecha:
        q = q.filter(Reservas.fecha_reserva == fecha)
    if estado:
        q = q.filter(Reservas.estado == estado)
    reservas = q.order_by(Reservas.fecha_reserva.desc(), Reservas.hora_inicio.asc()).all()
    return jsonify({"exito": True, "reservas": [r.to_dict() for r in reservas]}), 200


@portal_admin_bp.route("/reservas/<int:reserva_id>", methods=["PUT", "PATCH", "POST"])
@jwt_required()
@tenant_required(allow_global_admin=True)
@roles_required("Administrador", "Vendedor", 1, 2)
def actualizar_reserva_admin(reserva_id):
    eid = _empresa_activa_id()
    data = request.get_json(silent=True) or {}
    try:
        reserva = PortalController.actualizar_reserva(eid, reserva_id, data, actor_tipo="admin")
        if not reserva:
            return jsonify({"exito": False, "mensaje": "Reserva no encontrada en la empresa activa."}), 404
        return jsonify({
            "exito": True,
            "mensaje": f"Reserva {reserva.numero} actualizada correctamente.",
            "reserva": reserva.to_dict()
        }), 200
    except ValueError as ve:
        session.rollback()
        return jsonify({"exito": False, "mensaje": str(ve)}), 400


# =========================================================================
# 6. CLIENTES REGISTRADOS EN EL PORTAL Y VERIFICACIÓN DE VINCULACIÓN
# =========================================================================
@portal_admin_bp.route("/clientes", methods=["GET"])
@jwt_required()
@tenant_required(allow_global_admin=True)
@roles_required("Administrador", "Vendedor", 1, 2)
def listar_clientes_portal_admin():
    eid = _empresa_activa_id()
    vincs = session.query(VinculacionesClientes).filter_by(id_empresa=eid).order_by(VinculacionesClientes.id.desc()).all()
    resultado = []
    for v in vincs:
        cuenta = CuentasClientes.get_by_id(v.id_cuenta_cliente)
        cli = Clientes.get_by_id(v.id_cliente)
        if cuenta:
            d = cuenta.to_dict()
            d["id"] = v.id
            d["id_cuenta_cliente"] = cuenta.id
            d["cuenta_nombre"] = cuenta.nombre_completo
            d["cuenta_documento"] = cuenta.documento
            d["cuenta_email"] = cuenta.email
            d["id_cliente"] = v.id_cliente
            d["verificado"] = (v.estado_verificacion == "Verificado")
            d["estado_vinculacion"] = v.estado_verificacion
            d["vinculacion_id"] = v.id
            d["id_cliente_comercial"] = v.id_cliente
            d["codigo_comercial"] = cli.codigo if cli else f"CLI-{v.id_cliente}"
            d["estado_verificacion"] = v.estado_verificacion
            d["metodo_verificacion"] = v.metodo_verificacion
            d["total_pedidos"] = session.query(Pedidos).filter_by(id_empresa=eid, id_cuenta_cliente=cuenta.id).count()
            d["total_reservas"] = session.query(Reservas).filter_by(id_empresa=eid, id_cuenta_cliente=cuenta.id).count()
            resultado.append(d)
    return jsonify({"exito": True, "clientes": resultado}), 200


@portal_admin_bp.route("/clientes/<int:vinc_id>/verificar", methods=["PUT", "POST"])
@jwt_required()
@tenant_required(allow_global_admin=True)
@roles_required("Administrador", "Vendedor", 1, 2)
def aprobar_vinculacion_cliente_admin(vinc_id):
    from datetime import datetime
    eid = _empresa_activa_id()
    vinc = session.query(VinculacionesClientes).filter_by(id=vinc_id, id_empresa=eid).first()
    if not vinc:
        return jsonify({"exito": False, "mensaje": "Vinculación no encontrada en esta empresa."}), 404
    data = request.get_json(silent=True) or {}
    vinc.estado_verificacion = data.get("estado_verificacion", "Verificado")
    vinc.metodo_verificacion = "aprobado_admin"
    vinc.verified_at = datetime.now()
    vinc.update()
    return jsonify({"exito": True, "mensaje": "Estado de verificación del cliente actualizado.", "vinculacion": vinc.to_dict()}), 200


# =========================================================================
# 7. CONSULTAS / RECLAMOS (PQRS) Y NOTIFICACIONES DE LA EMPRESA
# =========================================================================
@portal_admin_bp.route("/solicitudes", methods=["GET"])
@jwt_required()
@tenant_required(allow_global_admin=True)
@roles_required("Administrador", "Vendedor", 1, 2)
def listar_solicitudes_admin():
    eid = _empresa_activa_id()
    estado = request.args.get("estado", "").strip()
    q = session.query(SolicitudesCliente).filter_by(id_empresa=eid)
    if estado:
        q = q.filter(SolicitudesCliente.estado == estado)
    sols = q.order_by(SolicitudesCliente.id.desc()).all()
    return jsonify({"exito": True, "solicitudes": [s.to_dict() for s in sols]}), 200


@portal_admin_bp.route("/solicitudes/<int:solicitud_id>", methods=["PUT", "PATCH", "POST"])
@jwt_required()
@tenant_required(allow_global_admin=True)
@roles_required("Administrador", "Vendedor", 1, 2)
def responder_solicitud_admin(solicitud_id):
    eid = _empresa_activa_id()
    data = request.get_json(silent=True) or {}
    uid = get_jwt_identity()
    sol = PortalController.responder_solicitud_cliente(eid, solicitud_id, data, usuario_id=uid)
    if not sol:
        return jsonify({"exito": False, "mensaje": "Solicitud no encontrada en la empresa activa."}), 404
    return jsonify({
        "exito": True,
        "mensaje": f"Solicitud {sol.radicado} actualizada correctamente.",
        "solicitud": sol.to_dict()
    }), 200


@portal_admin_bp.route("/notificaciones", methods=["GET"])
@jwt_required()
@tenant_required(allow_global_admin=True)
@roles_required("Administrador", "Vendedor", "Almacenista", 1, 2, 3)
def listar_notificaciones_admin():
    eid = _empresa_activa_id()
    notifs = session.query(Notificaciones).filter_by(
        id_empresa=eid, destinatario_tipo="empresa"
    ).order_by(Notificaciones.id.desc()).limit(60).all()
    return jsonify({
        "exito": True,
        "notificaciones": [n.to_dict() for n in notifs],
        "no_leidas": sum(1 for n in notifs if not n.leida)
    }), 200


@portal_admin_bp.route("/notificaciones/leer", methods=["POST"])
@jwt_required()
@tenant_required(allow_global_admin=True)
def marcar_notificaciones_leidas_admin():
    eid = _empresa_activa_id()
    for n in session.query(Notificaciones).filter_by(
        id_empresa=eid, destinatario_tipo="empresa", leida=0
    ).all():
        n.leida = 1
    session.commit()
    return jsonify({"exito": True, "mensaje": "Notificaciones de la empresa marcadas como leídas."}), 200
