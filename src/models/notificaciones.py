from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from src.models import Base, session


class Notificaciones(Base):
    """
    Sistema de notificaciones internas para empresas y clientes del portal.
    """
    __tablename__ = "notificaciones"

    id = Column(Integer, primary_key=True)
    id_empresa = Column(Integer, ForeignKey("empresas.id"), nullable=False, index=True)
    id_cuenta_cliente = Column(Integer, ForeignKey("cuentas_clientes.id"), nullable=True, index=True)
    id_usuario = Column(Integer, ForeignKey("usuarios.id"), nullable=True, index=True)
    destinatario_tipo = Column(String(20), nullable=False, index=True)  # 'empresa' | 'cliente'
    tipo = Column(String(40), nullable=False)  # 'pedido', 'reserva', 'solicitud', 'pago', 'sistema'
    titulo = Column(String(200), nullable=False)
    mensaje = Column(Text, nullable=False)
    referencia_id = Column(Integer, nullable=True)
    leida = Column(Integer, default=0, nullable=False)
    created_at = Column(DateTime, default=datetime.now, nullable=False)

    @classmethod
    def registrar(cls, id_empresa, destinatario_tipo, tipo, titulo, mensaje,
                  id_cuenta_cliente=None, id_usuario=None, referencia_id=None, commit=True):
        notif = cls(
            id_empresa=id_empresa,
            destinatario_tipo=destinatario_tipo,
            tipo=tipo,
            titulo=titulo,
            mensaje=mensaje,
            id_cuenta_cliente=id_cuenta_cliente,
            id_usuario=id_usuario,
            referencia_id=referencia_id,
            leida=0,
            created_at=datetime.now()
        )
        session.add(notif)
        if commit:
            session.commit()
        return notif

    def to_dict(self):
        return {
            "id": self.id,
            "id_empresa": self.id_empresa,
            "id_cuenta_cliente": self.id_cuenta_cliente,
            "id_usuario": self.id_usuario,
            "destinatario_tipo": self.destinatario_tipo,
            "tipo": self.tipo,
            "titulo": self.titulo,
            "mensaje": self.mensaje,
            "referencia_id": self.referencia_id,
            "leida": bool(self.leida),
            "created_at": self.created_at.strftime("%Y-%m-%d %H:%M:%S") if self.created_at else None,
        }


class SolicitudesCliente(Base):
    """
    Consultas, solicitudes, sugerencias o reclamos (PQRS) enviados por los clientes a una empresa.
    """
    __tablename__ = "solicitudes_cliente"

    id = Column(Integer, primary_key=True)
    radicado = Column(String(50), nullable=False, index=True)
    id_empresa = Column(Integer, ForeignKey("empresas.id"), nullable=False, index=True)
    id_cuenta_cliente = Column(Integer, ForeignKey("cuentas_clientes.id"), nullable=True, index=True)
    id_cliente = Column(Integer, ForeignKey("clientes.id"), nullable=True, index=True)
    id_pedido = Column(Integer, ForeignKey("pedidos.id"), nullable=True)
    id_reserva = Column(Integer, ForeignKey("reservas.id"), nullable=True)

    nombre_contacto = Column(String(150), nullable=False)
    email_contacto = Column(String(120), nullable=False)
    telefono_contacto = Column(String(40), nullable=True)

    tipo = Column(String(40), default="Consulta", nullable=False)  # 'Consulta', 'Solicitud', 'Reclamo', 'Sugerencia'
    asunto = Column(String(200), nullable=False)
    mensaje = Column(Text, nullable=False)
    estado = Column(String(30), default="Abierta", nullable=False)  # 'Abierta', 'En revisión', 'Respondida', 'Cerrada'
    respuesta = Column(Text, nullable=True)
    respondido_por = Column(Integer, ForeignKey("usuarios.id"), nullable=True)

    created_at = Column(DateTime, default=datetime.now, nullable=False)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now, nullable=False)

    def to_dict(self):
        fmt = "%Y-%m-%d %H:%M:%S"
        return {
            "id": self.id,
            "radicado": self.radicado,
            "id_empresa": self.id_empresa,
            "id_cuenta_cliente": self.id_cuenta_cliente,
            "id_cliente": self.id_cliente,
            "id_pedido": self.id_pedido,
            "id_reserva": self.id_reserva,
            "nombre_contacto": self.nombre_contacto,
            "email_contacto": self.email_contacto,
            "telefono_contacto": self.telefono_contacto or "",
            "tipo": self.tipo,
            "asunto": self.asunto,
            "mensaje": self.mensaje,
            "estado": self.estado,
            "respuesta": self.respuesta or "",
            "respuesta_empresa": self.respuesta or "",
            "respondido_por": self.respondido_por,
            "created_at": self.created_at.strftime(fmt) if self.created_at else None,
            "updated_at": self.updated_at.strftime(fmt) if self.updated_at else None,
        }
