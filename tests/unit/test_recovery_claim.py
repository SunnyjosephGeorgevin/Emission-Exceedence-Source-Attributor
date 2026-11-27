
import pytest

from src.database.connection import get_connection
from src.database.schema import SCHEMA
from src.database.repository import InvestigationRepository
from src.database.checkpoint_repository import CheckpointRepository


@pytest.fixture
async def repositories(tmp_path, monkeypatch):

    database_path = tmp_path / "recovery_claim.db"

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

    return (
        InvestigationRepository(),
        CheckpointRepository(),
    )


@pytest.mark.anyio
async def test_first_worker_can_claim_recovery(repositories):

    investigation_repo, checkpoint_repo = repositories

    investigation_id = await investigation_repo.create_investigation(
        station_id="ST-001",
        status="running",
        current_stage="data_retrieved",
    )

    claimed = await checkpoint_repo.claim_recovery(
        investigation_id
    )

    assert claimed is True

    saved = await investigation_repo.get_investigation(
        investigation_id
    )

    assert saved["investigation"]["status"] == "recovering"


@pytest.mark.anyio
async def test_second_worker_cannot_claim_same_investigation(
    repositories,
):

    investigation_repo, checkpoint_repo = repositories

    investigation_id = await investigation_repo.create_investigation(
        station_id="ST-001",
        status="running",
        current_stage="data_retrieved",
    )

    first_claim = await checkpoint_repo.claim_recovery(
        investigation_id
    )

    second_claim = await checkpoint_repo.claim_recovery(
        investigation_id
    )

    assert first_claim is True
    assert second_claim is False


@pytest.mark.anyio
async def test_recovery_claim_rejects_completed_investigation(
    repositories,
):

    investigation_repo, checkpoint_repo = repositories

    investigation_id = await investigation_repo.create_investigation(
        station_id="ST-001",
        status="completed",
        current_stage="completed",
    )

    claimed = await checkpoint_repo.claim_recovery(
        investigation_id
    )

    assert claimed is False


@pytest.mark.anyio
async def test_release_recovery_allows_another_attempt(
    repositories,
):

    investigation_repo, checkpoint_repo = repositories

    investigation_id = await investigation_repo.create_investigation(
        station_id="ST-001",
        status="running",
        current_stage="data_retrieved",
    )

    first_claim = await checkpoint_repo.claim_recovery(
        investigation_id
    )

    released = await checkpoint_repo.release_recovery(
        investigation_id
    )

    second_claim = await checkpoint_repo.claim_recovery(
        investigation_id
    )

    assert first_claim is True
    assert released is True
    assert second_claim is True


@pytest.mark.anyio
async def test_release_recovery_rejects_unclaimed_investigation(
    repositories,
):

    investigation_repo, checkpoint_repo = repositories

    investigation_id = await investigation_repo.create_investigation(
        station_id="ST-001",
        status="running",
        current_stage="data_retrieved",
    )

    released = await checkpoint_repo.release_recovery(
        investigation_id
    )

    assert released is False


@pytest.mark.anyio
async def test_claim_recovery_rejects_unknown_investigation(
    repositories,
):

    _, checkpoint_repo = repositories

    claimed = await checkpoint_repo.claim_recovery(99999)

    assert claimed is False
