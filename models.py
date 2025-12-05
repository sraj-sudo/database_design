from sqlalchemy import create_engine, Column, Integer, String, DateTime, func, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, scoped_session

Base = declarative_base()

class ProdTable(Base):
    __tablename__ = "prod_table"
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), nullable=False)
    region = Column(String(50), nullable=True)   # sample filter column
    spec = Column(String(50), nullable=True)     # sample filter column
    notes = Column(Text, nullable=True)
    last_modified = Column(DateTime, server_default=func.now(), onupdate=func.now())

class TestTable(Base):
    __tablename__ = "test_table"
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), nullable=False)
    region = Column(String(50), nullable=True)
    spec = Column(String(50), nullable=True)
    notes = Column(Text, nullable=True)
    origin_system = Column(String(32), nullable=True)  # for replication metadata
    change_id = Column(String(64), nullable=True)
    last_modified = Column(DateTime, server_default=func.now(), onupdate=func.now())

def get_engine(sqlite_path: str):
    return create_engine(f"sqlite:///{sqlite_path}", echo=False, connect_args={'check_same_thread': False})

def get_session(engine):
    Session = scoped_session(sessionmaker(bind=engine))
    return Session
