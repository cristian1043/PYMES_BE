from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime
from src.models import Base, session


class Terminales(Base):
    """Terminal de pago física (datáfono) vinculada a una empresa y a un método de pago integrado (Bold / Simulado)."""
    __tablename__ = 'terminales_pago'

    id = Column(Integer, primary_key=True)
    id_empresa = Column(Integer, nullable=False)
    nombre = Column(String(100), nullable=False)            # Ej: "Caja 1"
    proveedor = Column(String(30), nullable=False, default='simulado')  # 'bold', 'simulado'
    id_metodo_pago = Column(Integer, nullable=False)        # Método de pago que contiene las credenciales
    terminal_serial = Column(String(100), nullable=True)    # Serial del datáfono (Bold: terminal_serial)
    terminal_model = Column(String(50), nullable=True)      # Modelo del datáfono (Bold: terminal_model, ej. N86)
    email_usuario = Column(String(255), nullable=True)      # Bold: email del usuario del comercio que opera el datáfono
    estado = Column(String(20), default='Activo')           # Activo, Inactivo
    created_at = Column(DateTime, default=datetime.now)

    def create(self):
        session.add(self)
        session.commit()

    def update(self):
        session.commit()

    @staticmethod
    def get_query():
        return session.query(Terminales)

    @staticmethod
    def get_by_id(id):
        return session.query(Terminales).filter_by(id=id).first()

    def to_dict(self):
        metodo_nombre = None
        try:
            from src.models.metodos_pago import MetodosPago
            metodo = MetodosPago.get_by_id(self.id_metodo_pago)
            metodo_nombre = metodo.nombre if metodo else None
        except Exception:
            pass
        return {
            "id": self.id,
            "id_empresa": self.id_empresa,
            "nombre": self.nombre,
            "proveedor": self.proveedor,
            "id_metodo_pago": self.id_metodo_pago,
            "metodo_pago_nombre": metodo_nombre,
            "terminal_serial": self.terminal_serial,
            "codigo_terminal": self.terminal_serial,
            "terminal_model": self.terminal_model,
            "email_usuario": self.email_usuario,
            "estado": self.estado or "Activo",
            "created_at": self.created_at.strftime('%Y-%m-%d %H:%M:%S') if self.created_at else None
        }
