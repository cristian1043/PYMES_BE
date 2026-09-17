from sqlalchemy import Column, Integer, String, ForeignKey
from src.models import Base, session

class MetodosPago(Base):
    __tablename__ = 'metodos_pago'

    id = Column(Integer, primary_key=True)
    nombre = Column(String(100), nullable=False)
    descripcion = Column(String(255), nullable=True)
    tipo = Column(String(50), default='Efectivo')  # Efectivo, Transferencia, Tarjeta, Pasarela, Billetera Digital, Crédito
    banco = Column(String(100), nullable=True)     # Bancolombia, Davivienda, Nequi, Daviplata, BBVA, etc.
    numero_cuenta = Column(String(50), nullable=True) # Número de cuenta, teléfono o identificador
    titular = Column(String(150), nullable=True)   # Nombre o razón social del titular
    id_empresa = Column(Integer, nullable=True)    # NULL = Global / Base, INT = Específico de esa empresa
    estado = Column(String(20), default='Activo')   # Activo, Inactivo
    
    # Integración con Pasarelas de Pago
    pasarela = Column(String(50), default='ninguna') # 'ninguna', 'wompi', 'mercadopago', 'stripe', 'bold', 'payu', 'epayco'
    api_key_publica = Column(String(255), nullable=True) # Public Key / Client ID expuesta para frontend
    api_key_privada = Column(String(255), nullable=True) # Secret Key / Token privado para backend
    webhook_secret = Column(String(255), nullable=True)  # Secreto para webhook
    modo = Column(String(20), default='sandbox')         # 'sandbox' (pruebas), 'produccion'

    def save(self):
        session.add(self)
        session.commit()

    def create(self):
        session.add(self)
        session.commit()

    @staticmethod
    def get():
        return session.query(MetodosPago).all()

    @staticmethod
    def get_query():
        return session.query(MetodosPago)

    @staticmethod
    def get_by_id(id):
        return session.query(MetodosPago).filter_by(id=id).first()

    def update(self):
        session.commit()

    def delete(self):
        session.delete(self)
        session.commit()

    def to_dict(self, incluir_privadas=False):
        d = {
            "id": self.id,
            "nombre": self.nombre,
            "descripcion": self.descripcion,
            "tipo": self.tipo or "Efectivo",
            "banco": self.banco,
            "numero_cuenta": self.numero_cuenta,
            "titular": self.titular,
            "id_empresa": self.id_empresa,
            "es_global": self.id_empresa is None,
            "estado": self.estado or "Activo",
            "pasarela": self.pasarela or "ninguna",
            "api_key_publica": self.api_key_publica,
            "modo": self.modo or "sandbox",
            "tiene_llave_privada": bool(self.api_key_privada)
        }
        if incluir_privadas:
            d["api_key_privada"] = self.api_key_privada
            d["webhook_secret"] = self.webhook_secret
        return d