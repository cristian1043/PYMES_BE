"""
Suite Integral de Pruebas Automatizadas de PYMESOFT (Fases 2, 3, 4, 7, 8, 9 y 10).
Cubre:
1. Aislamiento estricto multiempresa (Multi-Tenant Isolation) y pruebas negativas cross-tenant.
2. Separación de identidades (Administrativa vs Cliente Externo) y RBAC contextual por empresa.
3. Seguridad de contraseñas, recuperación sin fuga de OTP/token y revocación de sesiones.
4. Privacidad del catálogo público (no exposición de costo ni proveedor) y estado del portal.
5. Carrito validado en servidor, ciclo transaccional de pedidos, descuento/reverso de stock y facturación.
6. Agendamiento de servicios con bloqueo anti-doble-reserva por solapamiento horario.
7. Integración de cobros y simulación Sandbox para pedidos del portal.
8. Migraciones versionadas no destructivas (`schema_migrations`) y auditoría de integridad.
"""
import os
import sys
import tempfile
import pytest

# Configurar base de datos SQLite aislada para pruebas antes de importar la app
_tmp_db = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
_tmp_db.close()
os.environ["FLASK_ENV"] = "testing"
os.environ["DATABASE_URL"] = f"sqlite:///{_tmp_db.name}"
os.environ["JWT_SECRET_KEY"] = "test-jwt-secret-key-pymesoft-2026-secure-32b"
os.environ["PAGOS_ENC_KEY"] = "test-pagos-enc-key-pymesoft-2026-secure-32b"

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.app import app
from src.models import Base, engine, session
from src.models.roles import Roles
from src.models.usuarios import Usuarios
from src.models.empresas import Empresas
from src.models.usuario_empresas import UsuarioEmpresas
from src.models.categorias import Categorias
from src.models.proveedores import Proveedores
from src.models.productos import Productos
from src.models.clientes import Clientes
from src.models.portal_config import ConfiguracionPortal
from src.utils.security import hash_password
from src.utils.migrations import ejecutar_migraciones, auditar_calidad_datos, SchemaMigrations


@pytest.fixture(scope="module")
def client():
    app.config["TESTING"] = True
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)
    ejecutar_migraciones()

    # Semilla base para escenarios multiempresa
    for rid, rname in [(1, "Administrador"), (2, "Vendedor"), (3, "Almacenista")]:
        if not Roles.get_by_id(rid):
            session.add(Roles(id=rid, nombre=rname, descripcion=f"Rol {rname}"))
    session.commit()

    # Crear Empresa A y Empresa B
    emp_a = Empresas(
        nombre="Empresa Alfa S.A.S.",
        razon_social="Alfa Comercializadora S.A.S.",
        nit="900111222-1",
        direccion="Calle 10 # 20-30",
        telefono="3001112233",
        email="contacto@alfa.com",
        estado="Activo",
    )
    emp_b = Empresas(
        nombre="Empresa Beta Ltda.",
        razon_social="Beta Servicios Ltda.",
        nit="900333444-2",
        direccion="Carrera 50 # 60-70",
        telefono="3004445566",
        email="contacto@beta.com",
        estado="Activo",
    )
    session.add_all([emp_a, emp_b])
    session.commit()

    ConfiguracionPortal.get_or_create_for_empresa(emp_a)
    ConfiguracionPortal.get_or_create_for_empresa(emp_b)

    # Usuario 1: Admin en Empresa A, pero Vendedor en Empresa B (y sin acceso a una futura Empresa C)
    user_alfa = Usuarios(
        documento="10101010",
        tipo_documento="CC",
        nombre="Carlos",
        apellido="Alfa",
        email="carlos@alfa.com",
        username="carlos.alfa",
        password=hash_password("AdminAlfa123"),
        id_rol=1,
        es_super_admin=0,
        estado="Activo",
    )
    # Usuario 2: Exclusivo de Empresa B (Admin en B, sin vínculo en A)
    user_beta = Usuarios(
        documento="20202020",
        tipo_documento="CC",
        nombre="Diana",
        apellido="Beta",
        email="diana@beta.com",
        username="diana.beta",
        password=hash_password("AdminBeta123"),
        id_rol=1,
        es_super_admin=0,
        estado="Activo",
    )
    session.add_all([user_alfa, user_beta])
    session.commit()

    session.add_all([
        UsuarioEmpresas(usuario_id=user_alfa.id, empresa_id=emp_a.id, rol_id=1, estado="Activo"),
        UsuarioEmpresas(usuario_id=user_alfa.id, empresa_id=emp_b.id, rol_id=2, estado="Activo"),
        UsuarioEmpresas(usuario_id=user_beta.id, empresa_id=emp_b.id, rol_id=1, estado="Activo"),
    ])
    session.commit()

    # Categorías, Proveedores y Productos aislados por empresa
    cat_a = Categorias(nombre="Tecnología Alfa", id_empresa=emp_a.id, estado="Activo")
    cat_b = Categorias(nombre="Hogar Beta", id_empresa=emp_b.id, estado="Activo")
    prov_a = Proveedores(nombre="Mayorista Confidencial Alfa", nit="800111000-1", email="prov@alfa.com", id_empresa=emp_a.id)
    prov_b = Proveedores(nombre="Mayorista Confidencial Beta", nit="800111000-1", email="prov@alfa.com", id_empresa=emp_b.id)
    session.add_all([cat_a, cat_b, prov_a, prov_b])
    session.commit()

    prod_a = Productos(
        codigo="PROD-A-001",
        nombre="Portátil Empresarial Alfa",
        descripcion="Uso interno",
        descripcion_publica="Portátil de alto rendimiento con garantía de 1 año.",
        precio=2500000.0,
        precio_publico=2400000.0,
        costo=1800000.0,  # Dato confidencial que jamás debe exponerse en el portal público
        stock=10,
        id_categoria=cat_a.id,
        id_proveedor=prov_a.id,
        id_empresa=emp_a.id,
        publicado_portal=1,
        disponible_portal=1,
        destacado=1,
        estado="Activo",
    )
    prod_b = Productos(
        codigo="PROD-B-001",
        nombre="Silla Ergonómica Beta",
        descripcion="Silla ejecutiva",
        precio=600000.0,
        costo=350000.0,
        stock=5,
        id_categoria=cat_b.id,
        id_proveedor=prov_b.id,
        id_empresa=emp_b.id,
        publicado_portal=1,
        disponible_portal=1,
        estado="Activo",
    )
    session.add_all([prod_a, prod_b])
    session.commit()

    with app.test_client() as test_client:
        yield test_client


def _login_admin(client, email, password):
    res = client.post("/api/auth/login", json={"email": email, "password": password})
    assert res.status_code == 200
    return res.get_json()["access_token"]


# =========================================================================
# 1. PRUEBAS DE AISLAMIENTO MULTIEMPRESA Y AUTORIZACIÓN CONTEXTUAL
# =========================================================================
def test_aislamiento_multiempresa_y_bloqueo_cross_tenant(client):
    token_beta = _login_admin(client, "diana@beta.com", "AdminBeta123")
    headers_forzando_empresa_a = {
        "Authorization": f"Bearer {token_beta}",
        "X-Empresa-ID": "1",  # Diana NO pertenece a la Empresa 1 (Alfa)
    }

    # Diana intenta listar o manipular recursos enviando X-Empresa-ID=1
    res_prods = client.get("/api/productos/?empresa_id=1", headers=headers_forzando_empresa_a)
    assert res_prods.status_code == 403

    # Diana (operando en su Empresa 2) intenta leer o editar un producto de la Empresa 1 por ID
    headers_beta = {"Authorization": f"Bearer {token_beta}", "X-Empresa-ID": "2"}
    res_prod_ajeno = client.get("/api/productos/1", headers=headers_beta)
    assert res_prod_ajeno.status_code == 404

    res_edit_ajeno = client.put(
        "/api/productos/1",
        json={"nombre": "Sabotaje Cross-Tenant", "precio": 1.0},
        headers=headers_beta,
    )
    assert res_edit_ajeno.status_code == 404


def test_rol_contextual_por_empresa_evita_escalada_privilegios(client):
    """
    Carlos es Administrador (rol 1) en Empresa A, pero solo Vendedor (rol 2) en Empresa B.
    Cuando opera en Empresa B, NO debe poder ejecutar acciones exclusivas de Administrador en Empresa B.
    """
    token_carlos = _login_admin(client, "carlos@alfa.com", "AdminAlfa123")
    headers_carlos_en_b = {"Authorization": f"Bearer {token_carlos}", "X-Empresa-ID": "2"}

    # Intentar modificar la configuración general del portal de Empresa B siendo Vendedor en B -> 403
    res_cfg = client.put(
        "/api/portal/admin/configuracion",
        json={"nombre_publico": "Intento Escalada"},
        headers=headers_carlos_en_b,
    )
    assert res_cfg.status_code == 403


# =========================================================================
# 2. SEGURIDAD DE AUTENTICACIÓN, RECUPERACIÓN Y SEPARACIÓN DE IDENTIDADES
# =========================================================================
def test_recuperacion_password_no_expone_otp_ni_enumera_usuarios(client):
    # Correo existente
    res_ok = client.post("/api/auth/recuperar-password-solicitar", json={"identificador": "carlos@alfa.com"})
    assert res_ok.status_code == 200
    data_ok = res_ok.get_json()
    assert "codigo_otp" not in data_ok
    assert "token" not in data_ok
    assert "otp" not in str(data_ok).lower()

    # Correo inexistente devuelve exactamente el mismo código 200 y mensaje genérico
    res_no = client.post("/api/auth/recuperar-password-solicitar", json={"identificador": "noexiste@fantasma.com"})
    assert res_no.status_code == 200
    assert res_no.get_json()["mensaje"] == data_ok["mensaje"]


def test_separacion_estricta_identidad_cliente_vs_admin(client):
    # Registrar un cliente externo en el portal
    res_reg = client.post(
        "/api/portal/cliente/auth/register",
        json={
            "tipo_documento": "CC",
            "documento": "99887766",
            "nombre": "Laura",
            "apellido": "Cliente",
            "email": "laura.cliente@correo.com",
            "telefono": "3105556677",
            "direccion": "Av Siempre Viva 123",
            "ciudad": "Bogotá",
            "password": "ClienteSegura123",
            "id_empresa": 1,
        },
    )
    assert res_reg.status_code == 201
    token_cliente = res_reg.get_json()["access_token"]
    headers_cliente = {"Authorization": f"Bearer {token_cliente}", "X-Empresa-ID": "1"}

    # El cliente externo intenta acceder a endpoints administrativos con su JWT -> 403
    res_admin_usuarios = client.get("/api/usuarios/", headers=headers_cliente)
    assert res_admin_usuarios.status_code == 403

    res_admin_portal = client.get("/api/portal/admin/pedidos", headers=headers_cliente)
    assert res_admin_portal.status_code == 403

    # Un administrador intenta usar su JWT en endpoints exclusivos de cliente externo -> 403
    token_admin = _login_admin(client, "carlos@alfa.com", "AdminAlfa123")
    res_cli_perfil = client.get(
        "/api/portal/cliente/perfil",
        headers={"Authorization": f"Bearer {token_admin}"},
    )
    assert res_cli_perfil.status_code == 403


# =========================================================================
# 3. CATÁLOGO PÚBLICO, CARRITO VALIDADO, PEDIDOS E INVENTARIO
# =========================================================================
def test_catalogo_publico_no_expone_costo_ni_proveedor(client):
    cfg_a = ConfiguracionPortal.get_by_empresa(1)
    res = client.get(f"/api/portal/publico/{cfg_a.slug}/productos")
    assert res.status_code == 200
    productos = res.get_json()["productos"]
    assert len(productos) == 1
    p = productos[0]
    assert p["nombre"] == "Portátil Empresarial Alfa"
    assert p["precio"] == 2400000.0
    assert "costo" not in p
    assert "id_proveedor" not in p
    assert "proveedor_nombre" not in p


def test_flujo_completo_pedido_stock_cancelacion_y_facturacion(client):
    cfg_a = ConfiguracionPortal.get_by_empresa(1)
    res_login = client.post(
        "/api/portal/cliente/auth/login",
        json={"email": "laura.cliente@correo.com", "password": "ClienteSegura123", "id_empresa": 1},
    )
    token_cli = res_login.get_json()["access_token"]
    headers_cli = {"Authorization": f"Bearer {token_cli}"}

    # 1. Intentar validar carrito con un producto de OTRA empresa (Producto 2 pertenece a Empresa B) -> 400
    res_invalido = client.post(
        f"/api/portal/publico/{cfg_a.slug}/carrito/validar",
        json={"items": [{"id_producto": 2, "cantidad": 1}]},
    )
    assert res_invalido.status_code == 400

    # 2. Intentar pedir más stock del disponible (hay 10 en stock) -> 400
    res_sobrestock = client.post(
        f"/api/portal/publico/{cfg_a.slug}/carrito/validar",
        json={"items": [{"id_producto": 1, "cantidad": 99}]},
    )
    assert res_sobrestock.status_code == 400

    # 3. Crear pedido válido de 2 unidades en Empresa A
    res_ped = client.post(
        f"/api/portal/cliente/{cfg_a.slug}/pedidos",
        json={
            "items": [{"id_producto": 1, "cantidad": 2}],
            "modalidad_entrega": "Domicilio",
            "direccion_entrega": "Calle 80 # 10-20",
            "ciudad_entrega": "Bogotá",
            "telefono_contacto": "3105556677",
        },
        headers=headers_cli,
    )
    assert res_ped.status_code == 201
    pedido_data = res_ped.get_json()["pedido"]
    pedido_id = pedido_data["id"]
    assert pedido_data["total"] == 4800000.0

    # Verificar que el stock se descontó de 10 a 8
    prod_db = Productos.get_by_id(1)
    assert prod_db.stock == 8

    # 4. Simular cobro en pasarela Sandbox para el pedido
    res_cobro = client.post(
        f"/api/portal/cliente/{cfg_a.slug}/pedidos/{pedido_id}/cobros",
        json={"canal": "link"},
        headers=headers_cli,
    )
    assert res_cobro.status_code == 201
    cobro_id = res_cobro.get_json()["cobro"]["id"]

    res_sim = client.post(
        f"/api/portal/cliente/{cfg_a.slug}/pedidos/{pedido_id}/cobros/{cobro_id}/simular",
        json={"resultado": "APROBADA"},
        headers=headers_cli,
    )
    assert res_sim.status_code == 200
    assert res_sim.get_json()["pedido"]["estado_pago"] == "Pagado"

    # 5. Administrador confirma y genera factura oficial desde el pedido
    token_admin = _login_admin(client, "carlos@alfa.com", "AdminAlfa123")
    headers_admin = {"Authorization": f"Bearer {token_admin}", "X-Empresa-ID": "1"}
    res_est = client.put(
        f"/api/portal/admin/pedidos/{pedido_id}/estado",
        json={"estado": "Confirmado", "comentario": "Pago verificado y facturado", "generar_factura": True},
        headers=headers_admin,
    )
    assert res_est.status_code == 200
    ped_actualizado = res_est.get_json()["pedido"]
    assert ped_actualizado["id_factura"] is not None

    # 6. Cancelar el pedido revierte el stock de 8 nuevamente a 10
    res_canc = client.put(
        f"/api/portal/admin/pedidos/{pedido_id}/estado",
        json={"estado": "Cancelado", "comentario": "Reverso de prueba"},
        headers=headers_admin,
    )
    assert res_canc.status_code == 200
    session.expire_all()
    assert Productos.get_by_id(1).stock == 10


# =========================================================================
# 4. SERVICIOS Y RESERVAS CON CONTROL DE CONCURRENCIA (ANTI-DOBLE-RESERVA)
# =========================================================================
def test_agendamiento_servicio_y_bloqueo_doble_reserva(client):
    cfg_a = ConfiguracionPortal.get_by_empresa(1)
    token_admin = _login_admin(client, "carlos@alfa.com", "AdminAlfa123")
    headers_admin = {"Authorization": f"Bearer {token_admin}", "X-Empresa-ID": "1"}

    # Crear servicio en Empresa A
    res_srv = client.post(
        "/api/portal/admin/servicios",
        json={
            "nombre": "Mantenimiento Especializado",
            "categoria": "Soporte",
            "precio": 90000.0,
            "duracion_minutos": 60,
            "publicado": True,
            "disponible": True,
            "requiere_reserva": True,
        },
        headers=headers_admin,
    )
    assert res_srv.status_code == 201
    srv_id = res_srv.get_json()["servicio"]["id"]

    # Login de cliente y agendar para 2026-12-15 a las 10:00
    res_login = client.post(
        "/api/portal/cliente/auth/login",
        json={"email": "laura.cliente@correo.com", "password": "ClienteSegura123", "id_empresa": 1},
    )
    headers_cli = {"Authorization": f"Bearer {res_login.get_json()['access_token']}"}

    res_r1 = client.post(
        f"/api/portal/cliente/{cfg_a.slug}/reservas",
        json={
            "id_servicio": srv_id,
            "fecha_reserva": "2026-12-15",
            "hora_inicio": "10:00",
            "notas_cliente": "Primera cita",
        },
        headers=headers_cli,
    )
    assert res_r1.status_code == 201

    # Intentar agendar otra cita en el mismo horario (10:00 o 10:30 que se solapa con 10:00-11:00) -> 400
    res_r2 = client.post(
        f"/api/portal/cliente/{cfg_a.slug}/reservas",
        json={
            "id_servicio": srv_id,
            "fecha_reserva": "2026-12-15",
            "hora_inicio": "10:30",
            "notas_cliente": "Intento de solapamiento",
        },
        headers=headers_cli,
    )
    assert res_r2.status_code == 400


# =========================================================================
# 5. MIGRACIONES VERSIONADAS Y AUDITORÍA DE CALIDAD DE DATOS
# =========================================================================
def test_migraciones_versionadas_y_auditoria_datos(client):
    versiones = session.query(SchemaMigrations).all()
    assert len(versiones) >= 4
    reporte = auditar_calidad_datos()
    assert isinstance(reporte, dict)
    assert reporte.get("productos_stock_negativo") == 0
