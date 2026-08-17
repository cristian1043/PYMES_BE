import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
import pymysql

db_url = os.environ.get("DATABASE_URL", "mysql+pymysql://root@localhost:3306/facturapp_25t2_py?charset=utf8mb4")

try:
    engine = create_engine(db_url, connect_args={"connect_timeout": 2} if "mysql" in db_url else {})
    with engine.connect() as conn:
        pass
except Exception:
    db_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "pymes.db"))
    engine = create_engine(f"sqlite:///{db_path}")

Session = sessionmaker(bind=engine)
session = Session()
Base = declarative_base()

