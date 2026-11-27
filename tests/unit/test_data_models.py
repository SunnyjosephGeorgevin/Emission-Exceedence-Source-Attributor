from src.data.sample_data import (
    AIR_QUALITY_READINGS,
    WIND_READINGS,
    INDUSTRIAL_FACILITIES,
)


def test_air_quality_data():
    assert len(AIR_QUALITY_READINGS) == 3
    assert AIR_QUALITY_READINGS[2].pm25 == 180


def test_wind_data():
    assert len(WIND_READINGS) == 3
    assert WIND_READINGS[2].wind_speed == 4.1


def test_facility_data():
    assert len(INDUSTRIAL_FACILITIES) == 3
    assert INDUSTRIAL_FACILITIES[0].facility_id == "FAC-001"