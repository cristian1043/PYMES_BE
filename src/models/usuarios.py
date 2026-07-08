from sqlalchemy import Column, Integer, String, ForeignKey
from src.models import Base, session
from src.models.roles import Roles

class Usuarios(Base):
    __tablename__ = 'usuarios'

    id = Column(Integer, primary_key=True)
    documento = Column(String(20), unique=True, nullable=False)
    nombre = Column(String(255), nullable=False)
    apellido = Column(String(255), nullable=False)
    telefono = Column(String(20), nullable=False)
    email = Column(String(255), unique=True, nullable=False)
    username = Column(String(100), unique=True, nullable=False)
    password = Column(String(255), nullable=False)
    id_rol = Column(Integer, ForeignKey('roles.id'), nullable=False)
