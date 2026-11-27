
from datetime import datetime

from pydantic import BaseModel, Field


class AirQualityReading(BaseModel):
    station_id: str
    timestamp: datetime

    pm25: float = Field(ge=0)
    pm10: float = Field(ge=0)
    so2: float = Field(ge=0)
    nox: float = Field(ge=0)


class WindReading(BaseModel):
    timestamp: datetime

    wind_speed: float = Field(ge=0)
    wind_direction: float = Field(ge=0, le=360)


class IndustrialFacility(BaseModel):
    facility_id: str
    facility_name: str
    industry_type: str

    latitude: float = Field(ge=-90, le=90)
    longitude: float = Field(ge=-180, le=180)

    permitted_pm25: float = Field(ge=0)
    permitted_so2: float = Field(ge=0)


class LLMInterpretation(BaseModel):
    ambient_analysis: str
    wind_analysis: str
    facility_analysis: str

    limitations: list[str]
    recommendations: list[str]
