from sqlalchemy import Column, Integer, String
from src.models import Base, session

class Proveedores(Base):
    __tablename__ = 'proveedores'

    id = Column(Integer, primary_key=True)
    nit = Column(String(20), unique=True, nullable=False)
    nombre = Column(String(255), nullable=False)
    telefono = Column(String(20), nullable=False)
    direccion = Column(String(255), nullable=False)
    email = Column(String(255), unique=True, nullable=False)

    def save(self):
        session.add(self)
        session.commit()   
    
    @staticmethod
    def get():
        return session.query(Proveedores).all()
    
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
            "nit": self.nit,
            "nombre": self.nombre,
            "telefono": self.telefono,
            "direccion": self.direccion,
            "email": self.email
        }