import asyncpg
import asyncio

async def main():
    conn = await asyncpg.connect(user='tzo_user', password='tzo_password', host='localhost', port=5432, database='tzo-market')
    tables = await conn.fetch("SELECT table_name FROM information_schema.tables WHERE table_schema = 'public' AND table_type = 'BASE TABLE' ORDER BY table_name")
    await conn.close()
    return [t[0] for t in tables]

if __name__ == '__main__':
    tables = asyncio.run(main())
    print('Tables:', tables)