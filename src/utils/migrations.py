from datetime import datetime
from sqlalchemy import text, inspect
from src.models import engine, Base, session


class DatabaseMigrations:
    """
    Gestor de migraciones de esquema versionadas y no destructivas (compatible con MySQL y SQLite).
    - Registra cada migración aplicada en la tabla `schema_migrations`.
    - Nunca ejecuta actualizaciones masivas destructivas ni asigna `id_empresa = 1` automáticamente
      durante el arranque normal del servidor.
    """

    MIGRACIONES = [
        ("2026_01_base_tables", "Creación de tablas base y tablas del Portal de Clientes"),
        ("2026_02_empresas_multitenant", "Adición de razon_social, created_at y campos de membresía en empresas"),
        ("2026_03_usuarios_superadmin", "Adición de es_super_admin, sesion_version y foto en usuarios"),
        ("2026_04_categorias_multitenant", "Adición de id_empresa, descripcion y estado en categorias"),
        ("2026_05_productos_portal", "Adición de campos de publicación del Portal de Clientes en productos"),
        ("2026_06_transacciones_pedidos", "Soporte de id_pedido y anulabilidad de id_factura en transacciones_pago"),
        ("2026_07_catalogos_base", "Semilla no destructiva de roles y métodos de pago estándar"),
    ]

    @staticmethod
    def _asegurar_tabla_versiones():
        with engine.connect() as conn:
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS schema_migrations (
                    version VARCHAR(80) PRIMARY KEY,
                    descripcion VARCHAR(255) NOT NULL,
                    applied_at VARCHAR(40) NOT NULL
                )
            """))
            conn.commit()

    @staticmethod
    def obtener_migraciones_aplicadas():
        DatabaseMigrations._asegurar_tabla_versiones()
        with engine.connect() as conn:
            rows = conn.execute(text("SELECT version, descripcion, applied_at FROM schema_migrations ORDER BY version ASC")).fetchall()
            return [{"version": r[0], "descripcion": r[1], "applied_at": r[2]} for r in rows]

    @staticmethod
    def _registrar_version(version, descripcion):
        ahora = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with engine.connect() as conn:
            existe = conn.execute(
                text("SELECT version FROM schema_migrations WHERE version = :v"),
                {"v": version}
            ).fetchone()
            if not existe:
                conn.execute(
                    text("INSERT INTO schema_migrations (version, descripcion, applied_at) VALUES (:v, :d, :a)"),
                    {"v": version, "d": descripcion, "a": ahora}
                )
                conn.commit()

    @staticmethod
    def ejecutar_migraciones():
        """Ejecuta migraciones estructurales seguras e idempotentes al iniciar la aplicación."""
        try:
            DatabaseMigrations._asegurar_tabla_versiones()
            Base.metadata.create_all(engine)

            inspector = inspect(engine)
            tablas = inspector.get_table_names()

            with engine.connect() as conn:
                def add_col(tabla, col, tipo):
                    if tabla not in tablas:
                        return
                    cols_actuales = [c["name"] for c in inspector.get_columns(tabla)]
                    if col not in cols_actuales:
                        try:
                            conn.execute(text(f"ALTER TABLE {tabla} ADD COLUMN {col} {tipo}"))
                            conn.commit()
                        except Exception:
                            pass

                # 1. Empresas
                add_col("empresas", "razon_social", "VARCHAR(200) NULL")
                add_col("empresas", "created_at", "DATETIME NULL")
                add_col("empresas", "plan_membresia", "VARCHAR(60) DEFAULT 'Plan PYME Mensual'")
                add_col("empresas", "precio_membresia", "FLOAT DEFAULT 19900.0")
                add_col("empresas", "estado_membresia", "VARCHAR(30) DEFAULT 'Activa'")
                add_col("empresas", "fecha_inicio_membresia", "DATETIME NULL")
                add_col("empresas", "fecha_vencimiento_membresia", "DATETIME NULL")
                add_col("empresas", "auto_renovacion", "INTEGER DEFAULT 1")

                # 2. Usuarios
                add_col("usuarios", "username", "VARCHAR(50) NULL")
                add_col("usuarios", "banco", "VARCHAR(100) NULL")
                add_col("usuarios", "tipo_cuenta", "VARCHAR(50) NULL")
                add_col("usuarios", "numero_cuenta", "VARCHAR(50) NULL")
                add_col("usuarios", "fecha_nacimiento", "VARCHAR(20) NULL")
                add_col("usuarios", "lugar_residencia", "VARCHAR(200) NULL")
                add_col("usuarios", "estado_civil", "VARCHAR(50) NULL")
                add_col("usuarios", "numero_hijos", "INTEGER DEFAULT 0")
                add_col("usuarios", "sesion_version", "INTEGER DEFAULT 1")
                add_col("usuarios", "foto", "LONGTEXT NULL")
                add_col("usuarios", "es_super_admin", "INTEGER DEFAULT 0")

                # 3. Categorías multi-empresa
                add_col("categorias", "descripcion", "VARCHAR(255) NULL")
                add_col("categorias", "estado", "VARCHAR(20) DEFAULT 'Activo'")
                add_col("categorias", "id_empresa", "INTEGER NULL")

                # 4. Clientes
                add_col("clientes", "apellido", "VARCHAR(100) DEFAULT ''")
                add_col("clientes", "codigo", "VARCHAR(50) NULL")
                add_col("clientes", "tipo_documento", "VARCHAR(20) DEFAULT 'CC'")
                add_col("clientes", "estado", "VARCHAR(20) DEFAULT 'Activo'")
                add_col("clientes", "id_empresa", "INTEGER NULL")

                # 5. Proveedores
                add_col("proveedores", "codigo", "VARCHAR(50) NULL")
                add_col("proveedores", "contacto", "VARCHAR(100) DEFAULT ''")
                add_col("proveedores", "estado", "VARCHAR(20) DEFAULT 'Activo'")
                add_col("proveedores", "id_empresa", "INTEGER NULL")

                # 6. Productos (incluyendo campos de Portal de Clientes)
                add_col("productos", "id_proveedor", "INTEGER NULL")
                add_col("productos", "costo", "FLOAT DEFAULT 0.0")
                add_col("productos", "estado", "VARCHAR(20) DEFAULT 'Activo'")
                add_col("productos", "imagen", "LONGTEXT NULL")
                add_col("productos", "id_empresa", "INTEGER NULL")
                add_col("productos", "publicado_portal", "INTEGER DEFAULT 1")
                add_col("productos", "descripcion_publica", "VARCHAR(500) NULL")
                add_col("productos", "imagen_publica", "LONGTEXT NULL")
                add_col("productos", "destacado", "INTEGER DEFAULT 0")
                add_col("productos", "precio_publico", "FLOAT NULL")
                add_col("productos", "disponible_portal", "INTEGER DEFAULT 1")

                # 7. Facturas y Compras
                add_col("facturas", "estado", "VARCHAR(20) DEFAULT 'Emitida'")
                add_col("facturas", "id_empresa", "INTEGER NULL")
                add_col("facturas", "pasarela", "VARCHAR(50) NULL")
                add_col("facturas", "referencia_pago", "VARCHAR(100) NULL")

                add_col("compras", "estado", "VARCHAR(20) DEFAULT 'Completada'")
                add_col("compras", "id_empresa", "INTEGER NULL")
                add_col("compras", "id_metodo_pago", "INTEGER DEFAULT 1")
                add_col("compras", "metodo_pago", "VARCHAR(100) DEFAULT 'Efectivo'")
                add_col("compras", "referencia_pago", "VARCHAR(100) NULL")

                # 8. Métodos de pago y Transacciones de pago
                add_col("metodos_pago", "tipo", "VARCHAR(30) DEFAULT 'manual'")
                add_col("metodos_pago", "pasarela", "VARCHAR(30) NULL")
                add_col("metodos_pago", "id_terminal_defecto", "INTEGER NULL")
                add_col("metodos_pago", "id_empresa", "INTEGER NULL")
                add_col("metodos_pago", "activo", "INTEGER DEFAULT 1")

                add_col("transacciones_pago", "id_pedido", "INTEGER NULL")

                # En MySQL permitir que id_factura sea NULL cuando el pago corresponde a un pedido del portal
                if "mysql" in str(engine.url):
                    try:
                        conn.execute(text("ALTER TABLE transacciones_pago MODIFY COLUMN id_factura INTEGER NULL"))
                        conn.commit()
                    except Exception:
                        pass

            DatabaseMigrations._sembrar_catalogos_base()

            for ver, desc in DatabaseMigrations.MIGRACIONES:
                DatabaseMigrations._registrar_version(ver, desc)

        except Exception as e:
            print(f"[migrations] Advertencia durante verificación de esquema: {e}")

    @staticmethod
    def _sembrar_catalogos_base():
        """Crea únicamente roles y métodos de pago esenciales si no existen (no crea empresas ficticias)."""
        try:
            from src.models.roles import Roles
            from src.models.metodos_pago import MetodosPago
            from src.models.categorias import Categorias

            roles_base = [
                (1, "Administrador", "Gestión administrativa de la empresa activa"),
                (2, "Vendedor", "Operaciones comerciales, ventas, clientes y pedidos"),
                (3, "Almacenista", "Gestión de inventario, productos, proveedores y compras"),
            ]
            for r_id, r_nom, r_desc in roles_base:
                if not session.query(Roles).filter_by(id=r_id).first():
                    session.add(Roles(id=r_id, nombre=r_nom, descripcion=r_desc))
            session.commit()

            if session.query(MetodosPago).count() == 0:
                metodos = [
                    MetodosPago(nombre="Efectivo", descripcion="Pago en efectivo o contraentrega", tipo="manual", activo=1),
                    MetodosPago(nombre="Tarjeta Débito", descripcion="Cobro con tarjeta débito", tipo="datafono", pasarela="bold", activo=1),
                    MetodosPago(nombre="Tarjeta Crédito", descripcion="Cobro con tarjeta crédito", tipo="datafono", pasarela="bold", activo=1),
                    MetodosPago(nombre="Transferencia / PSE", descripcion="Pago electrónico vía link de pasarela", tipo="link_pago", pasarela="wompi", activo=1),
                ]
                session.add_all(metodos)
                session.commit()

            if session.query(Categorias).count() == 0:
                cats = [
                    Categorias(nombre="General", descripcion="Categoría general de productos", estado="Activo", id_empresa=None),
                    Categorias(nombre="Tecnología", descripcion="Equipos y accesorios tecnológicos", estado="Activo", id_empresa=None),
                    Categorias(nombre="Alimentos y Bebidas", descripcion="Productos de consumo", estado="Activo", id_empresa=None),
                    Categorias(nombre="Hogar y Oficina", descripcion="Artículos para hogar y papelería", estado="Activo", id_empresa=None),
                ]
                session.add_all(cats)
                session.commit()
        except Exception:
            session.rollback()

    @staticmethod
    def auditar_calidad_datos():
        """
        Inspecciona la base de datos e identifica registros huérfanos (`id_empresa IS NULL`)
        o posibles inconsistencias sin alterar destructivamente los datos comerciales.
        """
        reporte = {"huerfanos": {}, "migraciones_aplicadas": DatabaseMigrations.obtener_migraciones_aplicadas()}
        tablas_tenant = ["clientes", "proveedores", "productos", "facturas", "compras"]
        with engine.connect() as conn:
            for t in tablas_tenant:
                try:
                    cnt = conn.execute(text(f"SELECT COUNT(*) FROM {t} WHERE id_empresa IS NULL")).scalar()
                    reporte["huerfanos"][t] = int(cnt or 0)
                except Exception:
                    reporte["huerfanos"][t] = 0
        return reporte
