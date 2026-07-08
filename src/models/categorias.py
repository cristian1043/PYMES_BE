from sqlalchemy import Column, Integer, String
from src.models import Base, session 

class Categorias(Base):
    __tablename__ = 'categorias'

    id = Column(Integer, primary_key=True)
    nombre = Column(String(255), nullable=False)
