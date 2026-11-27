
from pathlib import Path

import aiosqlite

from src.core.config import DATABASE_URL


def get_database_path() -> str:
    """
    Extract the SQLite database file path from DATABASE_URL.
    """

    prefix = "sqlite+aiosqlite:///"

    if not DATABASE_URL.startswith(prefix):
        raise ValueError(
            "Only SQLite with aiosqlite is supported."
        )

    database_path = DATABASE_URL[len(prefix):]

    return database_path


async def get_connection(
    database_path: str | Path | None = None,
):
    """
    Create and return an asynchronous SQLite connection.

    If a custom path is provided, use it.
    Otherwise, use the path configured in DATABASE_URL.
    """

    if database_path is None:
        database_path = get_database_path()

    database_path = str(database_path)

    # Ensure the database directory exists.
    Path(database_path).parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    connection = await aiosqlite.connect(database_path)

    # Enable dictionary-like row access.
    connection.row_factory = aiosqlite.Row

    # Enable foreign-key constraints.
    await connection.execute("PRAGMA foreign_keys = ON")

    return connection
