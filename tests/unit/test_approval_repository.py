
import pytest

from src.database.approval_repository import ApprovalRepository
from src.database.repository import InvestigationRepository
from src.database.init_db import initialize_database


@pytest.fixture
async def repositories(tmp_path, monkeypatch):

    database_path = tmp_path / "approval_test.db"

    import src.database.connection as connection_module

    monkeypatch.setattr(
        connection_module,
        "DATABASE_URL",
        f"sqlite+aiosqlite:///{database_path}",
    )

    await initialize_database()

    return (
        ApprovalRepository(),
        InvestigationRepository(),
    )


@pytest.mark.anyio
async def test_approve_investigation(repositories):

    approval_repo, investigation_repo = repositories

    investigation_id = await investigation_repo.create_investigation(
        station_id="ST-001",
        status="awaiting_approval",
        current_stage="awaiting_approval",
    )

    result = await approval_repo.submit_decision(
        investigation_id=investigation_id,
        decision="approved",
        reviewer="Environmental Officer",
        comments="Evidence reviewed.",
    )

    assert result["decision"] == "approved"
    assert result["reviewer"] == "Environmental Officer"

    investigation = await investigation_repo.get_investigation(
        investigation_id
    )

    assert investigation["investigation"]["status"] == "approved"


@pytest.mark.anyio
async def test_reject_investigation(repositories):

    approval_repo, investigation_repo = repositories

    investigation_id = await investigation_repo.create_investigation(
        station_id="ST-001",
        status="awaiting_approval",
    )

    result = await approval_repo.submit_decision(
        investigation_id=investigation_id,
        decision="rejected",
        reviewer="Environmental Officer",
        comments="Insufficient supporting evidence.",
    )

    assert result["decision"] == "rejected"

    investigation = await investigation_repo.get_investigation(
        investigation_id
    )

    assert investigation["investigation"]["status"] == "rejected"


@pytest.mark.anyio
async def test_duplicate_decision_is_rejected(repositories):

    approval_repo, investigation_repo = repositories

    investigation_id = await investigation_repo.create_investigation(
        station_id="ST-001",
        status="awaiting_approval",
    )

    await approval_repo.submit_decision(
        investigation_id,
        "approved",
        "Officer A",
    )

    with pytest.raises(ValueError, match="awaiting approval"):
        await approval_repo.submit_decision(
            investigation_id,
            "rejected",
            "Officer B",
        )


@pytest.mark.anyio
async def test_invalid_decision_is_rejected(repositories):

    approval_repo, investigation_repo = repositories

    investigation_id = await investigation_repo.create_investigation(
        station_id="ST-001",
        status="awaiting_approval",
    )

    with pytest.raises(ValueError, match="Decision must be"):
        await approval_repo.submit_decision(
            investigation_id,
            "pending",
            "Officer A",
        )


@pytest.mark.anyio
async def test_missing_investigation_is_rejected(repositories):

    approval_repo, investigation_repo = repositories

    with pytest.raises(ValueError, match="not found"):
        await approval_repo.submit_decision(
            9999,
            "approved",
            "Officer A",
        )


@pytest.mark.anyio
async def test_get_approval_record(repositories):

    approval_repo, investigation_repo = repositories

    investigation_id = await investigation_repo.create_investigation(
        station_id="ST-001",
        status="awaiting_approval",
    )

    await approval_repo.submit_decision(
        investigation_id,
        "approved",
        "Officer A",
        "Reviewed successfully.",
    )

    approval = await approval_repo.get_approval(investigation_id)

    assert approval is not None
    assert approval["decision"] == "approved"
    assert approval["reviewer"] == "Officer A"
    assert approval["comments"] == "Reviewed successfully."


@pytest.mark.anyio
async def test_missing_approval_returns_none(repositories):

    approval_repo, investigation_repo = repositories

    approval = await approval_repo.get_approval(9999)

    assert approval is None


@pytest.mark.anyio
async def test_reviewer_is_required(repositories):

    approval_repo, investigation_repo = repositories

    investigation_id = await investigation_repo.create_investigation(
        station_id="ST-001",
        status="awaiting_approval",
    )

    with pytest.raises(ValueError, match="Reviewer name is required"):
        await approval_repo.submit_decision(
            investigation_id,
            "approved",
            "   ",
        )
