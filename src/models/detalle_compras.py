from sqlalchemy import Column, Integer, Float, ForeignKey
from src.models import Base, session
from src.models.compras import Compras
from src.models.productos import Productos


class DetalleCompras(Base):
    __tablename__ = 'detalle_compras'

    id = Column(Integer, primary_key=True)
    cantidad = Column(Integer, nullable=False)
    costo_unitario = Column(Float, nullable=False)
    subtotal = Column(Float, nullable=False)

    id_compra = Column(Integer, ForeignKey('compras.id'), nullable=False)
    id_producto = Column(Integer, ForeignKey('productos.id'), nullable=False)
