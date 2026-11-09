from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, Text, Float
from src.models import Base, session
from src.models.empresas import PRECIO_MEMBRESIA_COP, PLAN_MEMBRESIA_DEFAULT


class PagosMembresia(Base):
    """
    Registro de transacciones de cobro de la membresía empresarial ($19.900 COP / mes).
    Solo cuando una transacción queda en estado APROBADA (por webhook, consulta a pasarela,
    simulación en sandbox o pago directo verificado), se activa o extiende la vigencia de la empresa.
    """
    __tablename__ = 'pagos_membresia'

    ESTADOS_FINALES = ('APROBADA', 'RECHAZADA', 'ANULADA', 'ERROR', 'EXPIRADA')

    id = Column(Integer, primary_key=True)
    id_empresa = Column(Integer, nullable=False, index=True)
    id_usuario = Column(Integer, nullable=True)
    id_terminal = Column(Integer, nullable=True)
    id_metodo_pago = Column(Integer, nullable=True)
    plan = Column(String(60), default=PLAN_MEMBRESIA_DEFAULT)
    meses = Column(Integer, default=1)
    canal = Column(String(20), nullable=False)          # 'link', 'datafono', 'manual'
    proveedor = Column(String(30), nullable=False)      # 'wompi', 'bold', 'simulado', 'manual'
    referencia = Column(String(100), unique=True, nullable=False, index=True)
    id_externo = Column(String(120), nullable=True)
    monto = Column(Float, nullable=False, default=PRECIO_MEMBRESIA_COP)
    monto_centavos = Column(Integer, nullable=False, default=int(PRECIO_MEMBRESIA_COP * 100))
    moneda = Column(String(5), default='COP')
    estado = Column(String(20), default='PENDIENTE', index=True)
    url_pago = Column(Text, nullable=True)
    mensaje = Column(String(255), nullable=True)
    payload = Column(Text, nullable=True)
    periodo_inicio = Column(DateTime, nullable=True)
    periodo_fin = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)

    @property
    def numero(self):
        return f"Membresía PYMEsoft ({self.referencia})"

    @property
    def id_factura(self):
        return self.id

    @property
    def es_final(self):
        return (self.estado or '') in PagosMembresia.ESTADOS_FINALES

    def create(self):
        session.add(self)
        session.commit()

    def update(self):
        session.commit()

    @staticmethod
    def get_query():
        return session.query(PagosMembresia)

    @staticmethod
    def get_by_id(id):
        return session.query(PagosMembresia).filter_by(id=id).first()

    @staticmethod
    def get_by_referencia(referencia):
        if not referencia:
            return None
        return session.query(PagosMembresia).filter_by(referencia=str(referencia)).first()

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
            "id_empresa": self.id_empresa,
            "id_usuario": self.id_usuario,
            "id_terminal": self.id_terminal,
            "terminal_nombre": terminal_nombre,
            "id_metodo_pago": self.id_metodo_pago,
            "plan": self.plan or PLAN_MEMBRESIA_DEFAULT,
            "meses": self.meses or 1,
            "canal": self.canal,
            "proveedor": self.proveedor,
            "pasarela": self.proveedor,
            "referencia": self.referencia,
            "referencia_interna": self.referencia,
            "id_externo": self.id_externo,
            "monto": float(self.monto or PRECIO_MEMBRESIA_COP),
            "monto_centavos": int(self.monto_centavos or int(PRECIO_MEMBRESIA_COP * 100)),
            "moneda": self.moneda or "COP",
            "estado": self.estado,
            "url_pago": self.url_pago,
            "url_checkout": self.url_pago,
            "mensaje": self.mensaje,
            "simulado": es_simulado,
            "periodo_inicio": self.periodo_inicio.strftime(fmt) if self.periodo_inicio else None,
            "periodo_fin": self.periodo_fin.strftime(fmt) if self.periodo_fin else None,
            "created_at": self.created_at.strftime(fmt) if self.created_at else None,
            "updated_at": self.updated_at.strftime(fmt) if self.updated_at else None,
        }
