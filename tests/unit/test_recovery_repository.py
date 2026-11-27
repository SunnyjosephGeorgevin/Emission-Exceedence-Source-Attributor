
import pytest

from src.database.connection import get_connection
from src.database.repository import InvestigationRepository
from src.database.checkpoint_repository import CheckpointRepository
from src.database.schema import SCHEMA


async def setup_test_database(database_path, monkeypatch):

    async def test_connection():
        return await get_connection(database_path)

    monkeypatch.setattr(
        "src.database.repository.get_connection",
        test_connection,
    )

    monkeypatch.setattr(
        "src.database.checkpoint_repository.get_connection",
        test_connection,
    )

    db = await get_connection(database_path)

    await db.executescript(SCHEMA)
    await db.commit()
    await db.close()


@pytest.mark.anyio
async def test_find_interrupted_investigation(tmp_path, monkeypatch):

    database_path = tmp_path / "recovery_test.db"

    await setup_test_database(database_path, monkeypatch)

    investigation_repo = InvestigationRepository()
    checkpoint_repo = CheckpointRepository()

    investigation_id = await investigation_repo.create_investigation(
        station_id="ST-001",
        status="running",
        current_stage="data_retrieved",
    )

    await checkpoint_repo.save_checkpoint(
        investigation_id=investigation_id,
        stage="data_retrieved",
        state={"readings_retrieved": True},
    )

    recoverable = (
        await checkpoint_repo.get_recoverable_investigations()
    )

    assert len(recoverable) == 1
    assert recoverable[0]["id"] == investigation_id
    assert recoverable[0]["status"] == "running"


@pytest.mark.anyio
async def test_awaiting_approval_is_not_recoverable(
    tmp_path,
    monkeypatch,
):

    database_path = tmp_path / "approval_test.db"

    await setup_test_database(database_path, monkeypatch)

    investigation_repo = InvestigationRepository()
    checkpoint_repo = CheckpointRepository()

    await investigation_repo.create_investigation(
        station_id="ST-001",
        status="awaiting_approval",
        current_stage="awaiting_approval",
    )

    recoverable = (
        await checkpoint_repo.get_recoverable_investigations()
    )

    assert len(recoverable) == 0


@pytest.mark.anyio
async def test_reconstruct_checkpoint_state(
    tmp_path,
    monkeypatch,
):

    database_path = tmp_path / "reconstruction_test.db"

    await setup_test_database(database_path, monkeypatch)

    investigation_repo = InvestigationRepository()
    checkpoint_repo = CheckpointRepository()

    investigation_id = await investigation_repo.create_investigation(
        station_id="ST-001",
        status="running",
        current_stage="data_retrieved",
    )

    saved_state = {
        "station_id": "ST-001",
        "readings_retrieved": True,
        "wind_direction": 100,
    }

    await checkpoint_repo.save_checkpoint(
        investigation_id=investigation_id,
        stage="data_retrieved",
        state=saved_state,
    )

    recovered = await checkpoint_repo.get_recovery_state(
        investigation_id
    )

    assert recovered is not None

    assert recovered["investigation"]["id"] == investigation_id

    assert recovered["investigation"]["station_id"] == "ST-001"

    assert recovered["checkpoint"]["stage"] == "data_retrieved"

    assert recovered["reconstructed_state"] == saved_state
