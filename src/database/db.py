"""
Database connection and session management.
Handles connection pooling, session lifecycle, and utilities.
"""

import logging
import os
from typing import Generator

from sqlalchemy import create_engine, event
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import QueuePool

logger = logging.getLogger(__name__)


class DatabaseConfig:
    """Database configuration from environment."""

    DB_HOST = os.getenv("DB_HOST", "localhost")
    DB_PORT = os.getenv("DB_PORT", "5432")
    DB_NAME = os.getenv("DB_NAME", "dropoff_detection")
    DB_USER = os.getenv("DB_USER", "postgres")
    DB_PASSWORD = os.getenv("DB_PASSWORD", "postgres")
    POOL_SIZE = int(os.getenv("DB_POOL_SIZE", "20"))
    MAX_OVERFLOW = int(os.getenv("DB_MAX_OVERFLOW", "40"))
    POOL_RECYCLE = int(os.getenv("DB_POOL_RECYCLE", "3600"))
    ECHO_SQL = os.getenv("DB_ECHO_SQL", "false").lower() == "true"

    @classmethod
    def get_database_url(cls) -> str:
        """Construct database URL from config."""
        return (
            f"postgresql://{cls.DB_USER}:{cls.DB_PASSWORD}@"
            f"{cls.DB_HOST}:{cls.DB_PORT}/{cls.DB_NAME}"
        )


class DatabaseManager:
    """Manages database connection lifecycle."""

    _engine = None
    _SessionLocal = None

    @classmethod
    def initialize(cls):
        """Initialize database engine and session factory."""
        if cls._engine is not None:
            logger.warning("Database already initialized")
            return

        db_url = DatabaseConfig.get_database_url()
        logger.info(f"Initializing database: {db_url.split('@')[1]}")

        # Create engine with connection pooling
        cls._engine = create_engine(
            db_url,
            poolclass=QueuePool,
            pool_size=DatabaseConfig.POOL_SIZE,
            max_overflow=DatabaseConfig.MAX_OVERFLOW,
            pool_recycle=DatabaseConfig.POOL_RECYCLE,
            echo=DatabaseConfig.ECHO_SQL,
            connect_args={"connect_timeout": 10},
        )

        # Configure connection event listeners
        cls._setup_connection_listeners()

        # Create session factory
        cls._SessionLocal = sessionmaker(
            autocommit=False, autoflush=False, bind=cls._engine
        )

        logger.info("Database initialized successfully")

    @classmethod
    def _setup_connection_listeners(cls):
        """Setup SQLAlchemy event listeners for connections."""

        @event.listens_for(cls._engine, "connect")
        def set_sqlite_pragma(dbapi_conn, connection_record):
            """Set PostgreSQL application name for monitoring."""
            try:
                dbapi_conn.application_name = "dropoff_detection_api"
            except Exception as e:
                logger.debug(f"Could not set application name: {e}")

        @event.listens_for(cls._engine, "engine_disposed")
        def receive_engine_disposed(engine):
            """Log when engine is disposed."""
            logger.info("Database connection pool disposed")

    @classmethod
    def get_session(cls) -> Session:
        """Get a new database session."""
        if cls._SessionLocal is None:
            cls.initialize()
        return cls._SessionLocal()

    @classmethod
    def get_engine(cls):
        """Get the database engine."""
        if cls._engine is None:
            cls.initialize()
        return cls._engine

    @classmethod
    def dispose_pool(cls):
        """Dispose all connections in the pool."""
        if cls._engine is not None:
            cls._engine.dispose()
            logger.info("Database connection pool disposed")

    @classmethod
    def health_check(cls) -> bool:
        """Check if database is accessible."""
        try:
            engine = cls.get_engine()
            with engine.connect() as conn:
                conn.execute("SELECT 1")
            return True
        except Exception as e:
            logger.error(f"Database health check failed: {e}")
            return False


def get_db() -> Generator[Session, None, None]:
    """
    Dependency for FastAPI to inject database session.
    Usage:
        @app.get("/")
        def get_data(db: Session = Depends(get_db)):
            ...
    """
    db = DatabaseManager.get_session()
    try:
        yield db
    finally:
        db.close()


class DatabaseUtils:
    """Utility functions for database operations."""

    @staticmethod
    def create_all_tables():
        """Create all tables in the database."""
        from src.database.models import Base

        engine = DatabaseManager.get_engine()
        Base.metadata.create_all(bind=engine)
        logger.info("All tables created successfully")

    @staticmethod
    def drop_all_tables():
        """Drop all tables (use with caution!)."""
        from src.database.models import Base

        engine = DatabaseManager.get_engine()
        Base.metadata.drop_all(bind=engine)
        logger.warning("All tables dropped!")

    @staticmethod
    def get_table_count() -> dict:
        """Get row count for each table."""
        from src.database.models import APICall, AuditLog, Prediction, User

        db = DatabaseManager.get_session()
        try:
            counts = {
                "users": db.query(User).count(),
                "predictions": db.query(Prediction).count(),
                "api_calls": db.query(APICall).count(),
                "audit_logs": db.query(AuditLog).count(),
            }
            return counts
        finally:
            db.close()

    @staticmethod
    def vacuum_database():
        """Run VACUUM on database (PostgreSQL only)."""
        from sqlalchemy import text

        engine = DatabaseManager.get_engine()
        with engine.connect() as conn:
            conn.execute(text("VACUUM ANALYZE"))
            conn.commit()
        logger.info("Database vacuumed and analyzed")


# Initialize database on module import
try:
    DatabaseManager.initialize()
except Exception as e:
    logger.error(f"Failed to initialize database: {e}")
