from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy import text
from typing import AsyncGenerator

from config import settings

engine = create_async_engine(settings.DATABASE_URL, echo=False)
async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


class Base(DeclarativeBase):
    pass


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with async_session() as session:
        try:
            yield session
        finally:
            await session.close()


_ADDITIVE_MIGRATIONS = [
    ("admins", "pin", "VARCHAR(255)"),
    ("seats", "pos_x", "INTEGER"),
    ("seats", "pos_y", "INTEGER"),
]


async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    # SQLite-only additive migrations for columns added after the initial schema.
    # create_all() only creates missing tables, never alters existing ones; running
    # ALTER TABLE ADD COLUMN here keeps deployed DBs in sync without Alembic.
    # Run in a fresh transaction so create_all DDL is committed before PRAGMA reads.
    async with engine.begin() as conn:
        for table, column, coltype in _ADDITIVE_MIGRATIONS:
            cols = await conn.exec_driver_sql(f"PRAGMA table_info({table})")
            existing = {row[1] for row in cols.fetchall()}
            if column not in existing:
                await conn.exec_driver_sql(f"ALTER TABLE {table} ADD COLUMN {column} {coltype}")
