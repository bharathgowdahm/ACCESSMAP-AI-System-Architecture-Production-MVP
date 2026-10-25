"""Pydantic v2 schemas for strict data validation."""
from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field


class MobilityProfileSchema(BaseModel):
    name: str = Field(..., example="Manual Wheelchair")
    max_slope_pct: float = Field(default=8.0, ge=0.0, le=30.0)
    requires_step_free: bool = Field(default=True)
    min_width_meters: float = Field(default=0.9, ge=0.5, le=5.0)
    avoid_unpaved: bool = Field(default=True)
    avoid_unverified_obstacles: bool = Field(default=True)


class BarrierReportCreate(BaseModel):
    title: str = Field(..., min_length=3, max_length=120)
    category: str = Field(..., example="Stairs")
    latitude: float = Field(..., ge=-90.0, le=90.0)
    longitude: float = Field(..., ge=-180.0, le=180.0)
    description: str = Field(..., min_length=5, max_length=1000)
    severity: int = Field(default=3, ge=1, le=5)


class BarrierReportOut(BaseModel):
    id: str
    title: str
    category: str
    latitude: float
    longitude: float
    description: str
    severity: int
    status: str
    trust_score: float
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class RouteRequest(BaseModel):
    origin_lat: float = Field(..., ge=-90.0, le=90.0)
    origin_lon: float = Field(..., ge=-180.0, le=180.0)
    dest_lat: float = Field(..., ge=-90.0, le=90.0)
    dest_lon: float = Field(..., ge=-180.0, le=180.0)
    profile: MobilityProfileSchema
