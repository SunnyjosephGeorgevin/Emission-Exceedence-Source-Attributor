from src.orchestration.supervisor import Supervisor
from src.data.sample_data import (
    AIR_QUALITY_READINGS,
    WIND_READINGS,
    INDUSTRIAL_FACILITIES,
)


def test_supervisor_runs_complete_investigation():
    supervisor = Supervisor(
        station_latitude=13.0800,
        station_longitude=80.2600,
    )

    result = supervisor.run_investigation(
        air_quality_readings=AIR_QUALITY_READINGS,
        wind_readings=WIND_READINGS,
        facilities=INDUSTRIAL_FACILITIES,
    )

    assert result["status"] == "success"
    assert result["exceedance_result"]["is_exceedance"] is True
    assert len(result["screened_candidates"]) == 3
    assert len(result["investigation_plan"]["recommendations"]) == 3


def test_supervisor_handles_empty_readings():
    supervisor = Supervisor(
        station_latitude=13.0800,
        station_longitude=80.2600,
    )

    result = supervisor.run_investigation(
        air_quality_readings=[],
        wind_readings=WIND_READINGS,
        facilities=INDUSTRIAL_FACILITIES,
    )

    assert result["status"] == "failed"


def test_supervisor_handles_missing_wind_data():
    supervisor = Supervisor(
        station_latitude=13.0800,
        station_longitude=80.2600,
    )

    result = supervisor.run_investigation(
        air_quality_readings=AIR_QUALITY_READINGS,
        wind_readings=[],
        facilities=INDUSTRIAL_FACILITIES,
    )

    assert result["status"] == "failed"
    assert "No matching wind reading" in result["message"]