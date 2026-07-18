from sqlalchemy import Column, Integer, String, ForeignKey
from src.models import Base, session
from src.models.roles import Roles
 
class Usuarios(Base):
    __tablename__ = 'usuarios'

    id = Column(Integer, primary_key=True)
    documento = Column(String(20), unique=True, nullable=False)
    nombre = Column(String(255), nullable=False)
    apellido = Column(String(255), nullable=False)
    telefono = Column(String(20), nullable=False)
    email = Column(String(255), unique=True, nullable=False)
    username = Column(String(100), unique=True, nullable=False)
    password = Column(String(255), nullable=False)
    id_rol = Column(Integer, ForeignKey('roles.id'), nullable=False)

def save(self):
    session.add(self)
    session.commit()

@staticmethod
def get():
    return session.query(Usuarios).all()

@staticmethod
def get_by_id(id):
    return session.query(Usuarios).filter_by(id=id).first()

def update(self):
    session.commit()
    
def delete(self):
    session.delete(self)
    session.commit()
    
def to_dict(self):
    return {
        "id": self.id,
        "documento": self.documento,
        "nombre": self.nombre,
        "apellido": self.apellido,
        "telefono": self.telefono,
        "email": self.email,
        "username": self.username,
        "id_rol": self.id_rol
    }