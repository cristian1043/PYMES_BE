from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

# Configuración de la conexión
DATABASE_URL = "mysql+pymysql://root@localhost:3306/FacturApp_25T2_PY?charset=utf8mb4"

# Motor de conexión
engine = create_engine(
    DATABASE_URL,
    echo=True,
    future=True
)

# Sesión
SessionLocal = sessionmaker(
    bind=engine,
    autoflush=False,
    autocommit=False
)

# Base para todos los modelos
Base = declarative_base()