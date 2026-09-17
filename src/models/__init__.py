import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, scoped_session, declarative_base

db_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "pymes.db"))
default_sqlite_url = f"sqlite:///{db_path}"

db_url = os.environ.get("DATABASE_URL")

if db_url:
    try:
        engine = create_engine(db_url, connect_args={"connect_timeout": 2} if "mysql" in db_url else {})
        with engine.connect() as conn:
            pass
    except Exception as e:
        print(f"No se pudo conectar a MySQL/DATABASE_URL ({e}), usando SQLite por defecto en {db_path}")
        engine = create_engine(default_sqlite_url)
else:
    engine = create_engine(default_sqlite_url)

Session = sessionmaker(bind=engine)
session = scoped_session(Session)
Base = declarative_base()

# Importar todos los modelos para registrar las tablas en Base.metadata y resolver ForeignKeys
from src.models.roles import Roles
from src.models.usuarios import Usuarios
from src.models.empresas import Empresas
from src.models.usuario_empresas import UsuarioEmpresas
from src.models.categorias import Categorias
from src.models.proveedores import Proveedores
from src.models.productos import Productos
from src.models.clientes import Clientes
from src.models.metodos_pago import MetodosPago
from src.models.facturas import Facturas
from src.models.detalle_facturas import DetalleFacturas
from src.models.compras import Compras
from src.models.detalle_compras import DetalleCompras
from src.models.movimiento_inventario import MovimientosInventario
