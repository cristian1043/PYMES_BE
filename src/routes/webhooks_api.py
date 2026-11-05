from html import escape
from flask import Blueprint, request, jsonify, Response
from src.services.pagos.cobros_service import CobrosService

# Endpoints públicos llamados por las pasarelas. NO usan JWT: la autenticidad se verifica con la firma de cada pasarela.
webhooks_bp = Blueprint("webhooks", __name__)


@webhooks_bp.route("/wompi", methods=["POST"])
def webhook_wompi():
    raw = request.get_data(cache=True) or b""
    status, msg = CobrosService.procesar_webhook_wompi(raw, request.headers)
    return jsonify({"mensaje": msg}), status


@webhooks_bp.route("/bold", methods=["POST"])
def webhook_bold():
    raw = request.get_data(cache=True) or b""
    status, msg = CobrosService.procesar_webhook_bold(raw, request.headers)
    return jsonify({"mensaje": msg}), status


@webhooks_bp.route("/wompi/retorno", methods=["GET"])
def retorno_wompi():
    """Página a la que Wompi redirige al cliente al terminar el checkout (?ref=...&id=...)."""
    ref = request.args.get("ref")
    tx = CobrosService.procesar_retorno_wompi(ref, request.args.get("id"))
    if not tx:
        titulo, texto = "Pago no encontrado", "No encontramos este cobro. Comunícate con el comercio."
    elif tx.estado == "APROBADA":
        titulo, texto = "¡Pago aprobado!", "Gracias. El pago fue confirmado; ya puedes cerrar esta ventana."
    elif tx.estado == "PENDIENTE":
        titulo, texto = "Pago en proceso", "Tu pago se está procesando. El comercio recibirá la confirmación automáticamente."
    else:
        titulo, texto = "Pago no completado", f"Estado: {tx.estado}. {tx.mensaje or ''}"
    html = (
        "<!doctype html><html lang='es'><head><meta charset='utf-8'>"
        "<meta name='viewport' content='width=device-width, initial-scale=1'>"
        f"<title>{escape(titulo)}</title>"
        "<style>body{font-family:system-ui,sans-serif;display:flex;align-items:center;justify-content:center;"
        "min-height:100vh;margin:0;background:#f4f6fb;color:#1f2937}.c{background:#fff;padding:32px;border-radius:16px;"
        "box-shadow:0 8px 24px rgba(0,0,0,.08);max-width:420px;text-align:center}</style></head>"
        f"<body><div class='c'><h2>{escape(titulo)}</h2><p>{escape(texto)}</p>"
        f"<small>{escape(ref or '')}</small></div></body></html>"
    )
    return Response(html, mimetype="text/html")


@webhooks_bp.route("/simulado/checkout", methods=["GET", "POST"])
def checkout_simulado():
    """Checkout interactivo de pruebas (PSE / Nequi / QR Bancolombia / Tarjeta) para pagos sin llaves reales."""
    from src.models.transacciones_pago import TransaccionesPago
    from src.models.facturas import Facturas

    ref = request.args.get("ref") or request.form.get("ref")
    tx = TransaccionesPago.get_by_referencia(ref) if ref else None
    if not tx:
        return Response("<h3>Cobro no encontrado</h3>", status=404, mimetype="text/html")

    if request.method == "POST" and tx.estado == "PENDIENTE":
        resultado = request.form.get("resultado", "APROBADA")
        medio = request.form.get("medio", "PSE / Nequi")
        try:
            CobrosService.simular(tx, resultado)
            if medio and tx.mensaje:
                tx.mensaje = f"[SIMULADO - {medio}] {tx.mensaje}"[:255]
                tx.update()
        except Exception:
            pass

    factura = Facturas.get_by_id(tx.id_factura)
    num_fac = getattr(factura, "numero", f"#{tx.id_factura}")
    monto_fmt = f"${tx.monto:,.2f} {tx.moneda or 'COP'}"

    if tx.estado == "APROBADA":
        cuerpo = (
            f"<div style='font-size:48px'>✅</div>"
            f"<h2 style='color:#16a34a;margin:8px 0'>¡Pago Aprobado Exitosamente!</h2>"
            f"<p>La factura <strong>{escape(str(num_fac))}</strong> por <strong>{escape(monto_fmt)}</strong> "
            f"ha quedado marcada como <strong>Pagada</strong> en PYMEsoft.</p>"
            f"<p style='font-size:13px;color:#64748b'>Referencia: <code>{escape(tx.referencia)}</code></p>"
            f"<button onclick='window.close()' style='margin-top:12px;background:#1e3c72;color:#fff;border:none;"
            f"padding:10px 20px;border-radius:8px;font-weight:700;cursor:pointer'>Cerrar ventana</button>"
        )
    elif tx.estado != "PENDIENTE":
        cuerpo = (
            f"<div style='font-size:48px'>❌</div>"
            f"<h2 style='color:#dc2626;margin:8px 0'>Pago {escape(tx.estado)}</h2>"
            f"<p>{escape(tx.mensaje or 'La transacción no fue aprobada.')}</p>"
            f"<p style='font-size:13px;color:#64748b'>Referencia: <code>{escape(tx.referencia)}</code></p>"
        )
    else:
        cuerpo = (
            f"<div style='background:#eff6ff;color:#1d4ed8;padding:6px 12px;border-radius:20px;font-size:12px;"
            f"font-weight:700;display:inline-block;margin-bottom:10px'>🔒 PASARELA WOMPI / BOLD SANDBOX (MODO PRUEBAS)</div>"
            f"<h2 style='margin:4px 0'>Pago de Factura {escape(str(num_fac))}</h2>"
            f"<h1 style='color:#16a34a;margin:8px 0'>{escape(monto_fmt)}</h1>"
            f"<p style='font-size:13px;color:#64748b;margin-bottom:16px'>Ref: <code>{escape(tx.referencia)}</code></p>"
            f"<form method='POST' style='text-align:left'>"
            f"<input type='hidden' name='ref' value='{escape(tx.referencia)}'>"
            f"<label style='font-weight:700;font-size:13px;display:block;margin-bottom:6px'>Selecciona el medio de pago del cliente:</label>"
            f"<select name='medio' style='width:100%;padding:10px;border-radius:8px;border:1px solid #cbd5e1;margin-bottom:16px;font-size:14px'>"
            f"<option value='Nequi / Billetera Digital'>📱 Nequi / Daviplata</option>"
            f"<option value='PSE Transferencia Bancaria'>🏦 PSE - Débito Bancario (Bancolombia, Davivienda, etc.)</option>"
            f"<option value='Tarjeta Débito / Crédito'>💳 Tarjeta Débito / Crédito (Visa / Mastercard)</option>"
            f"<option value='QR Bancolombia'>📲 QR Bancolombia</option>"
            f"</select>"
            f"<div style='display:flex;gap:10px'>"
            f"<button type='submit' name='resultado' value='APROBADA' style='flex:1;background:#16a34a;color:#fff;border:none;"
            f"padding:12px;border-radius:10px;font-weight:700;font-size:14px;cursor:pointer'>✅ Aprobar Pago Ahora</button>"
            f"<button type='submit' name='resultado' value='RECHAZADA' style='flex:1;background:#dc2626;color:#fff;border:none;"
            f"padding:12px;border-radius:10px;font-weight:700;font-size:14px;cursor:pointer'>❌ Simular Rechazo</button>"
            f"</div></form>"
        )

    html = (
        "<!doctype html><html lang='es'><head><meta charset='utf-8'>"
        "<meta name='viewport' content='width=device-width, initial-scale=1'>"
        f"<title>Checkout PYMEsoft - {escape(str(num_fac))}</title>"
        "<style>body{font-family:system-ui,sans-serif;display:flex;align-items:center;justify-content:center;"
        "min-height:100vh;margin:0;background:#0f172a;color:#1e293b}.c{background:#fff;padding:28px;border-radius:16px;"
        "box-shadow:0 12px 32px rgba(0,0,0,.25);max-width:440px;width:90%;text-align:center}</style></head>"
        f"<body><div class='c'>{cuerpo}</div></body></html>"
    )
    return Response(html, mimetype="text/html")
