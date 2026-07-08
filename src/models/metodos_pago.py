from sqlalchemy import Column, Integer, String
from src.models import Base, session

class MetodosPago(Base):
    __tablename__ = 'metodos_pago'

    id = Column(Integer, primary_key=True)
    nombre = Column(String(100), unique=True, nullable=False)
    descripcion = Column(String(255), nullable=True)
