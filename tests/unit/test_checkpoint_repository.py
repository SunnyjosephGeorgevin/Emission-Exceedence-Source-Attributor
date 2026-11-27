
import asyncio

import pytest

from src.database import connection as connection_module
from src.database import checkpoint_repository as repository_module
from src.database.schema import SCHEMA


def configure_test_database(tmp_path, monkeypatch):

    database_path = tmp_path / "checkpoint_test.db"

    async def initialize():

        db = await connection_module.get_connection(
            database_path
        )

        try:
            await db.executescript(SCHEMA)

            await db.execute(
                """
                INSERT INTO investigations (
                    station_id,
                    status,
                    current_stage,
                    created_at
                )
                VALUES (?, ?, ?, ?)
                """,
                (
                    "ST-TEST",
                    "running",
                    "pending",
                    "2026-11-25T10:00:00+00:00",
                ),
            )

            await db.commit()

        finally:
            await db.close()

    asyncio.run(initialize())

    async def get_test_connection():
        return await connection_module.get_connection(
            database_path
        )

    monkeypatch.setattr(
        repository_module,
        "get_connection",
        get_test_connection,
    )


def test_save_and_retrieve_checkpoint(tmp_path, monkeypatch):

    configure_test_database(tmp_path, monkeypatch)

    async def main():

        repository = repository_module.CheckpointRepository()

        state = {
            "exceedances_detected": 3,
            "facilities_screened": 3,
            "completed_agents": [
                "spike_detector",
                "wind_backtracker",
            ],
        }

        checkpoint_id = await repository.save_checkpoint(
            investigation_id=1,
            stage="python_investigation_completed",
            state=state,
        )

        assert checkpoint_id > 0

        checkpoint = await repository.get_latest_checkpoint(1)

        assert checkpoint is not None
        assert checkpoint["stage"] == "python_investigation_completed"
        assert checkpoint["state"] == state

    asyncio.run(main())


def test_checkpoint_history(tmp_path, monkeypatch):

    configure_test_database(tmp_path, monkeypatch)

    async def main():

        repository = repository_module.CheckpointRepository()

        await repository.save_checkpoint(
            investigation_id=1,
            stage="data_retrieved",
            state={"readings": 3},
        )

        await repository.save_checkpoint(
            investigation_id=1,
            stage="python_investigation_completed",
            state={"facilities": 3},
        )

        history = await repository.get_checkpoint_history(1)

        assert len(history) == 2
        assert history[0]["stage"] == "data_retrieved"
        assert history[1]["stage"] == "python_investigation_completed"

    asyncio.run(main())


def test_latest_checkpoint_returns_none(tmp_path, monkeypatch):

    configure_test_database(tmp_path, monkeypatch)

    async def main():

        repository = repository_module.CheckpointRepository()

        checkpoint = await repository.get_latest_checkpoint(1)

        assert checkpoint is None

    asyncio.run(main())


def test_save_checkpoint_rejects_invalid_json(tmp_path, monkeypatch):

    configure_test_database(tmp_path, monkeypatch)

    async def main():

        repository = repository_module.CheckpointRepository()

        with pytest.raises(ValueError):

            await repository.save_checkpoint(
                investigation_id=1,
                stage="invalid",
                state={"invalid_number": float("nan")},
            )

    asyncio.run(main())
