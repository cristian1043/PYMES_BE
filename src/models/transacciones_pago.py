from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, Text, Float
from src.models import Base, session


class TransaccionesPago(Base):
    """
    Registro de cada intento de cobro (fuente única de verdad del pago).
    Solo cuando una transacción queda APROBADA (confirmada por la pasarela) la factura pasa a 'Pagada'.
    """
    __tablename__ = 'transacciones_pago'

    ESTADOS_FINALES = ('APROBADA', 'RECHAZADA', 'ANULADA', 'ERROR', 'EXPIRADA')

    id = Column(Integer, primary_key=True)
    id_factura = Column(Integer, nullable=False, index=True)
    id_empresa = Column(Integer, nullable=True, index=True)
    id_terminal = Column(Integer, nullable=True)
    id_metodo_pago = Column(Integer, nullable=True)
    id_usuario = Column(Integer, nullable=True)
    canal = Column(String(20), nullable=False)          # 'datafono', 'link'
    proveedor = Column(String(30), nullable=False)      # 'bold', 'wompi', 'simulado'
    referencia = Column(String(100), unique=True, nullable=False)  # Referencia interna enviada a la pasarela
    id_externo = Column(String(120), nullable=True)     # ID de la transacción/integración en la pasarela
    monto = Column(Float, nullable=False)               # Pesos
    monto_centavos = Column(Integer, nullable=False)
    moneda = Column(String(5), default='COP')
    estado = Column(String(20), default='PENDIENTE', index=True)  # PENDIENTE, APROBADA, RECHAZADA, ANULADA, ERROR, EXPIRADA
    url_pago = Column(Text, nullable=True)              # Link de checkout (canal 'link')
    mensaje = Column(String(255), nullable=True)
    payload = Column(Text, nullable=True)               # Última respuesta/evento crudo de la pasarela (JSON)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)

    @property
    def es_final(self):
        return (self.estado or '') in TransaccionesPago.ESTADOS_FINALES

    def create(self):
        session.add(self)
        session.commit()

    def update(self):
        session.commit()

    @staticmethod
    def get_query():
        return session.query(TransaccionesPago)

    @staticmethod
    def get_by_id(id):
        return session.query(TransaccionesPago).filter_by(id=id).first()

    @staticmethod
    def get_by_referencia(referencia):
        if not referencia:
            return None
        return session.query(TransaccionesPago).filter_by(referencia=str(referencia)).first()

    def to_dict(self):
        fmt = '%Y-%m-%d %H:%M:%S'
        terminal_nombre = None
        if self.id_terminal:
            try:
                from src.models.terminales import Terminales
                t = Terminales.get_by_id(self.id_terminal)
                if t:
                    terminal_nombre = t.nombre
            except Exception:
                pass
        es_simulado = (
            self.proveedor == 'simulado'
            or str(self.id_externo or '').startswith('SIM-')
            or '/simulado/' in str(self.url_pago or '')
        )
        return {
            "id": self.id,
            "id_factura": self.id_factura,
            "id_empresa": self.id_empresa,
            "id_terminal": self.id_terminal,
            "terminal_nombre": terminal_nombre,
            "id_metodo_pago": self.id_metodo_pago,
            "canal": self.canal,
            "proveedor": self.proveedor,
            "pasarela": self.proveedor,
            "referencia": self.referencia,
            "referencia_interna": self.referencia,
            "id_externo": self.id_externo,
            "monto": self.monto,
            "monto_centavos": self.monto_centavos,
            "moneda": self.moneda or "COP",
            "estado": self.estado,
            "url_pago": self.url_pago,
            "url_checkout": self.url_pago,
            "mensaje": self.mensaje,
            "simulado": es_simulado,
            "created_at": self.created_at.strftime(fmt) if self.created_at else None,
            "updated_at": self.updated_at.strftime(fmt) if self.updated_at else None
        }
