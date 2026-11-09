from datetime import datetime
import json
import re
from sqlalchemy import Column, Integer, String, Float, Text, DateTime, ForeignKey
from src.models import Base, session


def slugify_empresa(texto, fallback_id=1):
    if not texto:
        return f"empresa-{fallback_id}"
    s = str(texto).strip().lower()
    reemplazos = {"á": "a", "é": "e", "í": "i", "ó": "o", "ú": "u", "ñ": "n", "ü": "u"}
    for k, v in reemplazos.items():
        s = s.replace(k, v)
    s = re.sub(r"[^a-z0-9]+", "-", s).strip("-")
    return s or f"empresa-{fallback_id}"


class ConfiguracionPortal(Base):
    """
    Configuración del Portal de Clientes por empresa (arquitectura multi-tenant).
    Permite activar/desactivar el portal y personalizar su identidad visual, canales y módulos.
    """
    __tablename__ = "configuracion_portal"

    id = Column(Integer, primary_key=True)
    id_empresa = Column(Integer, ForeignKey("empresas.id"), unique=True, nullable=False, index=True)
    slug = Column(String(120), unique=True, nullable=False, index=True)
    activo = Column(Integer, default=1, nullable=False)

    nombre_publico = Column(String(150), nullable=False)
    eslogan = Column(String(255), nullable=True)
    descripcion = Column(Text, nullable=True)
    logo_url = Column(Text(length=16777215), nullable=True)
    portada_url = Column(Text(length=16777215), nullable=True)
    color_primario = Column(String(20), default="#2563eb", nullable=False)
    color_secundario = Column(String(20), default="#1e40af", nullable=False)

    telefono_contacto = Column(String(40), nullable=True)
    email_contacto = Column(String(120), nullable=True)
    whatsapp = Column(String(40), nullable=True)
    direccion = Column(String(255), nullable=True)
    horario_atencion = Column(String(255), default="Lunes a Sábado: 8:00 AM - 6:00 PM", nullable=True)
    redes_sociales = Column(Text, nullable=True)  # JSON string: {"instagram": "", "facebook": "", "web": ""}

    mostrar_catalogo = Column(Integer, default=1, nullable=False)
    mostrar_precios = Column(Integer, default=1, nullable=False)
    permitir_pedidos = Column(Integer, default=1, nullable=False)
    mostrar_servicios = Column(Integer, default=1, nullable=False)
    permitir_reservas = Column(Integer, default=1, nullable=False)

    modalidades_entrega = Column(String(100), default="Domicilio,Recoger en tienda", nullable=True)
    costo_envio_base = Column(Float, default=0.0, nullable=False)
    mensaje_promocional = Column(String(500), nullable=True)
    condiciones_servicio = Column(Text, nullable=True)

    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)

    def save(self):
        session.add(self)
        session.commit()

    def update(self):
        self.updated_at = datetime.now()
        session.commit()

    @classmethod
    def get_by_empresa(cls, id_empresa):
        return session.query(cls).filter_by(id_empresa=id_empresa).first()

    @classmethod
    def get_by_slug(cls, slug):
        if not slug:
            return None
        return session.query(cls).filter_by(slug=str(slug).strip().lower()).first()

    @classmethod
    def get_or_create_for_empresa(cls, empresa):
        cfg = cls.get_by_empresa(empresa.id)
        if cfg:
            return cfg
        base_slug = slugify_empresa(empresa.nombre, empresa.id)
        slug_candidato = base_slug
        contador = 1
        while session.query(cls).filter_by(slug=slug_candidato).first() is not None:
            contador += 1
            slug_candidato = f"{base_slug}-{contador}"

        cfg = cls(
            id_empresa=empresa.id,
            slug=slug_candidato,
            activo=1,
            nombre_publico=empresa.nombre,
            eslogan=f"Bienvenido al portal oficial de {empresa.nombre}",
            descripcion=f"Catálogo en línea, pedidos y reservas de servicios de {empresa.nombre}.",
            color_primario="#2563eb",
            color_secundario="#1e40af",
            telefono_contacto=empresa.telefono or "",
            email_contacto=empresa.email or "",
            whatsapp=empresa.telefono or "",
            direccion=empresa.direccion or "",
            horario_atencion="Lunes a Sábado: 8:00 AM - 6:00 PM",
            redes_sociales=json.dumps({"instagram": "", "facebook": "", "tiktok": "", "web": ""}),
            mostrar_catalogo=1,
            mostrar_precios=1,
            permitir_pedidos=1,
            mostrar_servicios=1,
            permitir_reservas=1,
            modalidades_entrega="Domicilio,Recoger en tienda",
            costo_envio_base=0.0,
            mensaje_promocional="Haz tus pedidos o agenda tus servicios en línea de forma rápida y segura."
        )
        session.add(cfg)
        session.commit()
        return cfg

    def to_dict(self):
        redes = {}
        if self.redes_sociales:
            try:
                redes = json.loads(self.redes_sociales) if isinstance(self.redes_sociales, str) else self.redes_sociales
            except Exception:
                redes = {}
        modalidades = [m.strip() for m in (self.modalidades_entrega or "Domicilio,Recoger en tienda").split(",") if m.strip()]
        return {
            "id": self.id,
            "id_empresa": self.id_empresa,
            "slug": self.slug,
            "activo": bool(self.activo),
            "nombre_publico": self.nombre_publico,
            "eslogan": self.eslogan or "",
            "descripcion": self.descripcion or "",
            "logo_url": self.logo_url or "",
            "portada_url": self.portada_url or "",
            "color_primario": self.color_primario or "#2563eb",
            "color_secundario": self.color_secundario or "#1e40af",
            "telefono_contacto": self.telefono_contacto or "",
            "telefono_publico": self.telefono_contacto or "",
            "email_contacto": self.email_contacto or "",
            "correo_publico": self.email_contacto or "",
            "whatsapp": self.whatsapp or "",
            "direccion": self.direccion or "",
            "direccion_publica": self.direccion or "",
            "horario_atencion": self.horario_atencion or "",
            "redes_sociales": redes,
            "mostrar_catalogo": bool(self.mostrar_catalogo),
            "catalogo_activo": bool(self.mostrar_catalogo),
            "mostrar_precios": bool(self.mostrar_precios),
            "mostrar_stock": True,
            "permitir_pedidos": bool(self.permitir_pedidos),
            "carrito_activo": bool(self.permitir_pedidos),
            "mostrar_servicios": bool(self.mostrar_servicios),
            "servicios_activos": bool(self.mostrar_servicios),
            "permitir_reservas": bool(self.permitir_reservas),
            "reservas_activas": bool(self.permitir_reservas),
            "modalidades_entrega": modalidades,
            "modalidades_entrega_str": self.modalidades_entrega or "Domicilio,Recoger en tienda",
            "permitir_entrega_domicilio": "Domicilio" in modalidades,
            "permitir_recogida_tienda": ("Recoger en tienda" in modalidades or "Tienda" in modalidades),
            "costo_envio_base": float(self.costo_envio_base or 0.0),
            "mensaje_promocional": self.mensaje_promocional or "",
            "historia": self.mensaje_promocional or "",
            "banner_url": self.portada_url or "",
            "condiciones_servicio": self.condiciones_servicio or "",
            "politicas_terminos": self.condiciones_servicio or "",
        }
