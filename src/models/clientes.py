from sqlalchemy import Column, DateTime, Integer, String
from src.models import Base, session
from datetime import date, datetime

class Clientes(Base):
    __tablename__ = 'clientes'
 
    id = Column(Integer, primary_key=True)
    documento = Column(String(50), unique=True, nullable=False)
    nombre = Column(String(255), nullable=False)
    direccion = Column(String(255), nullable=False)
    telefono = Column(String(20), nullable=False)
    email = Column(String(255), unique=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow) 

    def save(self):
        session.add(self)
        session.commit()

    @staticmethod
    def get():
        return session.query(Clientes).all()

    @staticmethod
    def get_by_id(id):
        return session.query(Clientes).filter_by(id=id).first()

    def update(self):
        session.commit()
    
    def delete(self):
        session.delete(self)
        session.commit()
   
    def to_dict(self):
        return {
            "id": self.id,
            "nombre": self.nombre
        }