# backend/db.py
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
# (opcional) si querés leer .env:
# from dotenv import load_dotenv; load_dotenv(); import os

# Si preferís .env, armá el string con os.getenv(...)
DATABASE_URL = "mysql+pymysql://Tomas:Tomas2016@127.0.0.1:3306/studyplanner"

engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,
    pool_recycle=3600,
    echo=False,
)

SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)
Base = declarative_base()

# 👇 ESTA función la usa FastAPI como “dependencia” para abrir/cerrar sesiones
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
