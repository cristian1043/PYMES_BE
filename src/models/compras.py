from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey
from datetime import datetime
from src.models import Base, session
from src.models.proveedores import Proveedores
from src.models.usuarios import Usuarios
from src.models.metodos_pago import MetodosPago


class Compras(Base):
    __tablename__ = 'compras'

    id = Column(Integer, primary_key=True)
    numero = Column(String(50), unique=True, nullable=False)
    fecha = Column(DateTime, default=datetime.now, nullable=False)
    subtotal = Column(Float, nullable=False)
    iva = Column(Float, nullable=False)
    descuento = Column(Float, nullable=False)
    total = Column(Float, nullable=False)

    id_proveedor = Column(Integer, ForeignKey('proveedores.id'), nullable=False)
    id_usuario = Column(Integer, ForeignKey('usuarios.id'), nullable=False)
    id_metodo_pago = Column(Integer, nullable=True, default=1)
    metodo_pago = Column(String(100), default='Efectivo', nullable=True)
    referencia_pago = Column(String(100), nullable=True)
    estado = Column(String(20), default='Completada')
    id_empresa = Column(Integer, nullable=True)

    def create(self):
        session.add(self)
        session.commit()

    @staticmethod
    def get():
        return session.query(Compras).all()

    @staticmethod
    def get_query():
        return session.query(Compras)

    @staticmethod
    def get_by_id(id):
        return session.query(Compras).filter_by(id=id).first()

    def update(self):
        session.commit()

    def delete(self):
        session.delete(self)
        session.commit()

    def to_dict(self):
        prov = session.query(Proveedores).filter_by(id=self.id_proveedor).first() if self.id_proveedor else None

        metodo_pago_nombre = getattr(self, "metodo_pago", None)
        id_mp = getattr(self, "id_metodo_pago", None)
        if not metodo_pago_nombre and id_mp:
            try:
                metodo_obj = MetodosPago.get_by_id(id_mp)
                if metodo_obj and getattr(metodo_obj, "nombre", None):
                    metodo_pago_nombre = metodo_obj.nombre
            except Exception:
                pass
        if not metodo_pago_nombre:
            metodo_pago_nombre = "Efectivo"

        return {
            "id": self.id,
            "numero": self.numero,
            "fecha": self.fecha.strftime('%Y-%m-%d %H:%M:%S') if hasattr(self.fecha, 'strftime') else str(self.fecha) if self.fecha else None,
            "subtotal": self.subtotal,
            "iva": self.iva,
            "descuento": self.descuento,
            "total": self.total,
            "estado": self.estado or "Completada",
            "id_proveedor": self.id_proveedor,
            "proveedor_nombre": prov.nombre if prov else f"Proveedor #{self.id_proveedor}",
            "id_usuario": self.id_usuario,
            "id_metodo_pago": id_mp or 1,
            "metodo_pago": metodo_pago_nombre,
            "referencia_pago": getattr(self, "referencia_pago", None),
            "id_empresa": getattr(self, "id_empresa", None)
        }
