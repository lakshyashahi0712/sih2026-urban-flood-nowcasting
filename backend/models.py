"""SQLAlchemy ORM models for the water quality monitoring system."""
from datetime import datetime, timezone
from sqlalchemy import Column, Integer, Float, String, DateTime, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from database import Base


def utcnow():
    """Timezone-aware UTC timestamp used as a default for datetimes."""
    return datetime.now(timezone.utc)


class SensorReading(Base):
    """A single water-quality measurement from one location/sensor unit."""
    __tablename__ = "sensor_readings"

    id = Column(Integer, primary_key=True, index=True)
    device_id = Column(String, index=True, default="water-node-01")

    # Water quality parameters
    ph = Column(Float, nullable=True)
    temperature = Column(Float, nullable=True)      # Celsius
    turbidity = Column(Float, nullable=True)        # NTU
    dissolved_oxygen = Column(Float, nullable=True) # mg/L
    conductivity = Column(Float, nullable=True)     # µS/cm
    tds = Column(Float, nullable=True)              # mg/L

    # Location
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)
    location_name = Column(String, nullable=True)

    # Flag set by the anomaly-detection service
    is_anomaly = Column(Boolean, default=False)
    anomaly_reason = Column(String, nullable=True)

    created_at = Column(DateTime(timezone=True), default=utcnow, index=True)

    alerts = relationship("Alert", back_populates="reading", cascade="all, delete-orphan")


class Alert(Base):
    """An anomaly or out-of-range alert raised for a sensor reading."""
    __tablename__ = "alerts"

    id = Column(Integer, primary_key=True, index=True)
    reading_id = Column(Integer, ForeignKey("sensor_readings.id"), nullable=True)
    device_id = Column(String, index=True)

    parameter = Column(String)         # e.g. "ph", "turbidity"
    severity = Column(String, default="medium")  # low | medium | high | critical
    message = Column(String)
    value = Column(Float, nullable=True)

    # "open" while active, "resolved" once conditions return to normal
    status = Column(String, default="open")
    is_read = Column(Boolean, default=False)

    created_at = Column(DateTime(timezone=True), default=utcnow, index=True)
    resolved_at = Column(DateTime(timezone=True), nullable=True)

    reading = relationship("SensorReading", back_populates="alerts")


class Device(Base):
    """Registered IoT monitoring device."""
    __tablename__ = "devices"

    id = Column(Integer, primary_key=True, index=True)
    device_id = Column(String, unique=True, index=True)
    name = Column(String)
    location_name = Column(String, nullable=True)
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)
    status = Column(String, default="online")  # online | offline
    last_seen = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), default=utcnow)
