from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
import pymysql

engine = create_engine("mysql+pymysql://root@localhost:3306/FacturApp_25T2_PY?charset=utf8mb4")

connection = engine.connect()

Session = sessionmaker(bind=engine)

session = Session()

Base = declarative_base()

Base.metadata.bind = engine