from sqlalchemy import Column, DateTime, Integer, String
from src.models import Base, session
from datetime import date, datetime

class Clientes(Base):
    __tablename__ = 'clientes'
 
    id = Column(Integer, primary_key=True)
    documento = Column(String(50), nullable=False)
    tipo_documento = Column(String(20), default='CC', nullable=True)
    nombre = Column(String(100), nullable=False)
    apellido = Column(String(100), nullable=True)
    codigo = Column(String(50), nullable=True)
    direccion = Column(String(255), nullable=False)
    telefono = Column(String(20), nullable=False)
    email = Column(String(255), nullable=False)
    estado = Column(String(20), default='Activo', nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow) 
    # OBSOLETO (PCI-DSS): columnas de tarjeta conservadas solo por compatibilidad con bases de datos existentes.
    # Su contenido se borra en src/utils/migrations.py y la API ya no las lee, escribe ni devuelve.
    # Los cobros con tarjeta se hacen en el datáfono (Bold) o en el checkout de la pasarela (Wompi).
    tiene_tarjeta = Column(String(5), default='No')
    tipo_tarjeta = Column(String(50))
    banco_tarjeta = Column(String(100))
    franquicia_tarjeta = Column(String(50))
    ultimos_digitos_tarjeta = Column(String(4))
    numero_tarjeta = Column(String(20))
    titular_tarjeta = Column(String(100))
    fecha_expiracion = Column(String(10))
    cvc_tarjeta = Column(String(10))
    id_empresa = Column(Integer, nullable=True)

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

    @staticmethod
    def get_by_documento(documento, empresa_id=None):
        if not documento:
            return None
        doc_str = str(documento).strip()
        if empresa_id:
            try:
                eid = int(empresa_id)
            except (ValueError, TypeError):
                eid = 1
            c = session.query(Clientes).filter(
                (Clientes.documento == doc_str) | (Clientes.documento == f"{doc_str}#E{eid}"),
                Clientes.id_empresa == eid
            ).first()
            if c:
                return c
            # Solo adoptar registros huérfanos sin empresa asignada (nunca robar clientes de otra empresa)
            c_orphan = session.query(Clientes).filter(
                Clientes.documento == doc_str,
                Clientes.id_empresa == None
            ).first()
            if c_orphan:
                c_orphan.id_empresa = eid
                c_orphan.estado = "Activo"
                c_orphan.update()
                return c_orphan
            return None
        return session.query(Clientes).filter(Clientes.documento == doc_str).first()

    def update(self):
        session.commit()
    
    def delete(self):
        session.delete(self)
        session.commit()
   
    def to_dict(self):
        doc_clean = (self.documento or "").split("#E")[0]
        return {
            "id": self.id,
            "codigo": getattr(self, "codigo", None) or f"CLI-E{getattr(self, 'id_empresa', 1) or 1}-{self.id:03d}",
            "nombre": self.nombre,
            "apellido": getattr(self, "apellido", "") or "",
            "documento": doc_clean,
            "tipo_documento": getattr(self, "tipo_documento", "CC") or "CC",
            "direccion": self.direccion,
            "telefono": self.telefono,
            "email": self.email,
            "estado": getattr(self, "estado", "Activo") or "Activo",
            "created_at": self.created_at,
            "id_empresa": getattr(self, "id_empresa", None)
        }
