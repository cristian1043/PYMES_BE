from sqlalchemy import Column, Integer, String
from src.models import Base, session

class Proveedores(Base):
    __tablename__ = 'proveedores'

    id = Column(Integer, primary_key=True)
    nit = Column(String(20), unique=True, nullable=False)
    nombre = Column(String(255), nullable=False)
    contacto = Column(String(255), nullable=False)
    telefono = Column(String(20), nullable=False)
    direccion = Column(String(255), nullable=False)
    email = Column(String(255), unique=True, nullable=False)

