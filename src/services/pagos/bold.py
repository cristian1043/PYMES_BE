"""
Bold (Colombia) – cobro enviado directamente al datáfono (Smart / Smart Pro) con API Integrations.

Credenciales en MetodosPago (pasarela='bold'):
  api_key_privada -> llave de identidad (header  Authorization: x-api-key <llave>)
  webhook_secret  -> llave secreta (verificación del header x-bold-signature)
Datos del datáfono en Terminales: terminal_serial, terminal_model, email_usuario.

Documentación: https://developers.bold.co  (API Integrations: /payments/binded-terminals, /payments/app-checkout)
El resultado del cobro llega por webhook (SALE_APPROVED / SALE_REJECTED / VOID_APPROVED), configurado en el panel de Bold.
"""
import base64

from src.services.pagos.base import (
    ErrorPasarela, ResultadoPasarela, http_json, hmac_sha256_hex, comparar_seguro, resumen_payload,
    PENDIENTE, APROBADA, RECHAZADA, ANULADA, ERROR,
)

API_BASE = "https://integrations.api.bold.co"

MAPA_EVENTOS = {
    "SALE_APPROVED": APROBADA,
    "SALE_REJECTED": RECHAZADA,
    "VOID_APPROVED": ANULADA,
}


def _headers(metodo):
    llave = metodo.credencial("api_key_privada")
    if not llave:
        raise ErrorPasarela("Bold no está configurado: falta la llave de identidad en el método de pago.")
    return {"Authorization": f"x-api-key {llave}"}


def _errores(body):
    errs = body.get("errors") if isinstance(body, dict) else None
    if not errs:
        return None
    try:
        return "; ".join(str(e.get("message") or e.get("code") or e) if isinstance(e, dict) else str(e) for e in errs)
    except Exception:
        return str(errs)


def listar_terminales(metodo):
    status, body = http_json("GET", f"{API_BASE}/payments/binded-terminals", headers=_headers(metodo))
    if status != 200:
        raise ErrorPasarela(_errores(body) or f"Bold respondió HTTP {status} al listar datáfonos.")
    terminales = ((body or {}).get("payload") or {}).get("available_terminals") or []
    return [{
        "terminal_serial": t.get("terminal_serial"),
        "terminal_model": t.get("terminal_model"),
        "name": t.get("name"),
        "status": t.get("status"),
    } for t in terminales]


def crear_cobro(tx, metodo, terminal=None, factura=None, contexto=None):
    if terminal is None or not terminal.terminal_serial or not terminal.terminal_model:
        raise ErrorPasarela("La terminal Bold no tiene serial y/o modelo configurado.")
    if not terminal.email_usuario:
        raise ErrorPasarela("La terminal Bold necesita el email del usuario Bold que opera el datáfono.")

    numero = getattr(factura, "numero", None) or f"Factura {tx.id_factura}"
    body = {
        "amount": {
            "currency": tx.moneda or "COP",
            "taxes": [],
            "tip_amount": 0,
            "total_amount": int(round(tx.monto)),
        },
        "payment_method": "POS",
        "terminal_model": terminal.terminal_model,
        "terminal_serial": terminal.terminal_serial,
        "reference": tx.referencia,
        "user_email": terminal.email_usuario,
        "description": f"Pago {numero}"[:100],
    }
    status, resp = http_json("POST", f"{API_BASE}/payments/app-checkout", headers=_headers(metodo), body=body)
    err = _errores(resp)
    if status >= 400 or err:
        return ResultadoPasarela(estado=ERROR, mensaje=(err or f"Bold respondió HTTP {status}")[:250],
                                 payload=resumen_payload(resp))
    integration_id = ((resp or {}).get("payload") or {}).get("integration_id")
    return ResultadoPasarela(estado=PENDIENTE, id_externo=integration_id, payload=resumen_payload(resp),
                             mensaje="Cobro enviado al datáfono. Esperando que el cliente pague.")


def consultar(tx, metodo):
    # Bold confirma el resultado por webhook; no se usa consulta activa.
    return None


def extraer_referencia_webhook(evento):
    data = evento.get("data") or {}
    meta = data.get("metadata") or {}
    return meta.get("reference") or data.get("reference")


def verificar_webhook_raw(raw_body, headers, metodo):
    """
    Bold firma el cuerpo: HMAC-SHA256(llave_secreta, base64(cuerpo)) en hexadecimal, enviado en x-bold-signature.
    Por compatibilidad también se acepta HMAC sobre el cuerpo crudo. En modo sandbox sin llave se usa llave vacía.
    """
    firma = headers.get("x-bold-signature") or headers.get("X-Bold-Signature")
    if not firma:
        return False
    secreto = metodo.credencial("webhook_secret")
    if not secreto:
        if (metodo.modo or "sandbox").lower() != "sandbox":
            return False
        secreto = ""
    candidatos = (
        hmac_sha256_hex(secreto, base64.b64encode(raw_body)),
        hmac_sha256_hex(secreto, raw_body),
    )
    return any(comparar_seguro(c, firma) for c in candidatos)


def resultado_webhook(evento):
    estado = MAPA_EVENTOS.get(str(evento.get("type", "")).upper())
    if not estado:
        return None
    data = evento.get("data") or {}
    total = (data.get("amount") or {}).get("total")
    monto_centavos = int(round(float(total) * 100)) if total is not None else None
    return ResultadoPasarela(
        estado=estado,
        id_externo=data.get("payment_id") or evento.get("subject"),
        mensaje=f"Bold: {evento.get('type')}",
        payload=resumen_payload(evento),
        monto_centavos=monto_centavos,
        referencia=extraer_referencia_webhook(evento),
    )
