
import pytest

from fastapi.testclient import TestClient

from src.api.main import app
from src.database.approval_repository import ApprovalRepository
from src.database.repository import InvestigationRepository


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture
async def create_pending_investigation(tmp_path, monkeypatch):

    database_path = tmp_path / "api_test.db"

    import src.database.connection as connection_module

    monkeypatch.setattr(
        connection_module,
        "DATABASE_URL",
        f"sqlite+aiosqlite:///{database_path}",
    )

    from src.database.init_db import initialize_database

    await initialize_database()

    repository = InvestigationRepository()

    investigation_id = await repository.create_investigation(
        station_id="ST-001",
        status="awaiting_approval",
        current_stage="awaiting_approval",
    )

    return investigation_id


@pytest.mark.anyio
async def test_approve_endpoint(
    client,
    create_pending_investigation,
):
    investigation_id = create_pending_investigation

    response = client.post(
        f"/investigations/{investigation_id}/approve",
        json={
            "reviewer": "Environmental Officer",
            "comments": "Evidence reviewed.",
        },
    )

    assert response.status_code == 200
    assert response.json()["decision"] == "approved"
    assert response.json()["status"] == "approved"


@pytest.mark.anyio
async def test_reject_endpoint(
    client,
    create_pending_investigation,
):
    investigation_id = create_pending_investigation

    response = client.post(
        f"/investigations/{investigation_id}/reject",
        json={
            "reviewer": "Environmental Officer",
            "comments": "Insufficient evidence.",
        },
    )

    assert response.status_code == 200
    assert response.json()["decision"] == "rejected"


@pytest.mark.anyio
async def test_duplicate_approval_is_rejected(
    client,
    create_pending_investigation,
):
    investigation_id = create_pending_investigation

    payload = {"reviewer": "Officer A"}

    first_response = client.post(
        f"/investigations/{investigation_id}/approve",
        json=payload,
    )

    second_response = client.post(
        f"/investigations/{investigation_id}/reject",
        json=payload,
    )

    assert first_response.status_code == 200
    assert second_response.status_code == 409


@pytest.mark.anyio
async def test_invalid_reviewer_is_rejected(
    client,
    create_pending_investigation,
):
    investigation_id = create_pending_investigation

    response = client.post(
        f"/investigations/{investigation_id}/approve",
        json={"reviewer": ""},
    )

    assert response.status_code == 422


@pytest.mark.anyio
async def test_get_approval_endpoint(
    client,
    create_pending_investigation,
):
    investigation_id = create_pending_investigation

    client.post(
        f"/investigations/{investigation_id}/approve",
        json={"reviewer": "Officer A"},
    )

    response = client.get(
        f"/investigations/{investigation_id}/approval"
    )

    assert response.status_code == 200
    assert response.json()["reviewer"] == "Officer A"


@pytest.mark.anyio
async def test_missing_approval_returns_404(client):

    response = client.get(
        "/investigations/9999/approval"
    )

    assert response.status_code == 404
