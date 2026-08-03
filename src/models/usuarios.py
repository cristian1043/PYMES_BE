from sqlalchemy import Column, Integer, String, ForeignKey
from src.models import Base, session

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

    def save(self):
        session.add(self)
        session.commit()

    @staticmethod
    def get():
        return session.query(Usuarios).all()

    @staticmethod
    def get_by_id(id):
        return session.query(Usuarios).filter_by(id=id).first()

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
            "password_hash": self.password_hash,
            "id_rol": self.id_rol,
            "estado": self.estado or "Activo"
        }