from sqlalchemy import create_engine, text
from sqlalchemy.orm import declarative_base, sessionmaker

from config import settings

if not settings.database_url:
    raise RuntimeError("DATABASE_URL is not set (see .env.example)")

engine = create_engine(settings.database_url, pool_pre_ping=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db() -> None:
    """Create extension + tables. TODO(db owner): replace with Alembic migrations (SRS §12.2)."""
    with engine.begin() as conn:
        conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
    from db import models  # noqa: F401  (register models)

    Base.metadata.create_all(bind=engine)
