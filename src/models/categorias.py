from sqlalchemy import Column, Integer, String
from src.models import Base, session 

class Categorias(Base):
    __tablename__ = 'categorias'

    id = Column(Integer, primary_key=True)
    nombre = Column(String(100), nullable=False)

    def save(self):
        session.add(self)
        session.commit()

    @staticmethod
    def get():
        return session.query(Categorias).all()

    @staticmethod
    def get_by_id(id):
        return session.query(Categorias).filter_by(id=id).first()

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