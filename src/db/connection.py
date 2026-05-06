from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Any, AsyncGenerator, Dict
import anyio
from contextlib import asynccontextmanager

from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import NullPool

from src.utils.config_loader import load_config


@lru_cache(maxsize=1)
def _load_database_config() -> Dict[str, Any]:
    cfg = load_config("config.yaml")
    database = cfg.get("database", {})
    return database if isinstance(database, dict) else {}


def _build_database_url(database_cfg: Dict[str, Any], async_mode: bool = False) -> str:
    explicit_url = str(database_cfg.get("url", "")).strip()
    if explicit_url:
        return explicit_url

    db_type = str(database_cfg.get("type", "sqlite")).lower().strip()
    if db_type == "sqlite":
        db_file = str(database_cfg.get("database", "mlops.db")).strip() or "mlops.db"
        db_path = Path(db_file)
        if not db_path.is_absolute():
            db_path = Path.cwd() / db_path
        db_path.parent.mkdir(parents=True, exist_ok=True)
        # For async SQLite, use aiosqlite
        if async_mode:
            return f"sqlite+aiosqlite:///{db_path.as_posix()}"
        return f"sqlite:///{db_path.as_posix()}"

    user = str(database_cfg.get("user", "")).strip()
    password = str(database_cfg.get("password", "")).strip()
    host = str(database_cfg.get("host", "localhost")).strip()
    port = database_cfg.get("port", 5432)
    name = str(database_cfg.get("database", "dropoff_detection")).strip()

    if db_type in {"postgres", "postgresql"}:
        if async_mode:
            return f"postgresql+asyncpg://{user}:{password}@{host}:{port}/{name}"
        return f"postgresql+psycopg2://{user}:{password}@{host}:{port}/{name}"

    if db_type in {"mysql", "mariadb"}:
        if async_mode:
            return f"mysql+aiomysql://{user}:{password}@{host}:{port}/{name}"
        return f"mysql+pymysql://{user}:{password}@{host}:{port}/{name}"

    raise ValueError(f"Unsupported database type: {db_type}")


@lru_cache(maxsize=1)
def get_database_url(async_mode: bool = False) -> str:
    return _build_database_url(_load_database_config(), async_mode=async_mode)


@lru_cache(maxsize=1)
def get_engine() -> Engine:
    """Create SQLAlchemy engine with optimized connection pooling. O(1) due to caching."""
    db_cfg = _load_database_config()
    db_url = get_database_url()
    echo = bool(db_cfg.get("echo", False))

    # Connection pool optimization: pool_size=10, max_overflow=20 for production databases only
    # SQLite doesn't benefit from connection pooling
    engine_kwargs = {
        "echo": echo,
        "pool_pre_ping": True,
        "future": True,
    }

    # Only add pool parameters for non-SQLite databases
    if not db_url.startswith("sqlite://"):
        engine_kwargs["pool_size"] = 10
        engine_kwargs["max_overflow"] = 20
        engine_kwargs["pool_recycle"] = 3600

    return create_engine(db_url, **engine_kwargs)


@lru_cache(maxsize=1)
def get_session_factory() -> sessionmaker[Session]:
    return sessionmaker(
        bind=get_engine(), autoflush=False, autocommit=False, expire_on_commit=False
    )


def init_database() -> None:
    # Import here to avoid circular imports.
    from src.db.models import Base

    Base.metadata.create_all(bind=get_engine())


# ============================================================================
# ASYNC DATABASE SUPPORT (for FastAPI with async/await)
# ============================================================================

@lru_cache(maxsize=1)
def get_async_engine():
    """Create async SQLAlchemy engine for FastAPI. Returns create_async_engine result."""
    db_cfg = _load_database_config()
    db_url = get_database_url(async_mode=True)
    echo = bool(db_cfg.get("echo", False))

    engine_kwargs = {
        "echo": echo,
        "future": True,
    }

    # SQLite async uses aiosqlite which has different pooling
    if db_url.startswith("sqlite"):
        engine_kwargs["connect_args"] = {"check_same_thread": False}
        engine_kwargs["poolclass"] = NullPool
    else:
        # PostgreSQL/MySQL async engines with connection pooling
        engine_kwargs["pool_size"] = 10
        engine_kwargs["max_overflow"] = 20
        engine_kwargs["pool_pre_ping"] = True
        engine_kwargs["pool_recycle"] = 3600

    return create_async_engine(db_url, **engine_kwargs)


def get_async_session_factory():
    """Get async sessionmaker for FastAPI dependency injection."""
    from sqlalchemy.ext.asyncio import async_sessionmaker
    
    return async_sessionmaker(
        get_async_engine(),
        class_=AsyncSession,
        autoflush=False,
        autocommit=False,
        expire_on_commit=False,
    )


async def get_async_session() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI dependency for getting async database sessions."""
    try:
        async_factory = get_async_session_factory()
    except ModuleNotFoundError:
        # Async DB driver not available (e.g. aiosqlite). Fall back to
        # providing a sync `Session` executed in a thread so async handlers
        # can still depend on a "session-like" object without crashing.
        @asynccontextmanager
        async def _sync_session_context():
            SyncFactory = get_session_factory()
            session = await anyio.to_thread.run_sync(lambda: SyncFactory())
            try:
                yield session
            finally:
                await anyio.to_thread.run_sync(session.close)

        async with _sync_session_context() as session:
            yield session
        return

    async with async_factory() as session:
        yield session


async def init_async_database() -> None:
    """Initialize async database (create tables if needed)."""
    from src.db.models import Base

    async_engine = get_async_engine()
    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
