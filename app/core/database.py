from typing import AsyncGenerator
from urllib.parse import urlparse, urlunparse
from sqlalchemy import event, text
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.ext.compiler import compiles
from sqlalchemy.dialects.postgresql import JSONB, UUID as PGUUID
from sqlalchemy.orm import declarative_base
from app.core.config import settings

import os


@compiles(JSONB, "sqlite")
def _compile_jsonb_sqlite(_type, _compiler, **_kw) -> str:
    return "JSON"


@compiles(PGUUID, "sqlite")
def _compile_uuid_sqlite(_type, _compiler, **_kw) -> str:
    return "CHAR(32)"


# Clean database URL schema for async pg
database_url = (
    os.getenv("DATABASE_URL")
    or os.getenv("DATABASE_PRIVATE_URL")
    or os.getenv("POSTGRES_URL")
    or settings.DATABASE_URL
)
if database_url.startswith("postgresql://") and not database_url.startswith("postgresql+asyncpg://"):
    database_url = database_url.replace("postgresql://", "postgresql+asyncpg://", 1)


def _resolve_bot_database_url() -> str:
    """Resuelve la URL de conexión para el rol de solo lectura `bot_lectura`."""
    explicit_bot_url = os.getenv("BOT_DATABASE_URL") or settings.BOT_DATABASE_URL
    if explicit_bot_url:
        if explicit_bot_url.startswith("postgresql://") and not explicit_bot_url.startswith("postgresql+asyncpg://"):
            return explicit_bot_url.replace("postgresql://", "postgresql+asyncpg://", 1)
        return explicit_bot_url

    bot_password = os.getenv("BOT_DB_PASSWORD") or settings.BOT_DB_PASSWORD
    bot_user = os.getenv("BOT_DB_USER") or settings.BOT_DB_USER or "bot_lectura"
    if bot_password and database_url.startswith("postgresql"):
        parsed = urlparse(database_url)
        host_port = f"{parsed.hostname}:{parsed.port}" if parsed.port else (parsed.hostname or "localhost")
        netloc = f"{bot_user}:{bot_password}@{host_port}"
        return urlunparse((parsed.scheme, netloc, parsed.path, parsed.params, parsed.query, parsed.fragment))

    return database_url


bot_database_url = _resolve_bot_database_url()

engine = create_async_engine(
    database_url,
    echo=False,
    future=True,
    pool_pre_ping=True,
    pool_size=20,
    max_overflow=20,
    pool_recycle=300,
    pool_timeout=60,
)

bot_engine = (
    create_async_engine(
        bot_database_url,
        echo=False,
        future=True,
        pool_pre_ping=True,
        pool_size=10,
        max_overflow=10,
        pool_recycle=300,
        pool_timeout=60,
    )
    if bot_database_url != database_url
    else engine
)

SessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)

BotSessionLocal = async_sessionmaker(
    bind=bot_engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)


def _prevent_bot_writes(session, _flush_context, _instances) -> None:
    if session.info.get("readonly_bot"):
        if session.new or session.dirty or session.deleted:
            raise PermissionError("El módulo /api/v1/bot usa el rol bot_lectura y es estrictamente de SOLO LECTURA.")


event.listen(AsyncSession.sync_session_class, "before_flush", _prevent_bot_writes)

Base = declarative_base()


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Dependency generator for database sessions in FastAPI routes."""
    async with SessionLocal() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def get_bot_db() -> AsyncGenerator[AsyncSession, None]:
    """Sesión de base de datos de SOLO LECTURA (rol `bot_lectura`) para `/api/v1/bot`."""
    async with BotSessionLocal() as session:
        session.info["readonly_bot"] = True
        try:
            bind = session.get_bind()
            dialect_name = getattr(getattr(bind, "dialect", None), "name", "")
            if dialect_name == "postgresql":
                await session.execute(text("SET LOCAL TRANSACTION READ ONLY"))
                try:
                    await session.execute(text("SET LOCAL ROLE bot_lectura"))
                except Exception:
                    pass
            yield session
        finally:
            await session.rollback()
            await session.close()
