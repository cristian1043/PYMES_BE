from sqlalchemy import Column, Integer, String
from src.models import Base, session

class Empresas(Base):
    __tablename__ = 'empresas'

    id = Column(Integer, primary_key=True)
    nombre = Column(String(100), nullable=False)
    nit = Column(String(20), unique=True, nullable=False)
    direccion = Column(String(255), nullable=True)
    telefono = Column(String(20), nullable=True)
    email = Column(String(100), nullable=True)
    estado = Column(String(20), default="Activo", nullable=True)

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

    def to_dict(self):
        return {
            "id": self.id,
            "nombre": self.nombre,
            "nit": self.nit,
            "direccion": self.direccion,
            "telefono": self.telefono,
            "email": self.email,
            "estado": self.estado or "Activo"
        }
