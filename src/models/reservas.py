from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, Text, DateTime, ForeignKey
from src.models import Base, session


class Reservas(Base):
    """
    Reservas y agendamiento de servicios solicitados por clientes en el Portal de Clientes.
    Incluye control de solapamiento de horarios por empresa/servicio/profesional.
    """
    __tablename__ = "reservas"

    ESTADOS_VALIDOS = (
        "Pendiente",
        "Confirmada",
        "En curso",
        "Completada",
        "Cancelada",
        "Reprogramada",
    )

    id = Column(Integer, primary_key=True)
    numero = Column(String(50), nullable=False, index=True)
    id_empresa = Column(Integer, ForeignKey("empresas.id"), nullable=False, index=True)
    id_servicio = Column(Integer, ForeignKey("servicios.id"), nullable=False, index=True)
    id_cuenta_cliente = Column(Integer, ForeignKey("cuentas_clientes.id"), nullable=True, index=True)
    id_cliente = Column(Integer, ForeignKey("clientes.id"), nullable=False, index=True)

    nombre_servicio_historico = Column(String(200), nullable=False)
    precio_historico = Column(Float, nullable=False, default=0.0)
    duracion_minutos = Column(Integer, nullable=False, default=60)

    fecha_reserva = Column(String(15), nullable=False, index=True)  # YYYY-MM-DD
    hora_inicio = Column(String(10), nullable=False)                # HH:MM
    hora_fin = Column(String(10), nullable=False)                   # HH:MM
    profesional = Column(String(120), default="General", nullable=True)

    estado = Column(String(30), default="Pendiente", nullable=False, index=True)
    notas_cliente = Column(Text, nullable=True)
    notas_empresa = Column(Text, nullable=True)

    created_at = Column(DateTime, default=datetime.now, nullable=False)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now, nullable=False)

    def create(self):
        session.add(self)
        session.commit()

    def update(self):
        self.updated_at = datetime.now()
        session.commit()

    @classmethod
    def get_by_id(cls, id):
        return session.query(cls).filter_by(id=id).first()

    def to_dict(self):
        from src.models.clientes import Clientes
        cliente_nombre = "Cliente Portal"
        cliente_telefono = ""
        cliente_email = ""
        try:
            cli = Clientes.get_by_id(self.id_cliente)
            if cli:
                cliente_nombre = cli.nombre
                cliente_telefono = cli.telefono or ""
                cliente_email = cli.email or ""
        except Exception:
            pass

        fmt = "%Y-%m-%d %H:%M:%S"
        return {
            "id": self.id,
            "numero": self.numero,
            "id_empresa": self.id_empresa,
            "id_servicio": self.id_servicio,
            "id_cuenta_cliente": self.id_cuenta_cliente,
            "id_cliente": self.id_cliente,
            "cliente_nombre": cliente_nombre,
            "nombre_cliente": cliente_nombre,
            "cliente_telefono": cliente_telefono,
            "telefono_cliente": cliente_telefono,
            "cliente_email": cliente_email,
            "email_cliente": cliente_email,
            "nombre_servicio": self.nombre_servicio_historico,
            "servicio_nombre": self.nombre_servicio_historico,
            "modalidad": "Presencial",
            "precio": round(float(self.precio_historico or 0.0), 2),
            "duracion_minutos": int(self.duracion_minutos or 60),
            "fecha_reserva": self.fecha_reserva,
            "hora_inicio": self.hora_inicio,
            "hora_fin": self.hora_fin,
            "profesional": self.profesional or "General",
            "estado": self.estado,
            "notas_cliente": self.notas_cliente or "",
            "notas_empresa": self.notas_empresa or "",
            "created_at": self.created_at.strftime(fmt) if self.created_at else None,
            "updated_at": self.updated_at.strftime(fmt) if self.updated_at else None,
        }
