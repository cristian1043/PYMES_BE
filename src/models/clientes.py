from sqlalchemy import Column, DateTime, Integer, String
from src.models import Base, session
from datetime import date, datetime

class Clientes(Base):
    __tablename__ = 'clientes'
 
    id = Column(Integer, primary_key=True)
    documento = Column(String(50), unique=True, nullable=False)
    nombre = Column(String(100), nullable=False)
    direccion = Column(String(255), nullable=False)
    telefono = Column(String(20), nullable=False)
    email = Column(String(255), unique=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow) 
    tiene_tarjeta = Column(String(5), default='No')
    tipo_tarjeta = Column(String(50))
    banco_tarjeta = Column(String(100))
    franquicia_tarjeta = Column(String(50))
    ultimos_digitos_tarjeta = Column(String(4))
    numero_tarjeta = Column(String(20))
    titular_tarjeta = Column(String(100))
    fecha_expiracion = Column(String(10))
    cvc_tarjeta = Column(String(10))

    def save(self):
        session.add(self)
        session.commit()

    @staticmethod
    def get():
        return session.query(Clientes).all()

    @staticmethod
    def get_query():
        return session.query(Clientes)

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
            "nombre": self.nombre,
            "documento": self.documento,
            "direccion": self.direccion,
            "telefono": self.telefono,
            "email": self.email,
            "created_at": self.created_at,
            "tiene_tarjeta": self.tiene_tarjeta or 'No',
            "tipo_tarjeta": self.tipo_tarjeta,
            "banco_tarjeta": self.banco_tarjeta,
            "franquicia_tarjeta": self.franquicia_tarjeta,
            "ultimos_digitos_tarjeta": self.ultimos_digitos_tarjeta,
            "numero_tarjeta": self.numero_tarjeta,
            "titular_tarjeta": self.titular_tarjeta,
            "fecha_expiracion": self.fecha_expiracion,
            "cvc_tarjeta": self.cvc_tarjeta
        }