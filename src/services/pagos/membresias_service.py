"""
Orquestador de cobros de Membresía Empresarial PYMEsoft ($19.900 COP / mes).
Soporta:
  - Link de pago online (Wompi: PSE, Nequi, QR Bancolombia, Tarjetas / Checkout Simulado)
  - Datáfono POS (Bold Smart / Smart Pro / Terminal Simulada)
  - Confirmación directa / Transferencia verificada
  - Webhooks firmados y simulación en modo Sandbox
"""
import secrets
import time
from datetime import datetime, timedelta

from src.models import session
from src.models.empresas import (
    Empresas,
    PRECIO_MEMBRESIA_COP,
    DIAS_MEMBRESIA_CICLO,
    PLAN_MEMBRESIA_DEFAULT,
)
from src.models.metodos_pago import MetodosPago
from src.models.terminales import Terminales
from src.models.pagos_membresia import PagosMembresia
from src.services.pagos import CANALES, obtener_proveedor, wompi, bold
from src.services.pagos.base import (
    ErrorPasarela,
    ResultadoPasarela,
    PENDIENTE,
    APROBADA,
    RECHAZADA,
    ANULADA,
    ERROR,
)
from src.services.pagos.cobros_service import ErrorCobro, ESTADOS_SIMULABLES


def _nueva_referencia_membresia(empresa_id):
    return f"MEMB{empresa_id}-{int(time.time())}-{secrets.token_hex(3).upper()}"


class MembresiasService:

    PRECIO_COP = PRECIO_MEMBRESIA_COP
    PRECIO_CENTAVOS = int(round(PRECIO_MEMBRESIA_COP * 100))
    DIAS_CICLO = DIAS_MEMBRESIA_CICLO
    PLAN_NOMBRE = PLAN_MEMBRESIA_DEFAULT

    @staticmethod
    def obtener_catalogo_plan():
        return {
            "plan": PLAN_MEMBRESIA_DEFAULT,
            "precio_cop": PRECIO_MEMBRESIA_COP,
            "precio_centavos": int(round(PRECIO_MEMBRESIA_COP * 100)),
            "precio_formateado": "$19.900 COP",
            "moneda": "COP",
            "periodicidad": "Mensual (30 días)",
            "dias_vigencia": DIAS_MEMBRESIA_CICLO,
            "pasarelas_soportadas": ["wompi", "bold", "simulado"],
            "medios_pago": [
                "PSE (Débito Bancario)",
                "Nequi / Daviplata",
                "Tarjeta Débito / Crédito (Visa, Mastercard)",
                "QR Bancolombia",
                "Datáfono Bold POS",
            ],
            "beneficios": [
                "Facturación y ventas ilimitadas en Web y App Móvil",
                "Control de inventario y Kardex en tiempo real",
                "Cobros integrados con datáfonos Bold y pasarela Wompi",
                "Gestión multi-usuario por roles (Administrador, Vendedor, Almacenista)",
                "Reportes gerenciales de ventas, clientes e inventario",
            ],
        }

    @staticmethod
    def listar_por_empresa(empresa_id, limit=25):
        return (
            PagosMembresia.get_query()
            .filter(PagosMembresia.id_empresa == int(empresa_id))
            .order_by(PagosMembresia.id.desc())
            .limit(limit)
            .all()
        )

    @staticmethod
    def obtener_estado_empresa(empresa_id):
        empresa = Empresas.get_by_id(int(empresa_id))
        if not empresa:
            raise ErrorCobro("Empresa no encontrada.")

        pagos = MembresiasService.listar_por_empresa(empresa.id)
        pendiente = next((p for p in pagos if p.estado == PENDIENTE), None)
        if pendiente:
            MembresiasService.refrescar(pendiente)

        emp_dict = empresa.to_dict()
        return {
            "empresa": emp_dict,
            "plan": MembresiasService.obtener_catalogo_plan(),
            "membresia": {
                "id_empresa": empresa.id,
                "nombre_empresa": empresa.nombre,
                "plan": emp_dict["plan_membresia"],
                "precio_cop": PRECIO_MEMBRESIA_COP,
                "precio_formateado": "$19.900 COP",
                "moneda": "COP",
                "estado": emp_dict["estado_membresia"],
                "activa": emp_dict["membresia_activa"],
                "dias_restantes": emp_dict["dias_restantes_membresia"],
                "fecha_inicio": emp_dict["fecha_inicio_membresia"],
                "fecha_vencimiento": emp_dict["fecha_vencimiento_membresia"],
                "auto_renovacion": emp_dict["auto_renovacion"],
            },
            "cobro_pendiente": pendiente.to_dict() if pendiente and pendiente.estado == PENDIENTE else None,
            "historial_pagos": [p.to_dict() for p in pagos],
        }

    @staticmethod
    def crear_cobro_membresia(empresa_id, data=None, id_usuario=None, base_url=None):
        data = data or {}
        empresa = Empresas.get_by_id(int(empresa_id))
        if not empresa:
            raise ErrorCobro("La empresa seleccionada no existe.")

        try:
            meses = max(1, min(12, int(data.get("meses") or 1)))
        except (ValueError, TypeError):
            meses = 1

        monto_total = round(PRECIO_MEMBRESIA_COP * meses, 2)
        monto_centavos = int(round(monto_total * 100))

        # Anular cualquier intento previo pendiente para esta empresa
        pendientes_previos = (
            PagosMembresia.get_query()
            .filter(
                PagosMembresia.id_empresa == empresa.id,
                PagosMembresia.estado == PENDIENTE,
            )
            .all()
        )
        for p_ant in pendientes_previos:
            p_ant.estado = ANULADA
            p_ant.mensaje = "Reemplazado automáticamente por un nuevo intento de pago de membresía."
            p_ant.update()

        try:
            from src.utils.migrations import DatabaseMigrations
            DatabaseMigrations.asegurar_esquema_y_datos(empresa_id=empresa.id)
        except Exception:
            pass

        canal_raw = str(data.get("canal") or data.get("modo_cobro") or "link").strip().lower()
        if canal_raw in ("manual", "caja", "transferencia", "efectivo"):
            canal = "manual"
        elif canal_raw in ("datafono", "terminal"):
            canal = "datafono"
        else:
            canal = "link"

        # Opción de registro manual / transferencia directa verificada
        if canal == "manual":
            ref_manual = (data.get("referencia_pago") or "").strip()
            pago = PagosMembresia()
            pago.id_empresa = empresa.id
            pago.id_usuario = id_usuario
            pago.id_terminal = None
            pago.id_metodo_pago = data.get("id_metodo_pago") if str(data.get("id_metodo_pago") or "").isdigit() else 2
            pago.plan = PLAN_MEMBRESIA_DEFAULT
            pago.meses = meses
            pago.canal = "manual"
            pago.proveedor = "transferencia"
            pago.referencia = _nueva_referencia_membresia(empresa.id)
            pago.id_externo = ref_manual or f"MAN-{int(time.time())}"
            pago.monto = monto_total
            pago.monto_centavos = monto_centavos
            pago.moneda = "COP"
            pago.estado = PENDIENTE
            pago.create()

            res = ResultadoPasarela(
                estado=APROBADA,
                id_externo=pago.id_externo,
                mensaje=f"Pago directo de membresía registrado ({ref_manual or 'Verificado'}).",
                monto_centavos=monto_centavos,
                referencia=pago.referencia,
            )
            MembresiasService.aplicar_resultado(pago, res, origen="pago directo")
            return pago, empresa

        terminal = None
        if canal == "datafono":
            id_terminal = data.get("id_terminal")
            terminal = Terminales.get_by_id(int(id_terminal)) if str(id_terminal or "").isdigit() else None
            if not terminal or (terminal.estado or "Activo") != "Activo":
                terminal = (
                    Terminales.get_query()
                    .filter(
                        Terminales.id_empresa == empresa.id,
                        (Terminales.estado == "Activo") | (Terminales.estado == None),
                    )
                    .first()
                )
            if not terminal:
                terminal = (
                    Terminales.get_query()
                    .filter((Terminales.estado == "Activo") | (Terminales.estado == None))
                    .first()
                )
            if not terminal:
                raise ErrorCobro("Selecciona una terminal de pago activa para enviar el cobro de membresía.")
            metodo = MetodosPago.get_by_id(terminal.id_metodo_pago)
        else:
            id_metodo = data.get("id_metodo_pago")
            metodo = MetodosPago.get_by_id(int(id_metodo)) if str(id_metodo or "").isdigit() else None
            if not metodo or (metodo.pasarela or "").lower() not in CANALES["link"]:
                metodo = (
                    MetodosPago.get_query()
                    .filter(
                        MetodosPago.pasarela.in_(["wompi", "simulado"]),
                        (MetodosPago.tipo == "Pasarela") | (MetodosPago.pasarela == "wompi"),
                    )
                    .first()
                    or MetodosPago.get_query()
                    .filter(MetodosPago.pasarela.in_(["wompi", "simulado"]))
                    .first()
                )

        if not metodo:
            raise ErrorCobro("No hay pasarela de pago configurada para procesar la membresía.")

        proveedor_nombre = (metodo.pasarela or "simulado").lower()
        if proveedor_nombre not in CANALES[canal]:
            proveedor_nombre = "simulado"
        proveedor = obtener_proveedor(proveedor_nombre)

        pago = PagosMembresia()
        pago.id_empresa = empresa.id
        pago.id_usuario = id_usuario
        pago.id_terminal = terminal.id if terminal else None
        pago.id_metodo_pago = metodo.id
        pago.plan = PLAN_MEMBRESIA_DEFAULT
        pago.meses = meses
        pago.canal = canal
        pago.proveedor = proveedor_nombre
        pago.referencia = _nueva_referencia_membresia(empresa.id)
        pago.monto = monto_total
        pago.monto_centavos = monto_centavos
        pago.moneda = "COP"
        pago.estado = PENDIENTE
        pago.create()

        contexto = {}
        if base_url:
            contexto["base_url"] = base_url.rstrip("/")
            contexto["redirect_url"] = f"{base_url.rstrip('/')}/api/webhooks/wompi/retorno?ref={pago.referencia}"
        if empresa.email:
            contexto["email_cliente"] = empresa.email
        if empresa.nombre:
            contexto["nombre_cliente"] = empresa.nombre

        try:
            res = proveedor.crear_cobro(pago, metodo, terminal=terminal, factura=pago, contexto=contexto)
            pago.estado = res.estado or PENDIENTE
            pago.id_externo = res.id_externo or pago.id_externo
            pago.url_pago = res.url_pago
            pago.mensaje = (res.mensaje or "")[:255]
            pago.payload = res.payload
        except ErrorPasarela as e:
            pago.estado = ERROR
            pago.mensaje = str(e)[:255]
        except Exception as e:
            pago.estado = ERROR
            pago.mensaje = f"Error inesperado al generar cobro de membresía: {e}"[:255]

        pago.update()
        return pago, empresa

    @staticmethod
    def aplicar_resultado(pago, res, origen=""):
        """Aplica el resultado confirmado por la pasarela y activa/renueva la membresía por 30 días."""
        if res is None or not res.estado:
            return pago

        nuevo = res.estado

        if nuevo == APROBADA:
            if res.referencia and str(res.referencia) != pago.referencia:
                nuevo = ERROR
                res.mensaje = "La referencia reportada por la pasarela no coincide con el cobro de membresía."
            elif res.monto_centavos is not None and int(res.monto_centavos) != int(pago.monto_centavos):
                nuevo = ERROR
                res.mensaje = (
                    f"Monto no coincide: pasarela ${int(res.monto_centavos) / 100:,.2f} vs "
                    f"membresía ${pago.monto_centavos / 100:,.2f}."
                )

        actual = pago.estado
        if actual == nuevo:
            if res.id_externo and not pago.id_externo:
                pago.id_externo = res.id_externo
                pago.update()
            return pago

        if actual == APROBADA and nuevo != ANULADA:
            return pago

        if nuevo == PENDIENTE:
            if res.id_externo and not pago.id_externo:
                pago.id_externo = res.id_externo
                pago.update()
            return pago

        pago.estado = nuevo
        if res.id_externo:
            pago.id_externo = res.id_externo
        pago.mensaje = (res.mensaje or (f"Actualizado por {origen}" if origen else nuevo))[:255]
        if res.payload:
            pago.payload = res.payload

        empresa = Empresas.get_by_id(pago.id_empresa)
        if empresa and nuevo == APROBADA:
            ahora = datetime.now()
            meses = max(1, int(pago.meses or 1))
            dias_extension = DIAS_MEMBRESIA_CICLO * meses

            venc_actual = empresa.fecha_vencimiento_membresia
            if venc_actual and isinstance(venc_actual, datetime) and venc_actual > ahora:
                inicio_periodo = venc_actual
            else:
                inicio_periodo = ahora
                empresa.fecha_inicio_membresia = ahora

            nuevo_vencimiento = inicio_periodo + timedelta(days=dias_extension)
            if not empresa.fecha_inicio_membresia:
                empresa.fecha_inicio_membresia = ahora

            empresa.plan_membresia = pago.plan or PLAN_MEMBRESIA_DEFAULT
            empresa.precio_membresia = PRECIO_MEMBRESIA_COP
            empresa.estado_membresia = "Activa"
            empresa.fecha_vencimiento_membresia = nuevo_vencimiento
            if (empresa.estado or "Activo") != "Activo":
                empresa.estado = "Activo"

            pago.periodo_inicio = inicio_periodo
            pago.periodo_fin = nuevo_vencimiento

        session.commit()
        return pago

    @staticmethod
    def refrescar(pago):
        if not pago or pago.estado != PENDIENTE:
            return pago
        metodo = MetodosPago.get_by_id(pago.id_metodo_pago) if pago.id_metodo_pago else None
        if not metodo:
            return pago
        try:
            proveedor = obtener_proveedor(pago.proveedor)
            res = proveedor.consultar(pago, metodo)
        except Exception as e:
            print(f"[membresias] No se pudo consultar el cobro {pago.referencia}: {e}")
            return pago
        return MembresiasService.aplicar_resultado(pago, res, origen="consulta")

    @staticmethod
    def cancelar(pago):
        if pago.estado != PENDIENTE:
            raise ErrorCobro("Solo se pueden cancelar cobros de membresía pendientes.")
        pago.estado = ANULADA
        pago.mensaje = "Cobro de membresía cancelado por el usuario."
        pago.update()
        return pago

    @staticmethod
    def simular(pago, resultado):
        if pago.estado != PENDIENTE:
            raise ErrorCobro("El cobro de membresía ya no está pendiente.")
        metodo = MetodosPago.get_by_id(pago.id_metodo_pago) if pago.id_metodo_pago else None
        es_sandbox = (
            (pago.proveedor or "").lower() == "simulado"
            or (metodo is not None and (metodo.modo or "sandbox").lower() == "sandbox")
        )
        if not es_sandbox:
            raise ErrorCobro("La simulación de pago solo está permitida en modo sandbox o proveedor simulado.")

        resultado = str(resultado or "").upper().strip()
        if resultado == "APPROVED":
            resultado = APROBADA
        elif resultado in ("DECLINED", "REJECTED"):
            resultado = RECHAZADA
        if resultado not in ESTADOS_SIMULABLES:
            raise ErrorCobro("Resultado inválido. Usa 'APROBADA' o 'RECHAZADA'.")

        res = ResultadoPasarela(
            estado=resultado,
            mensaje="[SIMULADO] Pago de membresía ($19.900 COP) aprobado." if resultado == APROBADA else "[SIMULADO] Pago de membresía rechazado.",
            monto_centavos=pago.monto_centavos,
            referencia=pago.referencia,
        )
        return MembresiasService.aplicar_resultado(pago, res, origen="simulación")
