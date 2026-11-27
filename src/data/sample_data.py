from datetime import datetime, timezone

from src.data.models import (
    AirQualityReading,
    WindReading,
    IndustrialFacility,
)


# ---------------------------------------
# 1. Ambient air quality readings
# ---------------------------------------

AIR_QUALITY_READINGS = [
    AirQualityReading(
        station_id="ST-001",
        timestamp=datetime(2026, 11, 25, 8, 0, tzinfo=timezone.utc),
        pm25=65,
        pm10=110,
        so2=18,
        nox=32,
    ),
    AirQualityReading(
        station_id="ST-001",
        timestamp=datetime(2026, 11, 25, 9, 0, tzinfo=timezone.utc),
        pm25=95,
        pm10=145,
        so2=25,
        nox=45,
    ),
    AirQualityReading(
        station_id="ST-001",
        timestamp=datetime(2026, 11, 25, 10, 0, tzinfo=timezone.utc),
        pm25=180,
        pm10=240,
        so2=48,
        nox=85,
    ),
]


# ---------------------------------------
# 2. Meteorological readings
# ---------------------------------------

WIND_READINGS = [
    WindReading(
        timestamp=datetime(2026, 11, 25, 8, 0, tzinfo=timezone.utc),
        wind_speed=3.2,
        wind_direction=90,
    ),
    WindReading(
        timestamp=datetime(2026, 11, 25, 9, 0, tzinfo=timezone.utc),
        wind_speed=3.8,
        wind_direction=95,
    ),
    WindReading(
        timestamp=datetime(2026, 11, 25, 10, 0, tzinfo=timezone.utc),
        wind_speed=4.1,
        wind_direction=100,
    ),
]


# ---------------------------------------
# 3. Industrial facility information
# ---------------------------------------

INDUSTRIAL_FACILITIES = [
    IndustrialFacility(
        facility_id="FAC-001",
        facility_name="Alpha Cement Works",
        industry_type="Cement Manufacturing",
        latitude=13.0900,
        longitude=80.2700,
        permitted_pm25=80,
        permitted_so2=50,
    ),
    IndustrialFacility(
        facility_id="FAC-002",
        facility_name="Beta Thermal Plant",
        industry_type="Thermal Power",
        latitude=13.1000,
        longitude=80.2800,
        permitted_pm25=75,
        permitted_so2=45,
    ),
    IndustrialFacility(
        facility_id="FAC-003",
        facility_name="Gamma Chemical Industries",
        industry_type="Chemical Manufacturing",
        latitude=13.1100,
        longitude=80.2900,
        permitted_pm25=60,
        permitted_so2=40,
    ),
]