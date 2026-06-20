import os
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.engine import make_url
import sqlite3

# Get DB_URL from env, default to sqlite
DB_URL = os.getenv("DB_URL", "sqlite:////runtime/data/db/app.sqlite")

# Prepare connect args and ensure SQLite path exists
connect_args = {}
url = make_url(DB_URL)
if url.get_backend_name() == "sqlite":
    # Ensure directory exists so SQLite can create the file
    db_path = url.database
    if db_path and db_path != ":memory:":
        db_dir = os.path.dirname(db_path) or "."
        os.makedirs(db_dir, exist_ok=True)
        # If DB file doesn't exist, initialize an empty SQLite file so engine can connect
        if not os.path.exists(db_path):
            conn = sqlite3.connect(db_path)
            conn.close()
    connect_args = {"check_same_thread": False, "timeout": 30}

engine = create_engine(DB_URL, connect_args=connect_args)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
