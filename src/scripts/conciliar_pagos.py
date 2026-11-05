"""
Conciliación de cobros con pasarelas (Bold / Wompi / Simulado).

Uso (desde la carpeta PYMES_BE):
    python src/scripts/conciliar_pagos.py [--minutos 30] [--horas 24] [--empresa 1]

- Consulta en la pasarela los cobros PENDIENTES (cuando la pasarela lo permite).
- Marca como EXPIRADA los que llevan más de N minutos sin confirmación.
- Lista facturas 'Emitida' con más de H horas sin pago y alertas (pago aprobado sobre factura cancelada, montos que no cuadran).
Imprime un resumen JSON. Código de salida 0 si todo bien, 2 si hay alertas.
"""
import argparse
import json
import os
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from src.models import Base, engine  # noqa: E402
from src.utils.migrations import DatabaseMigrations  # noqa: E402


def main():
    parser = argparse.ArgumentParser(description="Conciliación de cobros PYMES")
    parser.add_argument("--minutos", type=int, default=None, help="Minutos para expirar cobros pendientes (def. PAGOS_MINUTOS_EXPIRACION o 30)")
    parser.add_argument("--horas", type=int, default=24, help="Horas para reportar facturas emitidas sin pago (def. 24)")
    parser.add_argument("--empresa", type=int, default=None, help="Limitar a una empresa")
    args = parser.parse_args()

    Base.metadata.create_all(bind=engine)
    DatabaseMigrations.ejecutar_migraciones()

    from src.services.pagos.cobros_service import CobrosService
    resumen = CobrosService.conciliar(minutos_expiracion=args.minutos, horas_facturas_sin_pago=args.horas,
                                      id_empresa=args.empresa)
    print(json.dumps(resumen, ensure_ascii=False, indent=2, default=str))
    return 2 if resumen.get("alertas") else 0


if __name__ == "__main__":
    sys.exit(main())
