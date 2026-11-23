from collections.abc import AsyncGenerator

from app.core.config import data_base_conf
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

engine = create_async_engine(url=data_base_conf.DATABASE_URL)

async_session_factory = async_sessionmaker(
    bind=engine, autoflush=False, expire_on_commit=False
)


async def get_async_session() -> AsyncGenerator[AsyncSession, None]:
    async with async_session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
