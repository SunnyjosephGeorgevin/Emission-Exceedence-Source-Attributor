
import asyncio

import pytest

from src.database import connection as connection_module
from src.database import repository as repository_module
from src.database.schema import SCHEMA


def configure_test_database(tmp_path, monkeypatch):
    """
    Configure an isolated SQLite database for a test.
    """

    database_path = tmp_path / "test_emissions.db"

    async def initialize_test_database():

        db = await connection_module.get_connection(
            database_path
        )

        try:
            await db.executescript(SCHEMA)
            await db.commit()

        finally:
            await db.close()

    asyncio.run(initialize_test_database())

    async def get_test_connection():
        return await connection_module.get_connection(
            database_path
        )

    monkeypatch.setattr(
        repository_module,
        "get_connection",
        get_test_connection,
    )


def test_save_investigation(tmp_path, monkeypatch):

    configure_test_database(tmp_path, monkeypatch)

    async def main():

        repository = repository_module.InvestigationRepository()

        metrics = {
            "tools": {
                "get_station_readings": {
                    "calls": 1,
                    "attempts": 1,
                    "successes": 1,
                    "failures": 0,
                    "retries": 0,
                    "total_attempt_duration_seconds": 0.015,
                    "last_attempt_duration_seconds": 0.015,
                }
            }
        }

        investigation_id = await repository.save_investigation(
            station_id="ST-TEST",
            status="completed",
            execution_seconds=2.5,
            mcp_metrics=metrics,
        )

        assert investigation_id is not None
        assert investigation_id > 0

    asyncio.run(main())


def test_retrieve_investigation(tmp_path, monkeypatch):

    configure_test_database(tmp_path, monkeypatch)

    async def main():

        repository = repository_module.InvestigationRepository()

        metrics = {
            "tools": {
                "get_wind_history": {
                    "calls": 1,
                    "attempts": 1,
                    "successes": 1,
                    "failures": 0,
                    "retries": 0,
                    "total_attempt_duration_seconds": 0.02,
                    "last_attempt_duration_seconds": 0.02,
                }
            }
        }

        investigation_id = await repository.save_investigation(
            station_id="ST-RETRIEVE",
            status="completed",
            execution_seconds=3.0,
            mcp_metrics=metrics,
        )

        result = await repository.get_investigation(
            investigation_id
        )

        assert result is not None

        assert (
            result["investigation"]["station_id"]
            == "ST-RETRIEVE"
        )

        assert (
            result["investigation"]["status"]
            == "completed"
        )

        assert len(result["tool_metrics"]) == 1

        assert (
            result["tool_metrics"][0]["tool_name"]
            == "get_wind_history"
        )

    asyncio.run(main())


def test_get_recent_investigations(tmp_path, monkeypatch):

    configure_test_database(tmp_path, monkeypatch)

    async def main():

        repository = repository_module.InvestigationRepository()

        metrics = {"tools": {}}

        await repository.save_investigation(
            station_id="ST-001",
            status="completed",
            execution_seconds=2.0,
            mcp_metrics=metrics,
        )

        await repository.save_investigation(
            station_id="ST-002",
            status="completed",
            execution_seconds=3.0,
            mcp_metrics=metrics,
        )

        await repository.save_investigation(
            station_id="ST-003",
            status="failed",
            execution_seconds=1.0,
            mcp_metrics=metrics,
        )

        history = await repository.get_recent_investigations()

        assert len(history) == 3

        assert history[0]["station_id"] == "ST-003"
        assert history[1]["station_id"] == "ST-002"
        assert history[2]["station_id"] == "ST-001"

    asyncio.run(main())


def test_get_recent_investigations_limit(tmp_path, monkeypatch):

    configure_test_database(tmp_path, monkeypatch)

    async def main():

        repository = repository_module.InvestigationRepository()

        metrics = {"tools": {}}

        for index in range(5):

            await repository.save_investigation(
                station_id=f"ST-{index}",
                status="completed",
                execution_seconds=2.0,
                mcp_metrics=metrics,
            )

        history = await repository.get_recent_investigations(
            limit=2
        )

        assert len(history) == 2

    asyncio.run(main())


def test_get_recent_investigations_invalid_limit(
    tmp_path,
    monkeypatch,
):

    configure_test_database(tmp_path, monkeypatch)

    async def main():

        repository = repository_module.InvestigationRepository()

        with pytest.raises(ValueError):
            await repository.get_recent_investigations(
                limit=0
            )

    asyncio.run(main())
