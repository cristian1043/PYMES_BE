"""
Orquestador de cobros: crea transacciones, aplica estados confirmados por la pasarela,
procesa webhooks y concilia cobros pendientes.

Regla de oro: una factura con método de pago integrado solo pasa a 'Pagada'
cuando la pasarela confirma el pago (webhook verificado, consulta a la API o simulación en sandbox).
"""
import json
import os
import secrets
import time
from datetime import datetime, timedelta

from src.models import session
from src.models.facturas import Facturas
from src.models.metodos_pago import MetodosPago
from src.models.terminales import Terminales
from src.models.transacciones_pago import TransaccionesPago
from src.services.pagos import CANALES, obtener_proveedor, wompi, bold
from src.services.pagos.base import (
    ErrorPasarela, PENDIENTE, APROBADA, RECHAZADA, ANULADA, ERROR, EXPIRADA, resumen_payload,
)

ESTADOS_SIMULABLES = (APROBADA, RECHAZADA)


class ErrorCobro(ValueError):
    """Error de validación de negocio (se responde como HTTP 400)."""


def _minutos_expiracion():
    try:
        return max(1, int(os.environ.get("PAGOS_MINUTOS_EXPIRACION", "30")))
    except ValueError:
        return 30


def _nueva_referencia(factura_id):
    return f"PYM{factura_id}-{int(time.time())}-{secrets.token_hex(3).upper()}"


def _metodo_accesible(metodo, id_empresa):
    return metodo and (metodo.id_empresa is None or int(metodo.id_empresa) == int(id_empresa or 0))


class CobrosService:

    # ------------------------------------------------------------------
    # Consulta
    # ------------------------------------------------------------------
    @staticmethod
    def listar_por_factura(factura_id):
        return (TransaccionesPago.get_query()
                .filter(TransaccionesPago.id_factura == int(factura_id))
                .order_by(TransaccionesPago.id.desc()).all())

    @staticmethod
    def pago_confirmado(factura_id):
        return TransaccionesPago.get_query().filter(
            TransaccionesPago.id_factura == int(factura_id),
            TransaccionesPago.estado == APROBADA
        ).first() is not None

    # ------------------------------------------------------------------
    # Crear cobro
    # ------------------------------------------------------------------
    @staticmethod
    def crear_cobro(factura_id, data, id_usuario=None, base_url=None):
        factura = Facturas.get_by_id(factura_id)
        if not factura:
            raise ErrorCobro("Factura no encontrada.")
        if (factura.estado or "") == "Pagada":
            raise ErrorCobro("La factura ya está pagada.")
        if (factura.estado or "") == "Cancelada":
            raise ErrorCobro("No se puede cobrar una factura cancelada.")

        total = float(factura.total or 0)
        if total <= 0:
            raise ErrorCobro("El total de la factura debe ser mayor a cero para cobrarla.")

        pendiente = TransaccionesPago.get_query().filter(
            TransaccionesPago.id_factura == factura.id,
            TransaccionesPago.estado == PENDIENTE
        ).first()
        if pendiente:
            pendiente.estado = ANULADA
            pendiente.mensaje = "Reemplazado automáticamente por un nuevo intento de cobro."
            pendiente.update()

        try:
            from src.utils.migrations import DatabaseMigrations
            DatabaseMigrations.asegurar_esquema_y_datos(empresa_id=factura.id_empresa or 1)
        except Exception:
            pass

        canal = str(data.get("canal") or "").strip().lower()
        if canal not in CANALES:
            if data.get("id_terminal") or str(data.get("modo_cobro") or "").lower() == "terminal":
                canal = "datafono"
            else:
                canal = "link"

        terminal = None
        if canal == "datafono":
            id_terminal = data.get("id_terminal")
            terminal = Terminales.get_by_id(int(id_terminal)) if str(id_terminal or "").isdigit() else None
            if not terminal or (terminal.estado or "Activo") != "Activo":
                terminal = Terminales.get_query().filter(
                    Terminales.id_empresa == (factura.id_empresa or 1),
                    (Terminales.estado == "Activo") | (Terminales.estado == None)
                ).first()
            if not terminal:
                terminal = Terminales.get_query().filter(
                    (Terminales.estado == "Activo") | (Terminales.estado == None)
                ).first()
            if not terminal:
                raise ErrorCobro("Selecciona una terminal de pago activa.")
            metodo = MetodosPago.get_by_id(terminal.id_metodo_pago)
        else:
            id_metodo = data.get("id_metodo_pago")
            metodo = MetodosPago.get_by_id(int(id_metodo)) if str(id_metodo or "").isdigit() else None
            if not metodo or (metodo.pasarela or "").lower() not in CANALES["link"]:
                metodo = MetodosPago.get_query().filter(
                    MetodosPago.pasarela.in_(["wompi", "simulado"]),
                    (MetodosPago.tipo == "Pasarela") | (MetodosPago.pasarela == "wompi")
                ).first() or MetodosPago.get_query().filter(
                    MetodosPago.pasarela.in_(["wompi", "simulado"])
                ).first()

        if not metodo:
            raise ErrorCobro("El método de pago no está disponible para esta empresa.")
        proveedor_nombre = (metodo.pasarela or "simulado").lower()
        if proveedor_nombre not in CANALES[canal]:
            proveedor_nombre = "simulado"
        proveedor = obtener_proveedor(proveedor_nombre)

        tx = TransaccionesPago()
        tx.id_factura = factura.id
        tx.id_empresa = factura.id_empresa
        tx.id_terminal = terminal.id if terminal else None
        tx.id_metodo_pago = metodo.id
        tx.id_usuario = id_usuario
        tx.canal = canal
        tx.proveedor = proveedor_nombre
        tx.referencia = _nueva_referencia(factura.id)
        tx.monto = round(total, 2)
        tx.monto_centavos = int(round(total * 100))
        tx.moneda = "COP"
        tx.estado = PENDIENTE
        tx.create()

        contexto = {}
        if base_url:
            contexto["base_url"] = base_url.rstrip("/")
            contexto["redirect_url"] = f"{base_url.rstrip('/')}/api/webhooks/wompi/retorno?ref={tx.referencia}"
        try:
            from src.models.clientes import Clientes
            cliente = Clientes.get_by_id(factura.id_cliente)
            if cliente:
                if cliente.email and not str(cliente.email).endswith("@correo.com"):
                    contexto["email_cliente"] = cliente.email
                contexto["nombre_cliente"] = f"{cliente.nombre or ''} {getattr(cliente, 'apellido', '') or ''}".strip()
        except Exception:
            pass

        try:
            res = proveedor.crear_cobro(tx, metodo, terminal=terminal, factura=factura, contexto=contexto)
            tx.estado = res.estado or PENDIENTE
            tx.id_externo = res.id_externo or tx.id_externo
            tx.url_pago = res.url_pago
            tx.mensaje = (res.mensaje or "")[:255]
            tx.payload = res.payload
        except ErrorPasarela as e:
            tx.estado = ERROR
            tx.mensaje = str(e)[:255]
        except Exception as e:  # nunca dejar la transacción colgada en PENDIENTE por un fallo inesperado
            tx.estado = ERROR
            tx.mensaje = f"Error inesperado al crear el cobro: {e}"[:255]
        tx.update()
        return tx, factura

    # ------------------------------------------------------------------
    # Aplicar estado (idempotente)
    # ------------------------------------------------------------------
    @staticmethod
    def aplicar_resultado(tx, res, origen=""):
        """Aplica un ResultadoPasarela a la transacción y, si corresponde, a la factura."""
        if res is None or not res.estado:
            return tx

        nuevo = res.estado

        # Validaciones de integridad antes de aprobar
        if nuevo == APROBADA:
            if res.referencia and str(res.referencia) != tx.referencia:
                nuevo = ERROR
                res.mensaje = "La referencia reportada por la pasarela no coincide con el cobro."
            elif res.monto_centavos is not None and int(res.monto_centavos) != int(tx.monto_centavos):
                nuevo = ERROR
                res.mensaje = (f"Monto no coincide: pasarela {int(res.monto_centavos) / 100:.2f} vs "
                               f"factura {tx.monto_centavos / 100:.2f}. Requiere revisión.")

        actual = tx.estado
        if actual == nuevo:
            # Evento repetido: solo completar datos faltantes
            if res.id_externo and not tx.id_externo:
                tx.id_externo = res.id_externo
                tx.update()
            return tx
        # Un cobro aprobado solo puede pasar a ANULADA (reverso/anulación confirmada por la pasarela)
        if actual == APROBADA and nuevo != ANULADA:
            return tx
        # Una pendiente no retrocede a pendiente; las finales (no aprobadas) pueden pasar a APROBADA
        # si la pasarela confirma tarde (p. ej. expiró localmente pero el cliente sí pagó).
        if nuevo == PENDIENTE:
            if res.id_externo and not tx.id_externo:
                tx.id_externo = res.id_externo
                tx.update()
            return tx

        tx.estado = nuevo
        if res.id_externo:
            tx.id_externo = res.id_externo
        tx.mensaje = (res.mensaje or (f"Actualizado por {origen}" if origen else nuevo))[:255]
        if res.payload:
            tx.payload = res.payload

        factura = Facturas.get_by_id(tx.id_factura)
        if factura:
            if nuevo == APROBADA:
                if (factura.estado or "") == "Cancelada":
                    tx.mensaje = ("Pago APROBADO sobre una factura CANCELADA: revisar y gestionar reembolso "
                                  "o reactivar la factura.")[:255]
                else:
                    factura.estado = "Pagada"
                    factura.pasarela = tx.proveedor
                    factura.referencia_pago = (tx.id_externo or tx.referencia)[:100]
                    factura.id_metodo_pago = tx.id_metodo_pago or factura.id_metodo_pago
            elif nuevo == ANULADA and actual == APROBADA:
                if (factura.estado or "") == "Pagada" and factura.referencia_pago in (tx.id_externo, tx.referencia):
                    factura.estado = "Emitida"
                    factura.referencia_pago = None
        session.commit()
        return tx

    @staticmethod
    def refrescar(tx):
        """Consulta la pasarela si el cobro sigue pendiente (no aplica a todos los proveedores)."""
        if tx.estado != PENDIENTE:
            return tx
        metodo = MetodosPago.get_by_id(tx.id_metodo_pago) if tx.id_metodo_pago else None
        if not metodo:
            return tx
        try:
            proveedor = obtener_proveedor(tx.proveedor)
            res = proveedor.consultar(tx, metodo)
        except ErrorPasarela as e:
            print(f"[cobros] No se pudo consultar el cobro {tx.referencia}: {e}")
            return tx
        except Exception as e:
            print(f"[cobros] Error inesperado consultando el cobro {tx.referencia}: {e}")
            return tx
        return CobrosService.aplicar_resultado(tx, res, origen="consulta")

    @staticmethod
    def cancelar(tx):
        if tx.estado != PENDIENTE:
            raise ErrorCobro("Solo se pueden cancelar cobros pendientes.")
        tx.estado = ANULADA
        if tx.canal == "datafono":
            tx.mensaje = ("Cancelado en el sistema. Si el datáfono aún muestra el cobro, cancélalo también "
                          "en el dispositivo.")
        else:
            tx.mensaje = "Cancelado por el usuario."
        tx.update()
        return tx

    @staticmethod
    def simular(tx, resultado):
        if tx.estado != PENDIENTE:
            raise ErrorCobro("El cobro ya no está pendiente.")
        resultado = str(resultado or "").upper().strip()
        if resultado == "APPROVED":
            resultado = APROBADA
        elif resultado in ("DECLINED", "REJECTED"):
            resultado = RECHAZADA
        if resultado not in ESTADOS_SIMULABLES:
            raise ErrorCobro("Resultado inválido. Usa 'APROBADA' o 'RECHAZADA'.")
        from src.services.pagos.base import ResultadoPasarela
        res = ResultadoPasarela(
            estado=resultado,
            mensaje="[SIMULADO] Pago aprobado." if resultado == APROBADA else "[SIMULADO] Pago rechazado.",
            monto_centavos=tx.monto_centavos,
            referencia=tx.referencia,
        )
        return CobrosService.aplicar_resultado(tx, res, origen="simulación")

    # ------------------------------------------------------------------
    # Webhooks
    # ------------------------------------------------------------------
    @staticmethod
    def procesar_webhook_wompi(raw_body, headers):
        try:
            evento = json.loads(raw_body.decode("utf-8") or "{}")
        except ValueError:
            return 400, "JSON inválido"
        referencia = wompi.extraer_referencia_webhook(evento)
        tx = TransaccionesPago.get_by_referencia(referencia)
        if not tx:
            # Evento de una transacción que no es nuestra: responder 200 para que Wompi no reintente.
            return 200, "Referencia desconocida (ignorado)"
        metodo = MetodosPago.get_by_id(tx.id_metodo_pago)
        if not metodo or not wompi.verificar_webhook(evento, headers, metodo):
            return 401, "Firma inválida"
        CobrosService.aplicar_resultado(tx, wompi.resultado_webhook(evento), origen="webhook Wompi")
        return 200, "OK"

    @staticmethod
    def procesar_webhook_bold(raw_body, headers):
        try:
            evento = json.loads(raw_body.decode("utf-8") or "{}")
        except ValueError:
            return 400, "JSON inválido"
        referencia = bold.extraer_referencia_webhook(evento)
        tx = TransaccionesPago.get_by_referencia(referencia)
        if not tx:
            return 200, "Referencia desconocida (ignorado)"
        metodo = MetodosPago.get_by_id(tx.id_metodo_pago)
        if not metodo or not bold.verificar_webhook_raw(raw_body, headers, metodo):
            return 401, "Firma inválida"
        CobrosService.aplicar_resultado(tx, bold.resultado_webhook(evento), origen="webhook Bold")
        return 200, "OK"

    @staticmethod
    def procesar_retorno_wompi(referencia, id_transaccion):
        """El cliente regresa del checkout de Wompi (?id=...). Se guarda el ID y se consulta el estado real."""
        tx = TransaccionesPago.get_by_referencia(referencia)
        if not tx:
            return None
        if id_transaccion and not tx.id_externo:
            tx.id_externo = str(id_transaccion)[:120]
            tx.update()
        return CobrosService.refrescar(tx)

    # ------------------------------------------------------------------
    # Conciliación (la ejecuta la tarea programada)
    # ------------------------------------------------------------------
    @staticmethod
    def conciliar(minutos_expiracion=None, horas_facturas_sin_pago=24, id_empresa=None):
        minutos = minutos_expiracion or _minutos_expiracion()
        ahora = datetime.now()
        limite = ahora - timedelta(minutes=minutos)

        q = TransaccionesPago.get_query().filter(TransaccionesPago.estado == PENDIENTE)
        if id_empresa:
            q = q.filter(TransaccionesPago.id_empresa == int(id_empresa))
        pendientes = q.all()

        resumen = {"fecha": ahora.strftime('%Y-%m-%d %H:%M:%S'), "minutos_expiracion": minutos,
                   "revisadas": len(pendientes), "aprobadas": [], "rechazadas": [], "expiradas": [],
                   "siguen_pendientes": [], "facturas_emitidas_sin_pago": [], "alertas": []}

        for tx in pendientes:
            CobrosService.refrescar(tx)
            if tx.estado == PENDIENTE and tx.created_at and tx.created_at < limite:
                tx.estado = EXPIRADA
                tx.mensaje = (f"Sin confirmación después de {minutos} min. "
                              + ("Verifica en el panel de Bold si el datáfono registró el pago."
                                 if tx.proveedor == "bold" else "Verifica en el panel de la pasarela."))[:255]
                tx.update()
            item = {"id": tx.id, "id_factura": tx.id_factura, "referencia": tx.referencia,
                    "proveedor": tx.proveedor, "monto": tx.monto, "estado": tx.estado}
            if tx.estado == APROBADA:
                resumen["aprobadas"].append(item)
            elif tx.estado in (RECHAZADA, ERROR, ANULADA):
                resumen["rechazadas"].append(item)
            elif tx.estado == EXPIRADA:
                resumen["expiradas"].append(item)
            else:
                resumen["siguen_pendientes"].append(item)

        # Facturas emitidas hace más de N horas sin pago confirmado
        limite_facturas = ahora - timedelta(hours=horas_facturas_sin_pago)
        qf = Facturas.get_query().filter(Facturas.estado == "Emitida", Facturas.fecha < limite_facturas)
        if id_empresa:
            qf = qf.filter(Facturas.id_empresa == int(id_empresa))
        for f in qf.order_by(Facturas.fecha.asc()).limit(200).all():
            resumen["facturas_emitidas_sin_pago"].append({
                "id": f.id, "numero": f.numero, "fecha": f.fecha.strftime('%Y-%m-%d %H:%M') if f.fecha else None,
                "total": f.total, "id_empresa": f.id_empresa})

        # Alertas: pagos aprobados sobre facturas canceladas o con montos que no cuadran
        qa = TransaccionesPago.get_query().filter(TransaccionesPago.updated_at >= ahora - timedelta(days=7))
        if id_empresa:
            qa = qa.filter(TransaccionesPago.id_empresa == int(id_empresa))
        for tx in qa.all():
            msg = tx.mensaje or ""
            if (tx.estado == APROBADA and "CANCELADA" in msg) or (tx.estado == ERROR and "no coincide" in msg):
                resumen["alertas"].append({"id": tx.id, "id_factura": tx.id_factura,
                                           "referencia": tx.referencia, "mensaje": msg})
        return resumen
