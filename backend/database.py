import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

DB_DIR = os.path.join(os.path.dirname(__file__), "data")
os.makedirs(DB_DIR, exist_ok=True)
DB_PATH = os.path.join(DB_DIR, "guestdb.sqlite")

engine = create_engine(f"sqlite:///{DB_PATH}", connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def init_db():
    from . import models
    Base.metadata.create_all(bind=engine)
    # Lightweight migration: add new columns if missing (SQLite only)
    with engine.connect() as conn:
        cols = [row[1] for row in conn.exec_driver_sql("PRAGMA table_info(guests)").fetchall()]
        def ensure(col_name: str, ddl: str):
            if col_name not in cols:
                conn.exec_driver_sql(f"ALTER TABLE guests ADD COLUMN {ddl}")
        ensure("middle_name", "middle_name TEXT")
        ensure("issue_date", "issue_date TEXT")
        ensure("phone_country_code", "phone_country_code TEXT")
        ensure("phone_number", "phone_number TEXT")
        ensure("deleted_at", "deleted_at DATETIME")
        ensure("first_name_norm", "first_name_norm TEXT")
        ensure("last_name_norm", "last_name_norm TEXT")
        ensure("dob_iso", "dob_iso TEXT")
        ensure("id_number_norm", "id_number_norm TEXT")
        ensure("identity_hash", "identity_hash TEXT")
        ensure("dnr_hit_id", "dnr_hit_id INTEGER")
        ensure("dnr_match_score", "dnr_match_score TEXT")
        ensure("dnr_match_tier", "dnr_match_tier INTEGER")
        ensure("dnr_override_by", "dnr_override_by TEXT")
        ensure("dnr_override_reason", "dnr_override_reason TEXT")
        ensure("dnr_override_at", "dnr_override_at DATETIME")

        # Blacklist table columns
        bcols = [row[1] for row in conn.exec_driver_sql("PRAGMA table_info(blacklist)").fetchall()]
        def ensure_b(col_name: str, ddl: str):
            if col_name not in bcols:
                conn.exec_driver_sql(f"ALTER TABLE blacklist ADD COLUMN {ddl}")
        ensure_b("updated_at", "updated_at DATETIME")
        ensure_b("deleted_at", "deleted_at DATETIME")
        ensure_b("first_name_norm", "first_name_norm TEXT")
        ensure_b("last_name_norm", "last_name_norm TEXT")
        ensure_b("dob_iso", "dob_iso TEXT")
        ensure_b("id_number_norm", "id_number_norm TEXT")