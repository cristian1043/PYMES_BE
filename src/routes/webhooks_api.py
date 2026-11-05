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
