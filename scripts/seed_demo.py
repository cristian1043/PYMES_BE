"""
Script independiente de semillas de demostración (exclusivo para desarrollo y pruebas).
NUNCA se ejecuta automáticamente durante las consultas normales ni en producción.

Uso:
    python -m scripts.seed_demo
"""
import os
import sys
from datetime import datetime, timedelta

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.models import session
from src.models.empresas import Empresas, PRECIO_MEMBRESIA_COP, PLAN_MEMBRESIA_DEFAULT, DIAS_MEMBRESIA_CICLO
from src.models.usuarios import Usuarios
from src.models.usuario_empresas import UsuarioEmpresas
from src.models.categorias import Categorias
from src.models.productos import Productos
from src.models.servicios import Servicios
from src.models.portal_config import ConfiguracionPortal
from src.utils.security import hash_password
from src.utils.migrations import DatabaseMigrations


def ejecutar_seed_demo():
    if os.environ.get("FLASK_ENV", "").lower() == "production":
        raise RuntimeError("No se permite ejecutar semillas de demostración en producción.")

    DatabaseMigrations.ejecutar_migraciones()
    ahora = datetime.now()
    venc = ahora + timedelta(days=DIAS_MEMBRESIA_CICLO)

    # 1. Empresas de demostración
    emp1 = session.query(Empresas).filter_by(nit="900123456-1").first()
    if not emp1:
        emp1 = Empresas(
            nombre="Comercializadora Andina S.A.S.",
            razon_social="Comercializadora Andina S.A.S.",
            nit="900123456-1",
            direccion="Calle 100 # 15-20, Bogotá",
            telefono="3001234567",
            email="contacto@andina.co",
            estado="Activo",
            plan_membresia=PLAN_MEMBRESIA_DEFAULT,
            precio_membresia=PRECIO_MEMBRESIA_COP,
            estado_membresia="Activa",
            fecha_inicio_membresia=ahora,
            fecha_vencimiento_membresia=venc,
            auto_renovacion=1,
        )
        emp1.save()

    emp2 = session.query(Empresas).filter_by(nit="900987654-2").first()
    if not emp2:
        emp2 = Empresas(
            nombre="TecnoServicios del Valle S.A.S.",
            razon_social="TecnoServicios del Valle S.A.S.",
            nit="900987654-2",
            direccion="Av. 6N # 28-10, Cali",
            telefono="3159876543",
            email="info@tecnoservicios.co",
            estado="Activo",
            plan_membresia=PLAN_MEMBRESIA_DEFAULT,
            precio_membresia=PRECIO_MEMBRESIA_COP,
            estado_membresia="Activa",
            fecha_inicio_membresia=ahora,
            fecha_vencimiento_membresia=venc,
            auto_renovacion=1,
        )
        emp2.save()

    # 2. Configurar portales de clientes para ambas empresas
    ConfiguracionPortal.get_or_create_for_empresa(emp1)
    ConfiguracionPortal.get_or_create_for_empresa(emp2)

    # 3. Categorías y productos iniciales por empresa si no tienen
    cat1 = session.query(Categorias).filter_by(id_empresa=emp1.id, nombre="Tecnología").first()
    if not cat1:
        cat1 = Categorias(nombre="Tecnología", descripcion="Equipos de cómputo y accesorios", estado="Activo", id_empresa=emp1.id)
        cat1.create()

    if session.query(Productos).filter_by(id_empresa=emp1.id).count() == 0:
        p1 = Productos(
            codigo="AND-001",
            nombre="Monitor LED 24 Pulgadas FHD",
            descripcion="Monitor IPS 75Hz con entrada HDMI",
            descripcion_publica="Monitor IPS Full HD 24 pulgadas ideal para oficina y estudio.",
            unidad_medida="UND",
            precio=620000.0,
            precio_publico=620000.0,
            costo=450000.0,
            stock=15,
            id_categoria=cat1.id,
            estado="Activo",
            id_empresa=emp1.id,
            publicado_portal=1,
            disponible_portal=1,
            destacado=1,
        )
        p1.create()

    if session.query(Servicios).filter_by(id_empresa=emp1.id).count() == 0:
        s1 = Servicios(
            id_empresa=emp1.id,
            codigo="SRV-001",
            nombre="Mantenimiento Preventivo de Portátil",
            descripcion="Limpieza interna, cambio de pasta térmica y optimización de sistema operativo.",
            categoria="Soporte Técnico",
            precio=85000.0,
            duracion_minutos=60,
            condiciones="Traer cargador original del equipo.",
            estado="Activo",
            publicado=1,
            disponible=1,
            requiere_reserva=1,
        )
        s1.create()

    print(f"[seed_demo] Semillas de demostración listas: {emp1.nombre} (ID {emp1.id}) y {emp2.nombre} (ID {emp2.id}).")


if __name__ == "__main__":
    ejecutar_seed_demo()
