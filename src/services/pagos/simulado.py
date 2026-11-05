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
    _validar_modo(metodo)
    if tx.canal == "datafono":
        msg = f"[SIMULADO] Cobro enviado al datáfono de pruebas '{getattr(terminal, 'nombre', '')}'. Usa 'Simular aprobado/rechazado'."
    else:
        msg = "[SIMULADO] Link de pago de pruebas generado. Usa 'Simular aprobado/rechazado'."
    return ResultadoPasarela(estado=PENDIENTE, id_externo=f"SIM-{secrets.token_hex(5).upper()}", mensaje=msg)


def consultar(tx, metodo):
    return None


def listar_terminales(metodo):
    _validar_modo(metodo)
    return [
        {"terminal_serial": "SIM-0001", "terminal_model": "SIMULADO", "name": "Datáfono de pruebas 1", "status": "BINDED"},
        {"terminal_serial": "SIM-0002", "terminal_model": "SIMULADO", "name": "Datáfono de pruebas 2", "status": "BINDED"},
    ]
