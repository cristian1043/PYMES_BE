from sqlalchemy import Column, Integer, String, Float, ForeignKey
from src.models import Base, session
from src.models.categorias import Categorias


class Productos(Base):
    __tablename__ = 'productos'

    id = Column(Integer, primary_key=True)
    codigo = Column(String(50), unique=True, nullable=False)
    nombre = Column(String(255), nullable=False)
    descripcion = Column(String(255), nullable=False)
    unidad_medida = Column(String(3), nullable=False)
    precio = Column(Float, nullable=False)
    stock = Column(Integer, nullable=False)
    id_categoria = Column(Integer, ForeignKey('categorias.id'), nullable=False)
