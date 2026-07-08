from sqlalchemy import Column, Integer, Float, ForeignKey
from src.models import Base, session
from src.models.facturas import Facturas
from src.models.productos import Productos


class DetalleFacturas(Base):
    __tablename__ = 'detalle_facturas'

    id = Column(Integer, primary_key=True)
    cantidad = Column(Integer, nullable=False)
    precio_unitario = Column(Float, nullable=False)
    subtotal = Column(Float, nullable=False)

    id_factura = Column(Integer, ForeignKey('facturas.id'), nullable=False)
    id_producto = Column(Integer, ForeignKey('productos.id'), nullable=False)
