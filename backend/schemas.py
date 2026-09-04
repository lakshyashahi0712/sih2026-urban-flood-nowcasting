"""Pydantic schemas for request/response validation."""
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field


class ReadingBase(BaseModel):
    device_id: str = "water-node-01"
    ph: Optional[float] = None
    temperature: Optional[float] = None
    turbidity: Optional[float] = None
    dissolved_oxygen: Optional[float] = None
    conductivity: Optional[float] = None
    tds: Optional[float] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    location_name: Optional[str] = None


class ReadingCreate(ReadingBase):
    """Payload sent by the Arduino/ESP device when posting a reading."""
    pass


class Reading(ReadingBase):
    id: int
    is_anomaly: bool
    anomaly_reason: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True


class ReadingList(BaseModel):
    total: int
    items: List[Reading]


class ReadingStats(BaseModel):
    """Aggregated statistics for a parameter over a time window."""
    parameter: str
    min: float
    max: float
    mean: float
    std: float
    current: float
    count: int


class Alert(BaseModel):
    id: int
    reading_id: Optional[int]
    device_id: str
    parameter: str
    severity: str
    message: str
    value: Optional[float]
    status: str
    is_read: bool
    created_at: datetime
    resolved_at: Optional[datetime]

    class Config:
        from_attributes = True


class AlertList(BaseModel):
    total: int
    open_count: int
    items: List[Alert]


class Device(BaseModel):
    id: int
    device_id: str
    name: str
    location_name: Optional[str]
    latitude: Optional[float]
    longitude: Optional[float]
    status: str
    last_seen: Optional[datetime]
    created_at: datetime

    class Config:
        from_attributes = True


class DashboardSummary(BaseModel):
    """Rollup used by the dashboard header."""
    total_readings: int
    open_alerts: int
    critical_alerts: int
    online_devices: int
    latest_reading: Optional[Reading]
    updated_at: datetime
