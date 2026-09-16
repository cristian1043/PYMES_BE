from sqlalchemy import Column, Integer, String, ForeignKey, func
from src.models import Base, session
from src.models.roles import Roles

class Usuarios(Base):
    __tablename__ = "usuarios"

    id = Column(Integer, primary_key=True)
    tipo_documento = Column(String(10), nullable=False)
    documento = Column(String(20), unique=True, nullable=False)
    nombre = Column(String(100), nullable=False)
    apellido = Column(String(100), nullable=False)
    telefono = Column(String(20), nullable=False)
    email = Column(String(100), unique=True, nullable=False)
    username = Column(String(50), unique=True, nullable=True)
    password_hash = Column(String(255), nullable=False)
    id_rol = Column(Integer, ForeignKey("roles.id"), nullable=False)
    estado = Column(String(20), default="Activo", nullable=True)
    banco = Column(String(100), nullable=True)
    tipo_cuenta = Column(String(50), nullable=True)
    numero_cuenta = Column(String(50), nullable=True)
    fecha_nacimiento = Column(String(20), nullable=True)
    lugar_residencia = Column(String(200), nullable=True)
    estado_civil = Column(String(50), nullable=True)
    numero_hijos = Column(Integer, default=0, nullable=True)
    sesion_version = Column(Integer, default=1, nullable=True)
    foto = Column(String, nullable=True)

    def save(self):
        session.add(self)
        session.commit()

    @staticmethod
    def get():
        return session.query(Usuarios).all()

    @staticmethod
    def get_query():
        return session.query(Usuarios)

    @staticmethod
    def get_by_id(id):
        return session.query(Usuarios).filter_by(id=id).first()

    @staticmethod
    def get_by_login(login_val):
        if not login_val:
            return None
        val = str(login_val).strip().lower()
        return session.query(Usuarios).filter(
            (func.lower(Usuarios.email) == val) |
            (func.lower(Usuarios.username) == val) |
            (func.lower(Usuarios.email) == val + "@pymesoft.com") |
            (func.lower(Usuarios.username) == val + "@pymesoft.com")
        ).first()

    def update(self):
        session.commit()

    def delete(self):
        session.delete(self)
        session.commit()

    def to_dict(self):
        return {
            "id": self.id,
            "tipo_documento": self.tipo_documento,
            "documento": self.documento,
            "nombre": self.nombre,
            "apellido": self.apellido,
            "telefono": self.telefono,
            "email": self.email,
            "username": self.username,
            "id_rol": self.id_rol,
            "estado": self.estado or "Activo",
            "banco": self.banco or "",
            "tipo_cuenta": self.tipo_cuenta or "",
            "numero_cuenta": self.numero_cuenta or "",
            "fecha_nacimiento": self.fecha_nacimiento or "",
            "lugar_residencia": self.lugar_residencia or "",
            "estado_civil": self.estado_civil or "",
            "numero_hijos": self.numero_hijos if self.numero_hijos is not None else 0,
            "sesion_version": getattr(self, "sesion_version", 1) or 1,
            "foto": self.foto or ""
        }