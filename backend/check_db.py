import asyncio

import asyncpg

from backend.app.core.config import data_base_conf


async def main() -> list[str]:
    conn = await asyncpg.connect(data_base_conf.DATABASE_URL.replace(
        "postgresql+asyncpg://", "postgresql://", 1
    ))
    try:
        tables = await conn.fetch(
            "SELECT table_name FROM information_schema.tables "
            "WHERE table_schema = 'public' AND table_type = 'BASE TABLE' "
            "ORDER BY table_name"
        )
    finally:
        await conn.close()
    return [t[0] for t in tables]

if __name__ == '__main__':
    tables = asyncio.run(main())
    print('Tables:', tables)
