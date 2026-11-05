"""
Proveedor SIMULADO para probar todo el flujo de cobro sin cuentas reales de Bold o Wompi.
Solo se permite con métodos de pago en modo 'sandbox'. El resultado se fija con POST /api/cobros/<id>/simular.
"""
import secrets

from src.services.pagos.base import ErrorPasarela, ResultadoPasarela, PENDIENTE


def _validar_modo(metodo):
    if (metodo.modo or "sandbox").lower() != "sandbox":
        raise ErrorPasarela("La pasarela 'simulado' solo puede usarse en modo sandbox (pruebas).")


def crear_cobro(tx, metodo, terminal=None, factura=None, contexto=None):
    contexto = contexto or {}
    if tx.canal == "datafono":
        msg = f"[SIMULADO] Cobro enviado al datáfono '{getattr(terminal, 'nombre', 'Caja Principal')}'. Usa 'Simular aprobado/rechazado'."
        url_pago = None
    else:
        msg = "[SIMULADO] Link de pago generado (PSE / Nequi / Tarjeta). Usa 'Simular aprobado/rechazado' o abre el Checkout."
        base_url = (contexto.get("base_url") or "http://localhost:5000").rstrip("/")
        url_pago = f"{base_url}/api/webhooks/simulado/checkout?ref={tx.referencia}"
    return ResultadoPasarela(
        estado=PENDIENTE,
        id_externo=f"SIM-{secrets.token_hex(5).upper()}",
        url_pago=url_pago,
        mensaje=msg
    )


def consultar(tx, metodo):
    return None


def listar_terminales(metodo):
    _validar_modo(metodo)
    return [
        {"terminal_serial": "SIM-0001", "terminal_model": "SIMULADO", "name": "Datáfono de pruebas 1", "status": "BINDED"},
        {"terminal_serial": "SIM-0002", "terminal_model": "SIMULADO", "name": "Datáfono de pruebas 2", "status": "BINDED"},
    ]
