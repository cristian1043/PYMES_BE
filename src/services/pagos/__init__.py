"""
Integración de cobros con pasarelas y terminales de pago.

- base.py            Utilidades comunes (HTTP sin dependencias externas, errores, firmas).
- wompi.py           Wompi (Bancolombia): link de checkout web (tarjeta, PSE, Nequi), consulta y webhook firmado.
- bold.py            Bold: cobro enviado al datáfono (API Integrations / app-checkout) y webhook firmado.
- simulado.py        Proveedor de pruebas (sin cuentas reales). Solo permitido en modo 'sandbox'.
- cobros_service.py  Orquestador: crea cobros, aplica estados, procesa webhooks y concilia pendientes.
"""
from src.services.pagos import wompi, bold, simulado

PROVEEDORES = {
    "wompi": wompi,
    "bold": bold,
    "simulado": simulado,
}

# Qué canal soporta cada proveedor
CANALES = {
    "datafono": ("bold", "simulado"),
    "link": ("wompi", "simulado"),
}


def obtener_proveedor(nombre):
    prov = PROVEEDORES.get((nombre or "").lower())
    if not prov:
        from src.services.pagos.base import ErrorPasarela
        raise ErrorPasarela(f"La pasarela '{nombre}' no tiene integración disponible.")
    return prov
