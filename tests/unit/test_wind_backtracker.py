from src.agents.wind_backtracker import WindBacktracker
from src.data.sample_data import (
    WIND_READINGS,
    INDUSTRIAL_FACILITIES,
)


def test_distance_is_positive():

    backtracker = WindBacktracker(
        station_latitude=13.0800,
        station_longitude=80.2600,
    )

    distance = backtracker.calculate_distance(
        INDUSTRIAL_FACILITIES[0]
    )

    assert distance > 0


def test_bearing_is_valid():

    backtracker = WindBacktracker(
        station_latitude=13.0800,
        station_longitude=80.2600,
    )

    bearing = backtracker.calculate_bearing(
        INDUSTRIAL_FACILITIES[0]
    )

    assert 0 <= bearing < 360


def test_investigation_returns_facilities():

    backtracker = WindBacktracker(
        station_latitude=13.0800,
        station_longitude=80.2600,
    )

    candidates = backtracker.investigate(
        WIND_READINGS[0],
        INDUSTRIAL_FACILITIES,
    )

    assert len(candidates) == 3

    assert "is_directionally_aligned" in candidates[0]