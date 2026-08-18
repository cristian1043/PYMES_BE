from sqlalchemy import Column, Integer, String, ForeignKey
from src.models import Base, session
from src.models.roles import Roles
from src.models.usuarios import Usuarios
from src.models.empresas import Empresas

class UsuarioEmpresas(Base):
    __tablename__ = "usuario_empresas"

    id = Column(Integer, primary_key=True)
    usuario_id = Column(Integer, ForeignKey("usuarios.id"), nullable=False)
    empresa_id = Column(Integer, ForeignKey("empresas.id"), nullable=False)
    rol_id = Column(Integer, ForeignKey("roles.id"), nullable=False)
    estado = Column(String(20), default="Activo", nullable=False)

    def save(self):
        session.add(self)
        session.commit()

    @staticmethod
    def get():
        return session.query(UsuarioEmpresas).all()

    @staticmethod
    def get_by_usuario_empresa(usuario_id, empresa_id):
        return session.query(UsuarioEmpresas).filter_by(usuario_id=usuario_id, empresa_id=empresa_id).first()

    @staticmethod
    def get_by_usuario_id(usuario_id):
        return session.query(UsuarioEmpresas).filter_by(usuario_id=usuario_id).all()

    def update(self):
        session.commit()

    def delete(self):
        session.delete(self)
        session.commit()

    def to_dict(self):
        return {
            "id": self.id,
            "usuario_id": self.usuario_id,
            "empresa_id": self.empresa_id,
            "rol_id": self.rol_id,
            "estado": self.estado
        }
