"""
Wompi (Colombia) – cobro por link de checkout web (tarjeta, PSE, Nequi, Bancolombia).

Credenciales en MetodosPago (pasarela='wompi'):
  api_key_publica  -> llave pública (pub_test_... / pub_prod_...)
  api_key_privada  -> llave privada (prv_test_... / prv_prod_...)   [consultas]
  integrity_secret -> secreto de integridad                         [firma del checkout]
  webhook_secret   -> secreto de eventos                            [verificación del webhook]
  modo             -> 'sandbox' | 'produccion'

Documentación: https://docs.wompi.co
"""
from urllib.parse import urlencode

from src.services.pagos.base import (
    ErrorPasarela, ResultadoPasarela, http_json, sha256_hex, comparar_seguro, resumen_payload,
    PENDIENTE, APROBADA, RECHAZADA, ANULADA, ERROR,
)

CHECKOUT_URL = "https://checkout.wompi.co/p/"

MAPA_ESTADOS = {
    "APPROVED": APROBADA,
    "DECLINED": RECHAZADA,
    "VOIDED": ANULADA,
    "ERROR": ERROR,
    "PENDING": PENDIENTE,
}


def _api_base(metodo):
    if (metodo.modo or "sandbox").lower() == "produccion":
        return "https://production.wompi.co/v1"
    return "https://sandbox.wompi.co/v1"


def firma_integridad(referencia, monto_centavos, moneda, secreto):
    """SHA256(referencia + monto_en_centavos + moneda + secreto_integridad)."""
    return sha256_hex(f"{referencia}{monto_centavos}{moneda}{secreto}")


def crear_cobro(tx, metodo, terminal=None, factura=None, contexto=None):
    contexto = contexto or {}
    llave_publica = (metodo.api_key_publica or "").strip()
    secreto_integridad = metodo.credencial("integrity_secret")
    if not llave_publica or not secreto_integridad:
        raise ErrorPasarela("Wompi no está configurado: faltan la llave pública y/o el secreto de integridad en el método de pago.")

    moneda = tx.moneda or "COP"
    params = {
        "public-key": llave_publica,
        "currency": moneda,
        "amount-in-cents": str(tx.monto_centavos),
        "reference": tx.referencia,
        "signature:integrity": firma_integridad(tx.referencia, tx.monto_centavos, moneda, secreto_integridad),
    }
    if contexto.get("redirect_url"):
        params["redirect-url"] = contexto["redirect_url"]
    if contexto.get("email_cliente"):
        params["customer-data:email"] = contexto["email_cliente"]
    if contexto.get("nombre_cliente"):
        params["customer-data:full-name"] = contexto["nombre_cliente"]

    url = CHECKOUT_URL + "?" + urlencode(params)
    return ResultadoPasarela(estado=PENDIENTE, url_pago=url,
                             mensaje="Link de pago generado. Esperando que el cliente complete el pago.")


def _resultado_desde_transaccion(t):
    estado = MAPA_ESTADOS.get(str(t.get("status", "")).upper(), PENDIENTE)
    return ResultadoPasarela(
        estado=estado,
        id_externo=t.get("id"),
        mensaje=t.get("status_message") or f"Wompi: {t.get('status')}",
        payload=resumen_payload(t),
        monto_centavos=t.get("amount_in_cents"),
        referencia=t.get("reference"),
    )


def consultar(tx, metodo):
    """Consulta el estado en Wompi. Devuelve ResultadoPasarela o None si no se puede determinar."""
    base = _api_base(metodo)
    llave = metodo.credencial("api_key_privada") or (metodo.api_key_publica or "").strip()
    if not llave:
        return None
    headers = {"Authorization": f"Bearer {llave}"}

    if tx.id_externo:
        status, body = http_json("GET", f"{base}/transactions/{tx.id_externo}", headers=headers)
        if status == 200 and isinstance(body.get("data"), dict):
            return _resultado_desde_transaccion(body["data"])
        return None

    # Sin ID de Wompi todavía: búsqueda por referencia (requiere llave privada). Si la API no lo permite, se ignora.
    if metodo.credencial("api_key_privada"):
        try:
            status, body = http_json("GET", f"{base}/transactions?{urlencode({'reference': tx.referencia})}", headers=headers)
        except ErrorPasarela:
            return None
        data = body.get("data") if status == 200 else None
        if isinstance(data, list) and data:
            # Priorizar una aprobada; si no, la más reciente
            aprobadas = [t for t in data if str(t.get("status", "")).upper() == "APPROVED"]
            t = aprobadas[0] if aprobadas else data[0]
            if t.get("reference") == tx.referencia:
                return _resultado_desde_transaccion(t)
    return None


def _valor_por_ruta(obj, ruta):
    actual = obj
    for parte in ruta.split("."):
        if not isinstance(actual, dict):
            return None
        actual = actual.get(parte)
    return actual


def extraer_referencia_webhook(evento):
    return _valor_por_ruta(evento, "data.transaction.reference")


def verificar_webhook(evento, headers, metodo):
    """
    checksum = SHA256( valores de signature.properties (leídos desde evento.data) + timestamp + secreto_eventos )
    """
    secreto = metodo.credencial("webhook_secret")
    if not secreto:
        return False
    firma = evento.get("signature") or {}
    propiedades = firma.get("properties") or []
    checksum = headers.get("X-Event-Checksum") or firma.get("checksum")
    timestamp = evento.get("timestamp")
    if not propiedades or not checksum or timestamp is None:
        return False
    concatenado = ""
    for ruta in propiedades:
        valor = _valor_por_ruta(evento.get("data") or {}, ruta)
        concatenado += "" if valor is None else str(valor)
    concatenado += f"{timestamp}{secreto}"
    return comparar_seguro(sha256_hex(concatenado), checksum)


def resultado_webhook(evento):
    if evento.get("event") != "transaction.updated":
        return None
    t = _valor_por_ruta(evento, "data.transaction")
    if not isinstance(t, dict):
        return None
    return _resultado_desde_transaccion(t)


def listar_terminales(metodo):
    raise ErrorPasarela("Wompi no maneja datáfonos; úsalo para cobros por link de pago.")
