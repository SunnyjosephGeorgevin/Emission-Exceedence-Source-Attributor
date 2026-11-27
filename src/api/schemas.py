
from pydantic import BaseModel, Field


class InvestigationRequest(BaseModel):
    station_id: str = Field(min_length=1, max_length=50)
    station_latitude: float = Field(ge=-90, le=90)
    station_longitude: float = Field(ge=-180, le=180)


class ApprovalRequest(BaseModel):
    reviewer: str = Field(min_length=1, max_length=100)
    comments: str | None = Field(default=None, max_length=1000)


class ApprovalResponse(BaseModel):
    investigation_id: int
    decision: str
    reviewer: str
    comments: str | None
    decided_at: str
    status: str
