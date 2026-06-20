import os
import sqlite3
from sqlalchemy import create_engine
from sqlalchemy.engine import make_url
from sqlalchemy.orm import sessionmaker, declarative_base

DB_URL = os.getenv("DB_URL", "sqlite:////runtime/data/db/app.sqlite")

connect_args = {}
url = make_url(DB_URL)
if url.get_backend_name() == "sqlite":
    db_path = url.database
    if db_path and db_path != ":memory:":
        db_dir = os.path.dirname(db_path) or "."
        os.makedirs(db_dir, exist_ok=True)
        if not os.path.exists(db_path):
            conn = sqlite3.connect(db_path)
            conn.close()
    connect_args = {"check_same_thread": False, "timeout": 30}

engine = create_engine(DB_URL, connect_args=connect_args)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()
