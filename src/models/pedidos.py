from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, Text, DateTime, ForeignKey
from src.models import Base, session


class Pedidos(Base):
    """
    Pedidos comerciales realizados desde el Portal de Clientes (separados de Facturas).
    Un pedido solo genera o se asocia a una factura cuando la empresa o el flujo de pago lo confirma explícitamente.
    """
    __tablename__ = "pedidos"

    ESTADOS_VALIDOS = (
        "Pendiente",
        "Confirmado",
        "En preparación",
        "Listo para recoger",
        "Enviado",
        "Entregado",
        "Cancelado",
    )

    id = Column(Integer, primary_key=True)
    numero = Column(String(50), nullable=False, index=True)
    id_empresa = Column(Integer, ForeignKey("empresas.id"), nullable=False, index=True)
    id_cuenta_cliente = Column(Integer, ForeignKey("cuentas_clientes.id"), nullable=True, index=True)
    id_cliente = Column(Integer, ForeignKey("clientes.id"), nullable=False, index=True)

    estado = Column(String(30), default="Pendiente", nullable=False, index=True)
    modalidad_entrega = Column(String(40), default="Domicilio", nullable=False)  # 'Domicilio', 'Recoger en tienda'
    direccion_entrega = Column(String(255), nullable=True)
    ciudad_entrega = Column(String(100), nullable=True)
    telefono_contacto = Column(String(40), nullable=True)
    notas_cliente = Column(Text, nullable=True)
    notas_internas = Column(Text, nullable=True)

    subtotal = Column(Float, nullable=False, default=0.0)
    iva = Column(Float, nullable=False, default=0.0)
    descuento = Column(Float, nullable=False, default=0.0)
    costo_envio = Column(Float, nullable=False, default=0.0)
    total = Column(Float, nullable=False, default=0.0)

    id_metodo_pago = Column(Integer, ForeignKey("metodos_pago.id"), nullable=True, default=1)
    metodo_pago_nombre = Column(String(80), default="Efectivo / Contraentrega", nullable=True)
    estado_pago = Column(String(30), default="Pendiente", nullable=False)  # 'Pendiente', 'Pagado', 'Rechazado', 'Reembolsado'
    pasarela = Column(String(50), nullable=True)
    referencia_pago = Column(String(100), nullable=True)

    id_factura = Column(Integer, ForeignKey("facturas.id"), nullable=True)
    inventario_descontado = Column(Integer, default=1, nullable=False)

    created_at = Column(DateTime, default=datetime.now, nullable=False)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now, nullable=False)

    def create(self):
        session.add(self)
        session.commit()

    def update(self):
        self.updated_at = datetime.now()
        session.commit()

    @classmethod
    def get_by_id(cls, id):
        return session.query(cls).filter_by(id=id).first()

    def to_dict(self, include_detalles=False, include_historial=False):
        from src.models.clientes import Clientes
        cliente_nombre = "Cliente Portal"
        cliente_doc = ""
        cliente_email = ""
        try:
            cli = Clientes.get_by_id(self.id_cliente)
            if cli:
                cliente_nombre = cli.nombre
                cliente_doc = cli.documento
                cliente_email = cli.email or ""
        except Exception:
            pass

        fmt = "%Y-%m-%d %H:%M:%S"
        data = {
            "id": self.id,
            "numero": self.numero,
            "numero_pedido": self.numero,
            "id_empresa": self.id_empresa,
            "id_cuenta_cliente": self.id_cuenta_cliente,
            "id_cliente": self.id_cliente,
            "cliente_nombre": cliente_nombre,
            "nombre_cliente": cliente_nombre,
            "cliente_documento": cliente_doc,
            "documento_cliente": cliente_doc,
            "cliente_email": cliente_email,
            "email_cliente": cliente_email,
            "telefono_cliente": self.telefono_contacto or "",
            "estado": self.estado,
            "modalidad_entrega": self.modalidad_entrega,
            "direccion_entrega": self.direccion_entrega or "",
            "ciudad_entrega": self.ciudad_entrega or "",
            "telefono_contacto": self.telefono_contacto or "",
            "notas_cliente": self.notas_cliente or "",
            "observaciones": self.notas_cliente or "",
            "notas_internas": self.notas_internas or "",
            "subtotal": round(float(self.subtotal or 0.0), 2),
            "iva": round(float(self.iva or 0.0), 2),
            "descuento": round(float(self.descuento or 0.0), 2),
            "costo_envio": round(float(self.costo_envio or 0.0), 2),
            "total": round(float(self.total or 0.0), 2),
            "id_metodo_pago": self.id_metodo_pago or 1,
            "metodo_pago": self.metodo_pago_nombre or "Efectivo / Contraentrega",
            "metodo_pago_preferido": self.metodo_pago_nombre or "Efectivo / Contraentrega",
            "estado_pago": self.estado_pago or "Pendiente",
            "pasarela": self.pasarela,
            "referencia_pago": self.referencia_pago,
            "id_factura": self.id_factura,
            "inventario_descontado": bool(self.inventario_descontado),
            "fecha": self.created_at.strftime(fmt) if self.created_at else None,
            "fecha_creacion": self.created_at.strftime(fmt) if self.created_at else None,
            "created_at": self.created_at.strftime(fmt) if self.created_at else None,
            "updated_at": self.updated_at.strftime(fmt) if self.updated_at else None,
        }
        if include_detalles:
            detalles = session.query(DetallePedidos).filter_by(id_pedido=self.id).all()
            data["detalles"] = [d.to_dict() for d in detalles]
        if include_historial:
            historial = session.query(HistorialPedidos).filter_by(id_pedido=self.id).order_by(HistorialPedidos.id.asc()).all()
            data["historial"] = [h.to_dict() for h in historial]
        return data


class DetallePedidos(Base):
    """
    Detalle histórico de cada ítem del pedido. Conserva el nombre, código y precio unitario vigentes
    en el momento exacto del pedido aunque el producto cambie posteriormente en el catálogo.
    """
    __tablename__ = "detalle_pedidos"

    id = Column(Integer, primary_key=True)
    id_pedido = Column(Integer, ForeignKey("pedidos.id"), nullable=False, index=True)
    id_producto = Column(Integer, ForeignKey("productos.id"), nullable=False, index=True)
    codigo_producto = Column(String(60), nullable=False)
    nombre_producto = Column(String(255), nullable=False)
    unidad_medida = Column(String(10), default="UND", nullable=False)
    cantidad = Column(Integer, nullable=False)
    precio_unitario = Column(Float, nullable=False)
    descuento_item = Column(Float, default=0.0, nullable=False)
    subtotal = Column(Float, nullable=False)

    def to_dict(self):
        return {
            "id": self.id,
            "id_pedido": self.id_pedido,
            "id_producto": self.id_producto,
            "codigo_producto": self.codigo_producto,
            "nombre_producto": self.nombre_producto,
            "unidad_medida": self.unidad_medida,
            "cantidad": self.cantidad,
            "precio_unitario": round(float(self.precio_unitario or 0.0), 2),
            "descuento_item": round(float(self.descuento_item or 0.0), 2),
            "subtotal": round(float(self.subtotal or 0.0), 2),
        }


class HistorialPedidos(Base):
    """
    Bitácora de auditoría para todos los cambios de estado de un pedido.
    """
    __tablename__ = "historial_pedidos"

    id = Column(Integer, primary_key=True)
    id_pedido = Column(Integer, ForeignKey("pedidos.id"), nullable=False, index=True)
    estado_anterior = Column(String(30), nullable=True)
    estado_nuevo = Column(String(30), nullable=False)
    comentario = Column(String(500), nullable=True)
    actor_tipo = Column(String(20), default="sistema", nullable=False)  # 'cliente', 'admin', 'sistema'
    actor_id = Column(Integer, nullable=True)
    created_at = Column(DateTime, default=datetime.now, nullable=False)

    def to_dict(self):
        return {
            "id": self.id,
            "id_pedido": self.id_pedido,
            "estado_anterior": self.estado_anterior,
            "estado_nuevo": self.estado_nuevo,
            "comentario": self.comentario or "",
            "actor_tipo": self.actor_tipo,
            "actor_id": self.actor_id,
            "fecha": self.created_at.strftime("%Y-%m-%d %H:%M:%S") if self.created_at else None,
        }
