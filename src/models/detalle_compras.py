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

    def save(self):
        session.add(self)
        session.commit()
 
    @staticmethod
    def get():
        return session.query(DetalleCompras).all()

    @staticmethod
    def get_by_id(id):
        return session.query(DetalleCompras).filter_by(id=id).first()

    def update(self):
        session.commit()

    def delete(self):
        session.delete(self)
        session.commit()
        
    def to_dict(self):
        return {
            "id": self.id,
            "cantidad": self.cantidad,
            "costo_unitario": self.costo_unitario,
            "subtotal": self.subtotal,
            "id_compra": self.id_compra,
            "id_producto": self.id_producto
        }