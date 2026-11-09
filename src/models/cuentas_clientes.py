from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, func
from src.models import Base, session


class CuentasClientes(Base):
    """
    Identidad de autenticación exclusiva para clientes externos del Portal de Clientes (PYMES_CLIENTES).
    Separada estrictamente de la tabla administrativa `usuarios` para evitar escalada de privilegios.
    Un cliente puede comprar o reservar en múltiples empresas registradas en PYMESOFT.
    """
    __tablename__ = "cuentas_clientes"

    id = Column(Integer, primary_key=True)
    tipo_documento = Column(String(10), default="CC", nullable=False)
    documento = Column(String(30), nullable=False, index=True)
    nombre = Column(String(100), nullable=False)
    apellido = Column(String(100), nullable=True, default="")
    email = Column(String(120), unique=True, nullable=False, index=True)
    telefono = Column(String(30), nullable=False)
    direccion_principal = Column(String(255), nullable=True, default="")
    ciudad = Column(String(100), nullable=True, default="")
    password_hash = Column(String(255), nullable=False)
    estado = Column(String(20), default="Activo", nullable=False)
    email_verificado = Column(Integer, default=1, nullable=False)
    sesion_version = Column(Integer, default=1, nullable=False)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)

    def save(self):
        session.add(self)
        session.commit()

    def update(self):
        self.updated_at = datetime.now()
        session.commit()

    @classmethod
    def get_by_id(cls, id):
        return session.query(cls).filter_by(id=id).first()

    @classmethod
    def get_by_email(cls, email):
        if not email:
            return None
        val = str(email).strip().lower()
        return session.query(cls).filter(func.lower(cls.email) == val).first()

    @property
    def nombre_completo(self):
        partes = [self.nombre or "", self.apellido or ""]
        return " ".join(p.strip() for p in partes if p and p.strip())

    def to_dict(self):
        return {
            "id": self.id,
            "tipo_documento": self.tipo_documento or "CC",
            "documento": self.documento,
            "nombre": self.nombre,
            "apellido": self.apellido or "",
            "nombre_completo": self.nombre_completo,
            "email": self.email,
            "telefono": self.telefono,
            "direccion_principal": self.direccion_principal or "",
            "ciudad": self.ciudad or "",
            "estado": self.estado or "Activo",
            "email_verificado": bool(self.email_verificado),
            "sesion_version": self.sesion_version or 1,
            "created_at": self.created_at.strftime("%Y-%m-%d %H:%M:%S") if self.created_at else None,
        }


class DireccionesClientes(Base):
    """
    Direcciones de entrega registradas por una cuenta de cliente externo.
    """
    __tablename__ = "direcciones_clientes"

    id = Column(Integer, primary_key=True)
    id_cuenta_cliente = Column(Integer, ForeignKey("cuentas_clientes.id"), nullable=False, index=True)
    alias = Column(String(80), default="Principal", nullable=False)
    direccion = Column(String(255), nullable=False)
    ciudad = Column(String(100), nullable=True, default="")
    departamento = Column(String(100), nullable=True, default="")
    referencia = Column(String(255), nullable=True, default="")
    telefono_contacto = Column(String(30), nullable=True, default="")
    es_principal = Column(Integer, default=0, nullable=False)
    created_at = Column(DateTime, default=datetime.now)

    def save(self):
        session.add(self)
        session.commit()

    def update(self):
        session.commit()

    def delete(self):
        session.delete(self)
        session.commit()

    def to_dict(self):
        return {
            "id": self.id,
            "id_cuenta_cliente": self.id_cuenta_cliente,
            "alias": self.alias,
            "direccion": self.direccion,
            "ciudad": self.ciudad or "",
            "departamento": self.departamento or "",
            "referencia": self.referencia or "",
            "telefono_contacto": self.telefono_contacto or "",
            "es_principal": bool(self.es_principal),
        }


class VinculacionesClientes(Base):
    """
    Relación verificada entre una cuenta de cliente externo (`CuentasClientes`) y su ficha comercial
    (`Clientes`) dentro de una empresa específica (`id_empresa`).
    Previene que un atacante consulte facturas históricas de otro cliente simplemente registrando su cédula:
    si la ficha comercial ya existía previamente en la empresa, la vinculación para ver historial previo
    de facturas requiere que el correo coincida o que se valide mediante código OTP / aprobación de la empresa.
    """
    __tablename__ = "vinculaciones_clientes"

    id = Column(Integer, primary_key=True)
    id_cuenta_cliente = Column(Integer, ForeignKey("cuentas_clientes.id"), nullable=False, index=True)
    id_empresa = Column(Integer, ForeignKey("empresas.id"), nullable=False, index=True)
    id_cliente = Column(Integer, ForeignKey("clientes.id"), nullable=False, index=True)
    estado_verificacion = Column(String(20), default="Verificado", nullable=False)  # 'Pendiente', 'Verificado', 'Rechazado'
    metodo_verificacion = Column(String(40), default="registro_portal", nullable=True)
    created_at = Column(DateTime, default=datetime.now)
    verified_at = Column(DateTime, nullable=True)

    def save(self):
        session.add(self)
        session.commit()

    def update(self):
        session.commit()

    def to_dict(self):
        return {
            "id": self.id,
            "id_cuenta_cliente": self.id_cuenta_cliente,
            "id_empresa": self.id_empresa,
            "id_cliente": self.id_cliente,
            "estado_verificacion": self.estado_verificacion,
            "metodo_verificacion": self.metodo_verificacion,
            "created_at": self.created_at.strftime("%Y-%m-%d %H:%M:%S") if self.created_at else None,
            "verified_at": self.verified_at.strftime("%Y-%m-%d %H:%M:%S") if self.verified_at else None,
        }
