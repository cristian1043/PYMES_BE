from flask import Blueprint, request, jsonify
from src.models import session
from src.models.categorias import Categorias
from src.models.metodos_pago import MetodosPago
from src.models.servicios import Servicios
from src.controllers.portal_controller import PortalController

portal_publico_bp = Blueprint("portal_publico", __name__)


@portal_publico_bp.route("/empresas", methods=["GET"])
def listar_empresas_portal():
    """Directorio público de empresas activas con portal habilitado."""
    try:
        portales = PortalController.listar_portales_publicos()
        return jsonify({"exito": True, "portales": portales}), 200
    except Exception as e:
        session.rollback()
        return jsonify({"exito": False, "portales": [], "mensaje": str(e)}), 200


@portal_publico_bp.route("/<slug_o_id>", methods=["GET"])
def obtener_inicio_portal(slug_o_id):
    """
    Obtiene toda la información pública de presentación de una empresa:
    configuración visual, contacto, horarios, categorías, productos destacados y servicios.
    """
    empresa, cfg, err, code = PortalController.obtener_portal_publico(slug_o_id)
    if err:
        return jsonify({"exito": False, "mensaje": err}), code

    categorias = Categorias.get(id_empresa=empresa.id, include_global=True)
    productos_destacados = PortalController.obtener_catalogo_publico(
        empresa.id, cfg=cfg, solo_destacados=True
    )
    if not productos_destacados:
        productos_destacados = PortalController.obtener_catalogo_publico(empresa.id, cfg=cfg)[:8]

    servicios = PortalController.obtener_servicios_publicos(empresa.id, cfg=cfg)
    metodos = MetodosPago.get_query().filter(
        (MetodosPago.id_empresa == empresa.id) | (MetodosPago.id_empresa == None),
        (MetodosPago.estado == "Activo") | (MetodosPago.estado == None)
    ).all()

    return jsonify({
        "exito": True,
        "empresa": {
            "id": empresa.id,
            "nombre": cfg.nombre_publico or empresa.nombre,
            "razon_social": getattr(empresa, "razon_social", None) or empresa.nombre,
            "nit": empresa.nit,
            "direccion": cfg.direccion or empresa.direccion,
            "telefono": cfg.telefono_contacto or empresa.telefono,
            "email": cfg.email_contacto or empresa.email,
        },
        "portal": cfg.to_dict(),
        "categorias": [c.to_dict() for c in categorias if (c.estado or "Activo") == "Activo"],
        "productos_destacados": productos_destacados,
        "servicios": servicios,
        "metodos_pago": [
            {"id": m.id, "nombre": m.nombre, "descripcion": m.descripcion, "tipo": m.tipo, "pasarela": m.pasarela, "integrado": m.integrado}
            for m in metodos
        ]
    }), 200


@portal_publico_bp.route("/<slug_o_id>/productos", methods=["GET"])
def listar_productos_publicos(slug_o_id):
    """Catálogo público de productos de la empresa (sin costos ni proveedores)."""
    empresa, cfg, err, code = PortalController.obtener_portal_publico(slug_o_id)
    if err:
        return jsonify({"exito": False, "mensaje": err}), code

    q = request.args.get("q", "").strip()
    id_cat = request.args.get("id_categoria") or request.args.get("categoria")
    solo_dest = str(request.args.get("destacados") or "").lower() in ("true", "1", "si")

    productos = PortalController.obtener_catalogo_publico(
        empresa.id, cfg=cfg, q=q, id_categoria=id_cat, solo_destacados=solo_dest
    )
    categorias = Categorias.get(id_empresa=empresa.id, include_global=True)
    return jsonify({
        "exito": True,
        "productos": productos,
        "total": len(productos),
        "categorias": [c.to_dict() for c in categorias if (c.estado or "Activo") == "Activo"],
    }), 200


@portal_publico_bp.route("/<slug_o_id>/productos/<int:producto_id>", methods=["GET"])
def detalle_producto_publico(slug_o_id, producto_id):
    """Detalle público de un producto validando estrictamente que pertenezca a la empresa del portal."""
    empresa, cfg, err, code = PortalController.obtener_portal_publico(slug_o_id)
    if err:
        return jsonify({"exito": False, "mensaje": err}), code

    prod_dict = PortalController.obtener_producto_publico(empresa.id, producto_id, cfg=cfg)
    if not prod_dict:
        return jsonify({"exito": False, "mensaje": "Producto no encontrado o no disponible en este portal."}), 404

    return jsonify({"exito": True, "producto": prod_dict}), 200


@portal_publico_bp.route("/<slug_o_id>/servicios", methods=["GET"])
def listar_servicios_publicos(slug_o_id):
    """Catálogo público de servicios ofrecidos por la empresa."""
    empresa, cfg, err, code = PortalController.obtener_portal_publico(slug_o_id)
    if err:
        return jsonify({"exito": False, "mensaje": err}), code

    categoria = request.args.get("categoria", "").strip()
    servicios = PortalController.obtener_servicios_publicos(empresa.id, cfg=cfg, categoria=categoria)
    return jsonify({"exito": True, "servicios": servicios, "total": len(servicios)}), 200


@portal_publico_bp.route("/<slug_o_id>/servicios/<int:servicio_id>", methods=["GET"])
def detalle_servicio_publico(slug_o_id, servicio_id):
    empresa, cfg, err, code = PortalController.obtener_portal_publico(slug_o_id)
    if err:
        return jsonify({"exito": False, "mensaje": err}), code

    srv = Servicios.get_by_id(servicio_id)
    if not srv or srv.id_empresa != empresa.id or srv.estado != "Activo" or not srv.publicado:
        return jsonify({"exito": False, "mensaje": "Servicio no encontrado en esta empresa."}), 404

    return jsonify({"exito": True, "servicio": srv.to_public_dict(mostrar_precios=bool(cfg.mostrar_precios))}), 200


@portal_publico_bp.route("/<slug_o_id>/servicios/<int:servicio_id>/horarios", methods=["GET"])
def horarios_disponibles_servicio(slug_o_id, servicio_id):
    """Consulta las franjas horarias disponibles para reservar un servicio en una fecha dada."""
    empresa, cfg, err, code = PortalController.obtener_portal_publico(slug_o_id)
    if err:
        return jsonify({"exito": False, "mensaje": err}), code

    fecha = request.args.get("fecha") or datetime_hoy_str()
    try:
        horarios = PortalController.obtener_horarios_disponibles(empresa.id, servicio_id, fecha)
        return jsonify({"exito": True, "fecha": fecha, "horarios": horarios}), 200
    except ValueError as ve:
        return jsonify({"exito": False, "mensaje": str(ve)}), 400


def datetime_hoy_str():
    from datetime import datetime
    return datetime.now().strftime("%Y-%m-%d")


@portal_publico_bp.route("/<slug_o_id>/carrito/validar", methods=["POST"])
def validar_carrito_publico(slug_o_id):
    """Valida en el servidor precios, stock, pertenencia a la empresa y total del carrito."""
    empresa, cfg, err, code = PortalController.obtener_portal_publico(slug_o_id)
    if err:
        return jsonify({"exito": False, "mensaje": err}), code

    data = request.get_json(silent=True) or {}
    items = data.get("items") or []
    modalidad = data.get("modalidad_entrega", "Domicilio")
    try:
        resumen = PortalController.validar_carrito(empresa.id, items, modalidad_entrega=modalidad)
        items_clean = []
        for it in resumen["items"]:
            copia = {k: v for k, v in it.items() if k != "producto_obj"}
            items_clean.append(copia)
        resumen["items"] = items_clean
        resumen["exito"] = True
        return jsonify(resumen), 200
    except ValueError as ve:
        return jsonify({"exito": False, "mensaje": str(ve)}), 400


@portal_publico_bp.route("/<slug_o_id>/contacto", methods=["POST"])
def enviar_consulta_publica(slug_o_id):
    """Permite enviar una consulta o solicitud de contacto a la empresa."""
    empresa, cfg, err, code = PortalController.obtener_portal_publico(slug_o_id)
    if err:
        return jsonify({"exito": False, "mensaje": err}), code

    data = request.get_json(silent=True) or {}
    try:
        sol = PortalController.crear_solicitud_cliente(empresa.id, data, cuenta=None)
        return jsonify({
            "exito": True,
            "mensaje": f"Tu mensaje ha sido registrado con el radicado {sol.radicado}.",
            "solicitud": sol.to_dict()
        }), 201
    except ValueError as ve:
        session.rollback()
        return jsonify({"exito": False, "mensaje": str(ve)}), 400
