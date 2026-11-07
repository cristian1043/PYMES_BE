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
    id_empresa = Column(Integer, nullable=True)

    def save(self):
        session.add(self)
        session.commit()

    def create(self):
        session.add(self)
        session.commit()
        return self

    @staticmethod
    def get():
        return session.query(MovimientosInventario).all()

    @staticmethod
    def get_query():
        return session.query(MovimientosInventario)

    @staticmethod
    def get_by_id(id):
        return session.query(MovimientosInventario).filter_by(id=id).first()

    def update(self):
        session.commit()

    def delete(self):
        session.delete(self)
        session.commit()
        
    def to_dict(self):
        return {
            "id": self.id,
            "tipo_movimiento": self.tipo_movimiento,
            "cantidad": self.cantidad,
            "fecha": self.fecha.strftime('%Y-%m-%d %H:%M:%S') if isinstance(self.fecha, datetime) else self.fecha,
            "observacion": self.observacion,
            "id_producto": self.id_producto,
            "id_usuario": self.id_usuario,
            "id_empresa": getattr(self, "id_empresa", None)
        }
