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
