
import pytest

from src.database.connection import get_connection
from src.database.repository import InvestigationRepository
from src.database.checkpoint_repository import CheckpointRepository
from src.database.schema import SCHEMA
from src.services.recovery_service import RecoveryService


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
async def test_prepare_valid_recovery(tmp_path, monkeypatch):

    database_path = tmp_path / "valid_recovery.db"

    await setup_test_database(database_path, monkeypatch)

    investigation_repo = InvestigationRepository()
    checkpoint_repo = CheckpointRepository()
    recovery_service = RecoveryService()

    investigation_id = await investigation_repo.create_investigation(
        station_id="ST-001",
        status="running",
        current_stage="data_retrieved",
    )

    saved_state = {
        "readings_retrieved": True,
        "station_id": "ST-001",
    }

    await checkpoint_repo.save_checkpoint(
        investigation_id=investigation_id,
        stage="data_retrieved",
        state=saved_state,
    )

    recovery = await recovery_service.prepare_recovery(
        investigation_id
    )

    assert recovery["investigation_id"] == investigation_id
    assert recovery["station_id"] == "ST-001"
    assert recovery["recovery_stage"] == "data_retrieved"
    assert recovery["reconstructed_state"] == saved_state
    assert recovery["recovery_ready"] is True


@pytest.mark.anyio
async def test_reject_awaiting_approval_recovery(
    tmp_path,
    monkeypatch,
):

    database_path = tmp_path / "approval_recovery.db"

    await setup_test_database(database_path, monkeypatch)

    investigation_repo = InvestigationRepository()
    recovery_service = RecoveryService()

    investigation_id = await investigation_repo.create_investigation(
        station_id="ST-001",
        status="awaiting_approval",
        current_stage="awaiting_approval",
    )

    with pytest.raises(ValueError, match="Only investigations"):
        await recovery_service.prepare_recovery(
            investigation_id
        )


@pytest.mark.anyio
async def test_reject_investigation_without_checkpoint(
    tmp_path,
    monkeypatch,
):

    database_path = tmp_path / "missing_checkpoint.db"

    await setup_test_database(database_path, monkeypatch)

    investigation_repo = InvestigationRepository()
    recovery_service = RecoveryService()

    investigation_id = await investigation_repo.create_investigation(
        station_id="ST-001",
        status="running",
        current_stage="started",
    )

    with pytest.raises(ValueError, match="no saved checkpoint"):
        await recovery_service.prepare_recovery(
            investigation_id
        )

@pytest.mark.anyio
async def test_recovery_action_after_data_retrieval(
    tmp_path,
    monkeypatch,
):

    database_path = tmp_path / "data_stage.db"
    await setup_test_database(database_path, monkeypatch)

    investigation_repo = InvestigationRepository()
    checkpoint_repo = CheckpointRepository()
    recovery_service = RecoveryService()

    investigation_id = await investigation_repo.create_investigation(
        station_id="ST-001",
        status="running",
    )

    await checkpoint_repo.save_checkpoint(
        investigation_id=investigation_id,
        stage="data_retrieved",
        state={"readings_retrieved": True},
    )

    recovery = await recovery_service.prepare_recovery(
        investigation_id
    )

    assert recovery["next_action"] == "resume_python_investigation"


@pytest.mark.anyio
async def test_recovery_action_after_python_investigation(
    tmp_path,
    monkeypatch,
):

    database_path = tmp_path / "python_stage.db"
    await setup_test_database(database_path, monkeypatch)

    investigation_repo = InvestigationRepository()
    checkpoint_repo = CheckpointRepository()
    recovery_service = RecoveryService()

    investigation_id = await investigation_repo.create_investigation(
        station_id="ST-001",
        status="running",
    )

    await checkpoint_repo.save_checkpoint(
        investigation_id=investigation_id,
        stage="python_investigation_completed",
        state={"investigation_completed": True},
    )

    recovery = await recovery_service.prepare_recovery(
        investigation_id
    )

    assert recovery["next_action"] == "resume_llm_interpretation"


@pytest.mark.anyio
async def test_recovery_action_after_llm_interpretation(
    tmp_path,
    monkeypatch,
):

    database_path = tmp_path / "llm_stage.db"
    await setup_test_database(database_path, monkeypatch)

    investigation_repo = InvestigationRepository()
    checkpoint_repo = CheckpointRepository()
    recovery_service = RecoveryService()

    investigation_id = await investigation_repo.create_investigation(
        station_id="ST-001",
        status="running",
    )

    await checkpoint_repo.save_checkpoint(
        investigation_id=investigation_id,
        stage="llm_interpretation_completed",
        state={"llm_interpretation_status": "passed_basic_checks"},
    )

    recovery = await recovery_service.prepare_recovery(
        investigation_id
    )

    assert recovery["next_action"] == "finalize_for_human_approval"
