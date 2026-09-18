from sqlalchemy import Column, Integer, String
from src.models import Base, session

class Proveedores(Base):
    __tablename__ = 'proveedores'

    id = Column(Integer, primary_key=True)
    nit = Column(String(20), unique=True, nullable=False)
    codigo = Column(String(50), nullable=True)
    nombre = Column(String(255), nullable=False)
    contacto = Column(String(100), nullable=True)
    telefono = Column(String(20), nullable=False)
    direccion = Column(String(255), nullable=False)
    email = Column(String(255), unique=True, nullable=False)
    detalle_servicios = Column(String(500))
    estado = Column(String(20), default='Activo', nullable=True)
    id_empresa = Column(Integer, nullable=True)

    def save(self):
        session.add(self)
        session.commit()   
    
    @staticmethod
    def get():
        return session.query(Proveedores).all()

    @staticmethod
    def get_query():
        return session.query(Proveedores)
    
    @staticmethod
    def get_by_id(id):
        return session.query(Proveedores).filter_by(id=id).first()
    
    def update(self):
        session.commit()  
        
    def delete(self):
        session.delete(self)
        session.commit()
        
    def to_dict(self):
        return {
            "id": self.id,
            "codigo": getattr(self, "codigo", None) or f"PROV-E{getattr(self, 'id_empresa', 1) or 1}-{self.id:03d}",
            "nit": self.nit,
            "nombre": self.nombre,
            "contacto": getattr(self, "contacto", "") or "",
            "telefono": self.telefono,
            "direccion": self.direccion or "",
            "email": self.email,
            "detalle_servicios": self.detalle_servicios or "",
            "estado": getattr(self, "estado", "Activo") or "Activo",
            "id_empresa": getattr(self, "id_empresa", None)
        }