from collections.abc import AsyncGenerator

from backend.app.core.config import data_base_conf
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

engine = create_async_engine(url=data_base_conf.DATABASE_URL)

async_session_factory = async_sessionmaker(
    bind=engine, autoflush=False, expire_on_commit=False
)


async def get_async_session() -> AsyncGenerator:
    async with async_session_factory() as session, session.begin():
        yield session
