import hashlib
import hmac
import json
import urllib.error
import urllib.request


class ErrorPasarela(Exception):
    """Error al comunicarse con una pasarela o por configuración incompleta."""


# Estados internos de TransaccionesPago
PENDIENTE = "PENDIENTE"
APROBADA = "APROBADA"
RECHAZADA = "RECHAZADA"
ANULADA = "ANULADA"
ERROR = "ERROR"
EXPIRADA = "EXPIRADA"


class ResultadoPasarela:
    """Resultado normalizado de una operación con la pasarela."""

    def __init__(self, estado=None, id_externo=None, url_pago=None, mensaje=None, payload=None,
                 monto_centavos=None, referencia=None):
        self.estado = estado
        self.id_externo = id_externo
        self.url_pago = url_pago
        self.mensaje = mensaje
        self.payload = payload
        self.monto_centavos = monto_centavos
        self.referencia = referencia


def http_json(metodo, url, headers=None, body=None, timeout=15):
    """Petición HTTP JSON con la librería estándar. Devuelve (status_code, dict)."""
    data = json.dumps(body).encode("utf-8") if body is not None else None
    req = urllib.request.Request(url, data=data, method=metodo)
    req.add_header("Accept", "application/json")
    req.add_header("User-Agent", "PYMESoft/1.0")
    if data is not None:
        req.add_header("Content-Type", "application/json")
    for k, v in (headers or {}).items():
        req.add_header(k, v)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            raw = resp.read().decode("utf-8", errors="replace")
            return resp.status, (json.loads(raw) if raw.strip() else {})
    except urllib.error.HTTPError as e:
        raw = e.read().decode("utf-8", errors="replace")
        try:
            parsed = json.loads(raw) if raw.strip() else {}
        except ValueError:
            parsed = {"raw": raw[:500]}
        return e.code, parsed
    except (urllib.error.URLError, TimeoutError, OSError, ValueError) as e:
        raise ErrorPasarela(f"No se pudo conectar con la pasarela: {e}")


def comparar_seguro(a, b):
    if a is None or b is None:
        return False
    return hmac.compare_digest(str(a).strip().lower(), str(b).strip().lower())


def sha256_hex(texto):
    return hashlib.sha256(texto.encode("utf-8")).hexdigest()


def hmac_sha256_hex(clave, mensaje_bytes):
    return hmac.new((clave or "").encode("utf-8"), mensaje_bytes, hashlib.sha256).hexdigest()


def resumen_payload(obj, max_len=8000):
    try:
        s = json.dumps(obj, ensure_ascii=False, default=str)
    except Exception:
        s = str(obj)
    return s[:max_len]
