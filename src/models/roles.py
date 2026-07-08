from sqlalchemy import Column, Integer, String
from src.models import Base, session

class Roles(Base):
    __tablename__ = 'roles'

    id = Column(Integer, primary_key=True)
    nombre = Column(String(50), unique=True, nullable=False)
    descripcion = Column(String(255), nullable=True)
