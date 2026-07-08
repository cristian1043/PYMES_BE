from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from datetime import datetime
from src.models import Base, session
from src.models.productos import Productos
from src.models.usuarios import Usuarios


class MovimientosInventario(Base):
    __tablename__ = 'movimientos_inventario'

    id = Column(Integer, primary_key=True)
    tipo_movimiento = Column(String(20), nullable=False)
    cantidad = Column(Integer, nullable=False)
    fecha = Column(DateTime, default=datetime.now, nullable=False)
    observacion = Column(String(255), nullable=True)

    id_producto = Column(Integer, ForeignKey('productos.id'), nullable=False)
    id_usuario = Column(Integer, ForeignKey('usuarios.id'), nullable=False)
