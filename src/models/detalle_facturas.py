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

    def create(self):
        session.add(self)
        session.commit()
 
    @staticmethod
    def get():
        return session.query(DetalleFacturas).all()

    @staticmethod
    def get_by_id(id):
        return session.query(DetalleFacturas).filter_by(id=id).first()

    def update(self):
        session.commit()

    def delete(self):
        session.delete(self)
        session.commit()
        
    def to_dict(self):
        return {
            "id": self.id,
            "cantidad": self.cantidad,
            "precio_unitario": self.precio_unitario,
            "subtotal": self.subtotal,
            "id_factura": self.id_factura,
            "id_producto": self.id_producto
        }