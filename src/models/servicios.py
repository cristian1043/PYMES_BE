from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, Text, DateTime, ForeignKey
from src.models import Base, session


class Servicios(Base):
    """
    Catálogo de servicios ofrecidos por cada empresa (ej. mantenimiento, asesoría, citas, estética, taller, etc.).
    """
    __tablename__ = "servicios"

    id = Column(Integer, primary_key=True)
    id_empresa = Column(Integer, ForeignKey("empresas.id"), nullable=False, index=True)
    codigo = Column(String(50), nullable=False)
    nombre = Column(String(200), nullable=False)
    descripcion = Column(Text, nullable=True)
    categoria = Column(String(100), default="General", nullable=True)
    precio = Column(Float, nullable=False, default=0.0)
    duracion_minutos = Column(Integer, nullable=False, default=60)
    imagen = Column(Text(length=16777215), nullable=True)
    condiciones = Column(Text, nullable=True)
    estado = Column(String(20), default="Activo", nullable=False)  # 'Activo', 'Inactivo'
    publicado = Column(Integer, default=1, nullable=False)
    disponible = Column(Integer, default=1, nullable=False)
    requiere_reserva = Column(Integer, default=1, nullable=False)
    created_at = Column(DateTime, default=datetime.now)

    def create(self):
        session.add(self)
        session.commit()

    def update(self):
        session.commit()

    def delete(self):
        session.delete(self)
        session.commit()

    @classmethod
    def get_by_id(cls, id):
        return session.query(cls).filter_by(id=id).first()

    @classmethod
    def get_by_empresa(cls, id_empresa, solo_publicados=False):
        q = session.query(cls).filter_by(id_empresa=id_empresa)
        if solo_publicados:
            q = q.filter(cls.estado == "Activo", cls.publicado == 1)
        return q.order_by(cls.id.desc()).all()

    def to_dict(self):
        return {
            "id": self.id,
            "id_empresa": self.id_empresa,
            "codigo": self.codigo,
            "nombre": self.nombre,
            "descripcion": self.descripcion or "",
            "categoria": self.categoria or "General",
            "precio": float(self.precio or 0.0),
            "duracion_minutos": int(self.duracion_minutos or 60),
            "duracion_estimada_min": int(self.duracion_minutos or 60),
            "modalidad": "Presencial",
            "imagen": self.imagen or "",
            "imagen_url": self.imagen or "",
            "condiciones": self.condiciones or "",
            "estado": self.estado or "Activo",
            "publicado": bool(self.publicado),
            "publicado_portal": bool(self.publicado),
            "disponible": bool(self.disponible) and (self.estado == "Activo"),
            "requiere_reserva": bool(self.requiere_reserva),
            "created_at": self.created_at.strftime("%Y-%m-%d %H:%M:%S") if self.created_at else None,
        }

    def to_public_dict(self, mostrar_precios=True):
        data = {
            "id": self.id,
            "id_empresa": self.id_empresa,
            "codigo": self.codigo,
            "nombre": self.nombre,
            "descripcion": self.descripcion or "",
            "categoria": self.categoria or "General",
            "precio": float(self.precio or 0.0) if mostrar_precios else None,
            "duracion_minutos": int(self.duracion_minutos or 60),
            "duracion_estimada_min": int(self.duracion_minutos or 60),
            "modalidad": "Presencial",
            "imagen": self.imagen or "",
            "imagen_url": self.imagen or "",
            "condiciones": self.condiciones or "",
            "disponible": bool(self.disponible) and (self.estado == "Activo"),
            "requiere_reserva": bool(self.requiere_reserva),
        }
        return data
