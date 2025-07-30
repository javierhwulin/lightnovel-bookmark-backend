"""
Database session configuration using the centralized settings system
"""
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base, Session
from app.core.config import settings

# Create engine with configuration from settings
# SQLite doesn't support connection pooling, so we handle it separately
if "sqlite" in settings.database.url:
    engine = create_engine(
        settings.database.url,
        echo=settings.database.echo,
        connect_args={"check_same_thread": False}
    )
else:
    # PostgreSQL and other databases support connection pooling
    engine = create_engine(
        settings.database.url,
        echo=settings.database.echo,
        pool_size=settings.database.pool_size,
        max_overflow=settings.database.max_overflow,
    )

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def create_tables():
    """Create database tables"""
    Base.metadata.create_all(bind=engine)


def get_db() -> Session:
    """
    Dependency to get database session
    
    Yields:
        Session: SQLAlchemy database session
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()