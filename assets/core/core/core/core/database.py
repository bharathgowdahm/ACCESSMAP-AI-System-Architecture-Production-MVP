"""Database engine and session management."""
from collections.abc import Generator
from core.config import get_settings
from core.models import Base
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

settings = get_settings()

# Engine config with thread check disabled for SQLite single-process web app
connect_args = {"check_same_thread": False} if settings.DATABASE_URL.startswith("sqlite") else {}
engine = create_engine(settings.DATABASE_URL, connect_args=connect_args, pool_pre_ping=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def init_db() -> None:
    """Create all relational tables."""
    Base.metadata.create_all(bind=engine)


def get_db() -> Generator[Session, None, None]:
    """Database session generator with auto-close semantics."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
