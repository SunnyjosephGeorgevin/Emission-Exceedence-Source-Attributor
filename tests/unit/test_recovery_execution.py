
import pytest

from src.database.connection import get_connection
from src.database.repository import InvestigationRepository
from src.database.checkpoint_repository import CheckpointRepository
from src.database.schema import SCHEMA

from src.orchestration.supervisor import Supervisor


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


async def create_interrupted_investigation(
    investigation_repo,
    checkpoint_repo,
    stage,
    state,
):

    investigation_id = await investigation_repo.create_investigation(
        station_id="ST-001",
        status="running",
        current_stage=stage,
    )

    await checkpoint_repo.save_checkpoint(
        investigation_id=investigation_id,
        stage=stage,
        state=state,
    )

    return investigation_id


@pytest.mark.anyio
async def test_resume_from_data_retrieved(
    tmp_path,
    monkeypatch,
):

    database_path = tmp_path / "resume_data.db"

    await setup_test_database(database_path, monkeypatch)

    investigation_repo = InvestigationRepository()
    checkpoint_repo = CheckpointRepository()

    saved_state = {
        "air_quality_readings": [
            {
                "station_id": "ST-001",
                "timestamp": "2026-11-25T10:00:00+00:00",
                "pm25": 180,
                "pm10": 240,
                "so2": 48,
                "nox": 85,
            }
        ],
        "wind_readings": [
            {
                "timestamp": "2026-11-25T10:00:00+00:00",
                "wind_speed": 4.1,
                "wind_direction": 100,
            }
        ],
        "facilities": [
            {
                "facility_id": "FAC-001",
                "facility_name": "Alpha Cement Works",
                "industry_type": "Cement Manufacturing",
                "latitude": 13.09,
                "longitude": 80.27,
                "permitted_pm25": 80,
                "permitted_so2": 50,
            }
        ],
    }

    investigation_id = await create_interrupted_investigation(
        investigation_repo,
        checkpoint_repo,
        "data_retrieved",
        saved_state,
    )

    supervisor = Supervisor(
        station_latitude=13.08,
        station_longitude=80.26,
    )

    python_called = False
    llm_called = False

    def fake_run_investigation(
        air_quality_readings,
        wind_readings,
        facilities,
    ):
        nonlocal python_called

        python_called = True

        assert len(air_quality_readings) == 1
        assert len(wind_readings) == 1
        assert len(facilities) == 1

        return {
            "status": "success",
            "station_id": "ST-001",
            "exceedance_result": {
                "is_exceedance": True,
                "exceedance_count": 1,
                "exceedances": [],
            },
            "investigation_plan": {
                "recommendations": [],
            },
        }

    async def fake_llm_interpretation(result):
        nonlocal llm_called

        llm_called = True

        result["llm_interpretation"] = {
            "ambient_analysis": "Test analysis",
        }

        result["llm_interpretation_status"] = (
            "passed_basic_checks"
        )

        return result

    monkeypatch.setattr(
        supervisor,
        "run_investigation",
        fake_run_investigation,
    )

    monkeypatch.setattr(
        supervisor,
        "_run_llm_interpretation",
        fake_llm_interpretation,
    )

    result = await supervisor.resume_investigation(
        investigation_id
    )

    assert python_called is True
    assert llm_called is True

    assert result["status"] == "success"
    assert result["review_status"] == "awaiting_approval"

    saved = await investigation_repo.get_investigation(
        investigation_id
    )

    assert saved["investigation"]["status"] == "awaiting_approval"


@pytest.mark.anyio
async def test_resume_from_python_completed(
    tmp_path,
    monkeypatch,
):

    database_path = tmp_path / "resume_python.db"

    await setup_test_database(database_path, monkeypatch)

    investigation_repo = InvestigationRepository()
    checkpoint_repo = CheckpointRepository()

    saved_result = {
        "status": "success",
        "station_id": "ST-001",
        "investigation_id": 2,
        "exceedance_result": {
            "is_exceedance": True,
            "exceedance_count": 1,
            "exceedances": [],
        },
        "investigation_plan": {
            "recommendations": [],
        },
    }

    investigation_id = await create_interrupted_investigation(
        investigation_repo,
        checkpoint_repo,
        "python_investigation_completed",
        {
            "investigation_result": saved_result,
        },
    )

    supervisor = Supervisor(
        station_latitude=13.08,
        station_longitude=80.26,
    )

    async def fake_llm_interpretation(result):

        result["llm_interpretation"] = {
            "ambient_analysis": "Recovered analysis",
        }

        result["llm_interpretation_status"] = (
            "passed_basic_checks"
        )

        return result

    monkeypatch.setattr(
        supervisor,
        "_run_llm_interpretation",
        fake_llm_interpretation,
    )

    result = await supervisor.resume_investigation(
        investigation_id
    )

    assert result["status"] == "success"

    assert result["llm_interpretation_status"] == (
        "passed_basic_checks"
    )

    assert result["review_status"] == "awaiting_approval"

    saved = await investigation_repo.get_investigation(
        investigation_id
    )

    assert saved["investigation"]["status"] == "awaiting_approval"


@pytest.mark.anyio
async def test_resume_from_llm_completed_without_repeating_llm(
    tmp_path,
    monkeypatch,
):

    database_path = tmp_path / "resume_llm.db"

    await setup_test_database(database_path, monkeypatch)

    investigation_repo = InvestigationRepository()
    checkpoint_repo = CheckpointRepository()

    saved_result = {
        "status": "success",
        "station_id": "ST-001",
        "llm_interpretation": {
            "ambient_analysis": "Previously completed analysis",
        },
        "llm_interpretation_status": "passed_basic_checks",
    }

    investigation_id = await create_interrupted_investigation(
        investigation_repo,
        checkpoint_repo,
        "llm_interpretation_completed",
        {
            "investigation_result": saved_result,
        },
    )

    supervisor = Supervisor(
        station_latitude=13.08,
        station_longitude=80.26,
    )

    llm_called = False

    async def fake_llm_interpretation(result):
        nonlocal llm_called

        llm_called = True

        return result

    monkeypatch.setattr(
        supervisor,
        "_run_llm_interpretation",
        fake_llm_interpretation,
    )

    result = await supervisor.resume_investigation(
        investigation_id
    )

    assert llm_called is False

    assert result["llm_interpretation_status"] == (
        "passed_basic_checks"
    )

    assert result["review_status"] == "awaiting_approval"

    saved = await investigation_repo.get_investigation(
        investigation_id
    )

    assert saved["investigation"]["status"] == "awaiting_approval"
