from datetime import datetime, timedelta
from sqlalchemy import Column, Integer, String, Float, DateTime
from src.models import Base, session

PRECIO_MEMBRESIA_COP = 19900.0
DIAS_MEMBRESIA_CICLO = 30
PLAN_MEMBRESIA_DEFAULT = "Plan PYME Mensual"


class Empresas(Base):
    __tablename__ = 'empresas'

    id = Column(Integer, primary_key=True)
    nombre = Column(String(100), nullable=False)
    razon_social = Column(String(200), nullable=True)
    nit = Column(String(20), unique=True, nullable=False)
    direccion = Column(String(255), nullable=True)
    telefono = Column(String(20), nullable=True)
    email = Column(String(100), nullable=True)
    estado = Column(String(20), default="Activo", nullable=True)
    created_at = Column(DateTime, default=datetime.now, nullable=True)

    # Campos de Membresía ($19.900 COP / mes)
    plan_membresia = Column(String(60), default=PLAN_MEMBRESIA_DEFAULT, nullable=True)
    precio_membresia = Column(Float, default=PRECIO_MEMBRESIA_COP, nullable=True)
    estado_membresia = Column(String(30), default="Activa", nullable=True)
    fecha_inicio_membresia = Column(DateTime, nullable=True)
    fecha_vencimiento_membresia = Column(DateTime, nullable=True)
    auto_renovacion = Column(Integer, default=1, nullable=True)

    def save(self):
        session.add(self)
        session.commit()

    @staticmethod
    def get():
        return session.query(Empresas).all()

    @staticmethod
    def get_by_id(id):
        return session.query(Empresas).filter_by(id=id).first()

    def update(self):
        session.commit()

    def delete(self):
        session.delete(self)
        session.commit()

    def calcular_estado_membresia(self):
        ahora = datetime.now()
        venc = self.fecha_vencimiento_membresia
        estado_raw = (self.estado_membresia or "Activa").strip()

        if venc and isinstance(venc, datetime):
            if venc < ahora:
                return "Vencida", False, 0
            delta = venc - ahora
            dias = max(0, delta.days + (1 if delta.seconds > 0 else 0))
            if estado_raw.lower() in ("vencida", "suspendida", "inactiva"):
                return "Vencida", False, 0
            return "Activa", True, dias

        if estado_raw.lower() in ("vencida", "pendiente", "suspendida"):
            return estado_raw.capitalize(), False, 0

        return "Activa", True, DIAS_MEMBRESIA_CICLO

    def to_dict(self):
        fmt = "%Y-%m-%d %H:%M:%S"
        estado_memb, memb_activa, dias_restantes = self.calcular_estado_membresia()
        inicio_dt = self.fecha_inicio_membresia
        venc_dt = self.fecha_vencimiento_membresia
        precio = float(self.precio_membresia or PRECIO_MEMBRESIA_COP)

        created_dt = getattr(self, "created_at", None)
        return {
            "id": self.id,
            "nombre": self.nombre,
            "razon_social": getattr(self, "razon_social", None) or self.nombre,
            "nit": self.nit,
            "direccion": self.direccion,
            "telefono": self.telefono,
            "email": self.email,
            "estado": self.estado or "Activo",
            "created_at": created_dt.strftime(fmt) if isinstance(created_dt, datetime) else (str(created_dt) if created_dt else None),
            "plan_membresia": self.plan_membresia or PLAN_MEMBRESIA_DEFAULT,
            "precio_membresia": precio,
            "precio_membresia_cop": precio,
            "moneda_membresia": "COP",
            "estado_membresia": estado_memb,
            "membresia_activa": memb_activa,
            "dias_restantes_membresia": dias_restantes,
            "fecha_inicio_membresia": inicio_dt.strftime(fmt) if isinstance(inicio_dt, datetime) else (str(inicio_dt) if inicio_dt else None),
            "fecha_vencimiento_membresia": venc_dt.strftime(fmt) if isinstance(venc_dt, datetime) else (str(venc_dt) if venc_dt else None),
            "auto_renovacion": bool(self.auto_renovacion if self.auto_renovacion is not None else 1),
        }
