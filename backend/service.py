"""Business logic for ingesting readings and raising alerts."""
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from backend import models
from backend.ml_anomaly import detector
from backend.websocket_manager import manager


def register_device(db: Session, reading) -> models.Device:
    """Create/update the device row so the dashboard shows live status."""
    device = db.query(models.Device).filter_by(device_id=reading.device_id).first()
    if device is None:
        device = models.Device(
            device_id=reading.device_id,
            name=f"Sensor Node {reading.device_id}",
            location_name=reading.location_name,
            latitude=reading.latitude,
            longitude=reading.longitude,
        )
        db.add(device)
    else:
        device.status = "online"
        device.last_seen = datetime.now(timezone.utc)
        if reading.location_name:
            device.location_name = reading.location_name
        if reading.latitude is not None:
            device.latitude = reading.latitude
        if reading.longitude is not None:
            device.longitude = reading.longitude
    return device


def process_reading(db: Session, reading: models.SensorReading) -> models.Alert | None:
    """Run anomaly detection and create an alert if needed.

    Returns the created Alert (if any) so the caller can broadcast it.
    """
    # Build the value dict used by the detector from the current reading.
    values = {
        "ph": reading.ph,
        "temperature": reading.temperature,
        "turbidity": reading.turbidity,
        "dissolved_oxygen": reading.dissolved_oxygen,
        "conductivity": reading.conductivity,
        "tds": reading.tds,
    }

    # Recent history (excluding the just-saved reading) for baseline training.
    history = [
        {
            "ph": r.ph,
            "temperature": r.temperature,
            "turbidity": r.turbidity,
            "dissolved_oxygen": r.dissolved_oxygen,
            "conductivity": r.conductivity,
            "tds": r.tds,
        }
        for r in db.query(models.SensorReading)
        .filter(models.SensorReading.id != reading.id)
        .order_by(models.SensorReading.created_at.desc())
        .limit(600)
        .all()
    ]

    result = detector.analyze(values, history)

    reading.is_anomaly = result["is_anomaly"]
    reading.anomaly_reason = result["reason"]
    db.commit()

    if not result["is_anomaly"]:
        return None

    alert = models.Alert(
        reading_id=reading.id,
        device_id=reading.device_id,
        parameter=result["parameter"],
        severity=result["severity"],
        message=result["reason"],
        value=values.get(result["parameter"]),
        status="open",
    )
    db.add(alert)
    db.commit()
    db.refresh(alert)
    return alert


async def ingest_reading(db: Session, data: dict) -> dict:
    """Full pipeline for a new sensor reading:
    persist -> detect -> alert -> broadcast live to dashboard clients.
    """
    reading = models.SensorReading(**data)
    db.add(reading)
    db.commit()
    db.refresh(reading)

    register_device(db, reading)
    db.commit()

    alert = process_reading(db, reading)

    # Broadcast the live reading (and any new alert) to every connected client.
    await manager.broadcast({
        "type": "reading",
        "data": reading_to_dict(reading),
    })
    if alert is not None:
        await manager.broadcast({
            "type": "alert",
            "data": alert_to_dict(alert),
        })

    return {"reading": reading_to_dict(reading), "alert": alert_to_dict(alert) if alert else None}


def reading_to_dict(r: models.SensorReading) -> dict:
    return {
        "id": r.id,
        "device_id": r.device_id,
        "ph": r.ph,
        "temperature": r.temperature,
        "turbidity": r.turbidity,
        "dissolved_oxygen": r.dissolved_oxygen,
        "conductivity": r.conductivity,
        "tds": r.tds,
        "latitude": r.latitude,
        "longitude": r.longitude,
        "location_name": r.location_name,
        "is_anomaly": r.is_anomaly,
        "anomaly_reason": r.anomaly_reason,
        "created_at": r.created_at.isoformat() if r.created_at else None,
    }


def alert_to_dict(a: models.Alert) -> dict:
    return {
        "id": a.id,
        "reading_id": a.reading_id,
        "device_id": a.device_id,
        "parameter": a.parameter,
        "severity": a.severity,
        "message": a.message,
        "value": a.value,
        "status": a.status,
        "is_read": a.is_read,
        "created_at": a.created_at.isoformat() if a.created_at else None,
        "resolved_at": a.resolved_at.isoformat() if a.resolved_at else None,
    }
