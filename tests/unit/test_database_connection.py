import asyncio

from src.database.connection import get_connection


def test_sqlite_connection():

    async def main():
        db = await get_connection()

        assert db is not None

        await db.close()

    asyncio.run(main())