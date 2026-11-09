"""
Cifrado de secretos (llaves de pasarelas de pago).

- Si la variable de entorno PAGOS_ENC_KEY está definida (clave Fernet en base64) y la librería
  `cryptography` está instalada, los secretos se guardan cifrados con el prefijo "enc:".
- En entorno de producción (FLASK_ENV=production o APP_ENV=production), PAGOS_ENC_KEY es obligatoria
  y el sistema falla de forma segura si no está configurada.
- En desarrollo/pruebas locales, si no está definida se emite una advertencia una sola vez.

Generar una clave:  python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
"""
import os

_PREFIJO = "enc:"
_advertido = False


def _es_produccion() -> bool:
    return (
        os.environ.get("FLASK_ENV", "").lower() == "production"
        or os.environ.get("APP_ENV", "").lower() == "production"
    )


def _fernet():
    clave = os.environ.get("PAGOS_ENC_KEY")
    if not clave:
        if _es_produccion():
            raise RuntimeError("PAGOS_ENC_KEY es obligatoria en producción para cifrar secretos de pasarelas.")
        return None
    try:
        from cryptography.fernet import Fernet
        return Fernet(clave.encode() if isinstance(clave, str) else clave)
    except Exception as e:
        if _es_produccion():
            raise RuntimeError(f"Error al inicializar cifrado Fernet en producción: {e}") from e
        print(f"[cifrado] No se pudo inicializar el cifrado de secretos: {e}")
        return None


def cifrar(valor):
    """Cifra un secreto si hay clave configurada. Devuelve None si el valor está vacío."""
    global _advertido
    if valor is None or str(valor).strip() == "":
        return None
    valor = str(valor).strip()
    if valor.startswith(_PREFIJO):
        return valor
    f = _fernet()
    if not f:
        if not _advertido:
            print("[cifrado] ADVERTENCIA: PAGOS_ENC_KEY no configurada en entorno local; las llaves de pasarela se guardan sin cifrar.")
            _advertido = True
        return valor
    return _PREFIJO + f.encrypt(valor.encode()).decode()


def descifrar(valor):
    """Descifra un secreto guardado. Si no está cifrado lo devuelve tal cual."""
    if not valor:
        return None
    valor = str(valor)
    if not valor.startswith(_PREFIJO):
        return valor
    f = _fernet()
    if not f:
        print("[cifrado] ERROR: hay secretos cifrados pero PAGOS_ENC_KEY no está disponible.")
        return None
    try:
        return f.decrypt(valor[len(_PREFIJO):].encode()).decode()
    except Exception as e:
        print(f"[cifrado] ERROR al descifrar secreto: {e}")
        return None
