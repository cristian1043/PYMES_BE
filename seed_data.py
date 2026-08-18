import os
import sys

# Configurar salida UTF-8 para evitar errores de codificación en Windows
sys.stdout.reconfigure(encoding='utf-8')

# Agregar src al PYTHONPATH
sys.path.append(os.path.abspath(os.path.dirname(__file__)))

from src.models import Base, engine, session
from src.models.roles import Roles
from src.models.metodos_pago import MetodosPago
from src.models.categorias import Categorias
from src.models.empresas import Empresas
from src.models.usuarios import Usuarios
from src.models.usuario_empresas import UsuarioEmpresas
from src.models.clientes import Clientes
from src.models.proveedores import Proveedores
from src.models.productos import Productos
from src.models.facturas import Facturas
from src.models.compras import Compras
from werkzeug.security import generate_password_hash

def limpiar_y_sembrar_datos():
    """Limpia empresas antiguas de prueba y garantiza exactamente 4 empresas oficiales con datos limpios."""
    print("[+] Limpiando y preparando base de datos...")
    Base.metadata.create_all(bind=engine)

    # 1. Roles
    roles_def = [
        (1, "Administrador", "Acceso total al sistema"),
        (2, "Vendedor", "Gestión de ventas y clientes"),
        (3, "Almacenista", "Gestión de compras e inventario")
    ]
    for r_id, nombre, desc in roles_def:
        existente = session.query(Roles).filter_by(id=r_id).first()
        if not existente:
            r = Roles()
            r.id = r_id
            r.nombre = nombre
            r.descripcion = desc
            session.add(r)
    session.commit()
    print("[OK] Roles cargados.")

    # 2. Métodos de Pago
    metodos_def = [
        (1, "Efectivo"),
        (2, "Tarjeta de Crédito / Débito"),
        (3, "Transferencia Bancaria / Nequi"),
        (4, "Crédito Comercial (30 Días)")
    ]
    for m_id, nombre in metodos_def:
        existente = session.query(MetodosPago).filter_by(id=m_id).first()
        if not existente:
            m = MetodosPago()
            m.id = m_id
            m.nombre = nombre
            session.add(m)
    session.commit()
    print("[OK] Métodos de pago cargados.")

    # 3. Limpieza de Empresas Viejas de Prueba
    nits_oficiales = ["901234567-1", "900999111-2", "800555444-3", "901888777-4"]
    empresas_viejas = session.query(Empresas).filter(Empresas.nit.notin_(nits_oficiales)).all()
    for ev in empresas_viejas:
        session.query(UsuarioEmpresas).filter_by(empresa_id=ev.id).delete()
        session.delete(ev)
    session.commit()
    print(f"[OK] Se eliminaron {len(empresas_viejas)} empresas antiguas de pruebas previas.")

    # 4. Crear/Verificar las 4 Empresas Oficiales
    empresas_def = [
        ("901234567-1", "Comercializadora PYMES S.A.S.", "Calle 100 # 15-45, Bogotá", "6015551234", "contacto@pymes.com.co"),
        ("900999111-2", "Tecnología e Innovación Pyme S.A.", "Av. El Dorado # 68-90, Bogotá", "6013214567", "contacto@tecnoinnova.com"),
        ("800555444-3", "Distribuciones del Caribe Ltda.", "Carrera 43 # 70-15, Barranquilla", "6053851234", "info@discaribe.com.co"),
        ("901888777-4", "Servicios Integrales PYME S.A.S.", "Calle 10 # 42-28, Medellín", "6044448899", "contacto@servipyme.com")
    ]
    emp_objs = []
    for nit, nom, dir_, tel, ema in empresas_def:
        emp = session.query(Empresas).filter_by(nit=nit).first()
        if not emp:
            emp = Empresas()
            emp.nit = nit
            emp.nombre = nom
            emp.direccion = dir_
            emp.telefono = tel
            emp.email = ema
            emp.estado = "Activo"
            session.add(emp)
            session.commit()
        emp_objs.append(emp)
    print("[OK] Exactamente 4 Empresas Oficiales listas.")

    # 5. Usuarios y Vinculaciones
    usuarios_def = [
        ("CC", "1000000001", "Admin Global", "Sistema", "admin@pymesoft.com", "admin", 1),
        ("CC", "1018223344", "Cristian", "García", "cristian@pymes.com", "cristian", 1),
        ("CC", "1020304050", "Laura", "Martínez", "laura@pymes.com", "laura", 2),
        ("CC", "1030405060", "Carlos", "Rodríguez", "carlos@pymes.com", "carlos", 3)
    ]

    for doc_type, doc, nombre, apellido, email, username, id_rol in usuarios_def:
        u = session.query(Usuarios).filter_by(email=email).first()
        if not u:
            u = Usuarios()
            u.tipo_documento = doc_type
            u.documento = doc
            u.nombre = nombre
            u.apellido = apellido
            u.telefono = "3001234567"
            u.email = email
            u.username = username
            u.password_hash = generate_password_hash("123456")
            u.id_rol = id_rol
            u.estado = "Activo"
            session.add(u)
            session.commit()

        # Vinculaciones específicas por empresa
        for idx, e in enumerate(emp_objs):
            v = session.query(UsuarioEmpresas).filter_by(usuario_id=u.id, empresa_id=e.id).first()
            if not v:
                v = UsuarioEmpresas()
                v.usuario_id = u.id
                v.empresa_id = e.id
                
                # admin@pymesoft.com y cristian@pymes.com son Administradores en todas
                if u.email in ["admin@pymesoft.com", "cristian@pymes.com"]:
                    # En la empresa 2 Cristian actúa como Vendedor para probar cambio de rol por empresa
                    if u.email == "cristian@pymes.com" and idx == 1:
                        v.rol_id = 2 # Vendedor
                    else:
                        v.rol_id = 1 # Administrador
                else:
                    v.rol_id = u.id_rol

                v.estado = "Activo"
                session.add(v)
                session.commit()

    print("[OK] Usuarios y vinculaciones verificados para las 4 empresas.")

    # 6. Categorías
    categorias_def = [
        ("Tecnología y Equipos", "Computadores, accesorios y electrónica de oficina"),
        ("Papelería y Útiles", "Suministros de papelería, impresión y escritura"),
        ("Mobiliario de Oficina", "Escritorios, sillas ergonómicas y estantería"),
        ("Insumos de Limpieza", "Productos de aseo y desinfección empresarial"),
        ("Servicios Técnicos", "Mantenimiento, soporte y asesoría especializada")
    ]
    cat_objs = []
    for nom, desc in categorias_def:
        cat = session.query(Categorias).filter_by(nombre=nom).first()
        if not cat:
            cat = Categorias()
            cat.nombre = nom
            cat.descripcion = desc
            session.add(cat)
            session.commit()
        cat_objs.append(cat)
    print("[OK] Categorías cargadas.")

    # 7. Productos
    productos_def = [
        ("Laptop Lenovo ThinkPad i7", "16GB RAM, 512GB SSD, pantalla 14 pulgadas", 3850000.0, 15, cat_objs[0].id, "PROD-001", "UND"),
        ("Monitor Dell 27 4K", "Ultra HD IPS 60Hz con conexión USB-C", 1450000.0, 22, cat_objs[0].id, "PROD-002", "UND"),
        ("Teclado Mecánico Inalámbrico", "Switch Brown con iluminación RGB", 280000.0, 45, cat_objs[0].id, "PROD-003", "UND"),
        ("Mouse Ergonómico Logitech MX", "Sensor 4000 DPI con batería recargable", 320000.0, 30, cat_objs[0].id, "PROD-004", "UND"),
        ("Impresora Multifuncional Epson", "Sistema continuo de tinta ecotank", 950000.0, 12, cat_objs[0].id, "PROD-005", "UND"),
        ("Silla Ergonómica Ejecutiva", "Malla transpirable con soporte lumbar", 680000.0, 18, cat_objs[2].id, "PROD-006", "UND"),
        ("Escritorio Modulable L", "Madera aglomerada 140x120 cm acabado roble", 540000.0, 8, cat_objs[2].id, "PROD-007", "UND"),
        ("Caja Papel Carta (5 resmas)", "Papel multipropósito 75g de alta blancura", 125000.0, 60, cat_objs[1].id, "PROD-008", "CAJA"),
        ("Paquete Lapiceros Gel (x12)", "Tinta negra 0.7mm secado rápido", 24000.0, 100, cat_objs[1].id, "PROD-009", "PAQ"),
        ("Archivador Metálico 4 Gavetas", "Cerradura central y rieles telescópicos", 490000.0, 6, cat_objs[2].id, "PROD-010", "UND"),
        ("Disco Duro Externo 2TB", "USB 3.0 para copias de seguridad", 310000.0, 25, cat_objs[0].id, "PROD-011", "UND"),
        ("Hub USB-C 7 en 1", "HDMI 4K, Lectores SD y passthrough 100W", 175000.0, 40, cat_objs[0].id, "PROD-012", "UND"),
        ("Kit de Aseo Desinfectante", "Jabón líquido, gel antibacterial y paños", 85000.0, 50, cat_objs[3].id, "PROD-013", "KIT"),
        ("Destruidora de Papel Corte Cruzado", "Capacidad 10 hojas continuas", 420000.0, 10, cat_objs[1].id, "PROD-014", "UND"),
        ("Proyector Epson Full HD", "3400 lúmenes con entrada HDMI", 210000.0, 5, cat_objs[0].id, "PROD-015", "UND")
    ]
    for nom, desc, prec, st, c_id, cod, un in productos_def:
        p = session.query(Productos).filter_by(nombre=nom).first()
        if not p:
            p = Productos()
            p.nombre = nom
            p.descripcion = desc
            p.precio = prec
            p.stock = st
            p.id_categoria = c_id
            p.codigo = cod
            p.unidad_medida = un
            session.add(p)
    session.commit()
    print("[OK] Productos cargados (15 productos).")

    # 8. Clientes
    clientes_def = [
        ("CC", "1015432109", "Juan Carlos", "Pérez Gómez", "juan.perez@gmail.com", "3104567890", "Calle 45 # 12-34"),
        ("NIT", "900888777-2", "Inversiones del Norte S.A.S.", "", "contacto@inversionesnorte.com", "6017894561", "Av. El Dorado # 68-90"),
        ("CC", "1026549870", "María Fernanda", "López Rincón", "mafe.lopez@hotmail.com", "3159876543", "Carrera 7 # 45-12"),
        ("CC", "1032165498", "Andrés Felipe", "Torres Castro", "andres.torres@outlook.com", "3001234567", "Calle 127 # 19-45"),
        ("NIT", "800123999-5", "Distribuidora Nacional Ltda.", "", "compras@disnacional.co", "6013216548", "Calle 13 # 38-50"),
        ("CC", "1045987321", "Diana Marcela", "Ramírez Silva", "diana.ramirez@yahoo.com", "3186549870", "Carrera 15 # 93-20"),
        ("CC", "1056473829", "Santiago", "Mendoza Morales", "santiago.mendoza@gmail.com", "3127894561", "Calle 80 # 68-15"),
        ("CC", "1067382910", "Camila", "Vargas Suárez", "camila.vargas@hotmail.com", "3164561230", "Carrera 9 # 116-30"),
        ("NIT", "901456321-8", "Soluciones Digitales PYME", "", "gerencia@solucionespyme.com", "6018901234", "Calle 100 # 19-61"),
        ("CC", "1078901234", "Héctor Mario", "Bermúdez Ríos", "hector.bermudez@gmail.com", "3112345678", "Calle 53 # 24-80"),
        ("CC", "1089012345", "Patricia", "Gutiérrez Niño", "patricia.gutierrez@outlook.com", "3178901234", "Carrera 50 # 100-15"),
        ("CC", "1090123456", "Gustavo Adolfo", "Sánchez Vega", "gustavo.sanchez@gmail.com", "3145678901", "Calle 170 # 15-40")
    ]
    for doc_t, doc, nom, ape, ema, tel, dir_ in clientes_def:
        c = session.query(Clientes).filter_by(documento=doc).first()
        if not c:
            c = Clientes()
            c.tipo_documento = doc_t
            c.documento = doc
            c.nombre = nom
            if hasattr(c, 'apellido'):
                c.apellido = ape
            c.email = ema
            c.telefono = tel
            c.direccion = dir_
            session.add(c)
    session.commit()
    print("[OK] Clientes cargados (12 clientes).")

    # 9. Proveedores
    proveedores_def = [
        ("900111222-3", "Mayorista Tecnológico de Colombia", "Carlos Alberto Ruiz", "6014445566", "ventas@mayortecno.com", "Calle 26 # 69-76"),
        ("890999888-1", "Distribuidora de Papelería Panamericana", "Esperanza Gómez", "6013332211", "contacto@panapapel.com.co", "Calle 12 # 34-56"),
        ("901333444-5", "Muebles y Diseños Ergonómicos S.A.", "Fernando Jaramillo", "6017778899", "comercial@mueblesergo.com", "Carrera 68 # 18-20"),
        ("900555666-7", "Suministros de Limpieza Industrial", "Luz Marina Botero", "6018889900", "info@limpiezaindustrial.co", "Calle 63 # 45-30"),
        ("901666777-9", "Importaciones Globales de Electrónica", "Jorge Eliécer Gaitán", "6012223344", "importaciones@globalelec.com", "Autopista Norte # 145-80")
    ]
    for nit, nom, cont, tel, ema, dir_ in proveedores_def:
        prov = session.query(Proveedores).filter_by(nit=nit).first()
        if not prov:
            prov = Proveedores()
            prov.nit = nit
            prov.nombre = nom
            if hasattr(prov, 'contacto'):
                prov.contacto = cont
            prov.telefono = tel
            prov.email = ema
            prov.direccion = dir_
            session.add(prov)
    session.commit()
    print("[OK] Proveedores cargados (5 proveedores).")

    # 10. Facturas de Prueba (12 facturas para establecer múltiples páginas de paginación)
    facturas_def = [
        ("FAC-001", 3850000.0, 731500.0, 4581500.0, 1, 1, 1),
        ("FAC-002", 1450000.0, 275500.0, 1725500.0, 2, 2, 2),
        ("FAC-003", 600000.0, 114000.0, 714000.0, 3, 3, 1),
        ("FAC-004", 950000.0, 180500.0, 1130500.0, 4, 1, 2),
        ("FAC-005", 280000.0, 53200.0, 333200.0, 5, 2, 1),
        ("FAC-006", 680000.0, 129200.0, 809200.0, 6, 1, 2),
        ("FAC-007", 540000.0, 102600.0, 642600.0, 7, 3, 1),
        ("FAC-008", 125000.0, 23750.0, 148750.0, 8, 1, 2),
        ("FAC-009", 490000.0, 93100.0, 583100.0, 9, 2, 1),
        ("FAC-010", 310000.0, 58900.0, 368900.0, 10, 1, 2),
        ("FAC-011", 175000.0, 33250.0, 208250.0, 11, 3, 1),
        ("FAC-012", 420000.0, 79800.0, 499800.0, 12, 1, 2)
    ]
    for num, sub, iva, tot, id_c, id_m, id_u in facturas_def:
        f = session.query(Facturas).filter_by(numero=num).first()
        if not f:
            f = Facturas()
            f.numero = num
            f.subtotal = sub
            f.iva = iva
            f.descuento = 0.0
            f.total = tot
            f.id_cliente = id_c
            f.id_metodo_pago = id_m
            f.id_usuario = id_u
            session.add(f)
    session.commit()
    print("[OK] Facturas cargadas.")

    print("\n[SUCCESS] ¡Base de datos limpia y lista con exactamente 4 empresas oficiales y datos completos!")

if __name__ == '__main__':
    limpiar_y_sembrar_datos()
