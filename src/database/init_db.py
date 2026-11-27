
import asyncio

from src.database.connection import get_connection
from src.database.schema import SCHEMA


async def initialize_database():

    db = await get_connection()

    try:
        # Create missing tables.
        await db.executescript(SCHEMA)

        # Inspect existing investigation columns.
        cursor = await db.execute(
            "PRAGMA table_info(investigations)"
        )

        columns = await cursor.fetchall()

        existing_columns = {
            column["name"]
            for column in columns
        }

        # Safe migrations for existing databases.
        migrations = {
            "result_json": "TEXT",
            "current_stage": "TEXT NOT NULL DEFAULT 'pending'",
            "updated_at": "TEXT",
            "error_message": "TEXT",
            "checkpoint_json": "TEXT",
            "station_latitude": "REAL",
            "station_longitude": "REAL",
        }

        for column_name, column_definition in migrations.items():

            if column_name not in existing_columns:

                await db.execute(
                    f"""
                    ALTER TABLE investigations
                    ADD COLUMN {column_name} {column_definition}
                    """
                )

                print(f"Added column: {column_name}")

        await db.commit()

        print("Database schema initialized successfully!")

    except Exception:
        await db.rollback()
        raise

    finally:
        await db.close()


if __name__ == "__main__":
    asyncio.run(initialize_database())
