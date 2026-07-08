from sqlalchemy import Column, DateTime, Integer, String
from src.models import Base, session
from datetime import date, datetime

class Clientes(Base):
    __tablename__ = 'clientes'
 
    id = Column(Integer, primary_key=True)
    documento = Column(String(50), unique=True, nullable=False)
    nombre = Column(String(255), nullable=False)
    direccion = Column(String(255), nullable=False)
    telefono = Column(String(20), nullable=False)
    email = Column(String(255), unique=True, nullable=False)
    created_at = Column(DateTime, default=date.today)
