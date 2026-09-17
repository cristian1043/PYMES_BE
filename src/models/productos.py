from sqlalchemy import Column, Integer, String, Float, ForeignKey
from src.models import Base, session
from src.models.categorias import Categorias
from src.models.proveedores import Proveedores


class Productos(Base):
    __tablename__ = 'productos'

    id = Column(Integer, primary_key=True)
    codigo = Column(String(50), nullable=False)
    nombre = Column(String(255), nullable=False)
    descripcion = Column(String(255), nullable=False)
    unidad_medida = Column(String(3), nullable=False)
    precio = Column(Float, nullable=False)
    stock = Column(Integer, nullable=False)
    id_categoria = Column(Integer, ForeignKey('categorias.id'), nullable=False)
    id_proveedor = Column(Integer, ForeignKey('proveedores.id'), nullable=True)
    costo = Column(Float, nullable=True, default=0.0)
    estado = Column(String(20), default="Activo")
    imagen = Column(String, nullable=True)
    id_empresa = Column(Integer, nullable=True)

    def create(self):
        session.add(self)
        session.commit()

    @staticmethod
    def get():
        return session.query(Productos).all()

    @staticmethod
    def get_query():
        return session.query(Productos)

    @staticmethod
    def get_by_id(id):
        return session.query(Productos).filter_by(id=id).first()

    def update(self):
        session.commit()

    def delete(self):
        session.delete(self)
        session.commit()

    def to_dict(self):
        costo_val = self.costo if (self.costo is not None and self.costo > 0) else round((self.precio or 0.0) * 0.70, 2)
        cat = session.query(Categorias).filter_by(id=self.id_categoria).first() if self.id_categoria else None
        prov = session.query(Proveedores).filter_by(id=self.id_proveedor).first() if self.id_proveedor else None
        return {
            "id": self.id,
            "codigo": self.codigo,
            "nombre": self.nombre,
            "descripcion": self.descripcion,
            "unidad_medida": self.unidad_medida,
            "precio": self.precio,
            "costo": costo_val,
            "stock": self.stock,
            "id_categoria": self.id_categoria,
            "categoria_nombre": cat.nombre if cat else "Sin categoría",
            "id_proveedor": self.id_proveedor,
            "proveedor_nombre": prov.nombre if prov else "Sin proveedor distribuidor",
            "estado": self.estado or "Activo",
            "imagen": self.imagen,
            "id_empresa": self.id_empresa
        }
