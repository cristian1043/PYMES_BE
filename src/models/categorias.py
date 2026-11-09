from sqlalchemy import Column, Integer, String, or_
from src.models import Base, session


class Categorias(Base):
    __tablename__ = 'categorias'

    id = Column(Integer, primary_key=True)
    nombre = Column(String(100), nullable=False)
    descripcion = Column(String(255), nullable=True)
    estado = Column(String(20), default="Activo", nullable=True)
    id_empresa = Column(Integer, nullable=True, index=True)

    def create(self):
        session.add(self)
        session.commit()

    @staticmethod
    def get(id_empresa=None, include_global=True):
        q = session.query(Categorias)
        if id_empresa is not None:
            if include_global:
                q = q.filter(or_(Categorias.id_empresa == int(id_empresa), Categorias.id_empresa == None))
            else:
                q = q.filter(Categorias.id_empresa == int(id_empresa))
        return q.all()

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
            "nombre": self.nombre,
            "descripcion": getattr(self, "descripcion", "") or "",
            "estado": getattr(self, "estado", "Activo") or "Activo",
            "id_empresa": getattr(self, "id_empresa", None)
        }
