"""Dashboard summary endpoint (rollup of key metrics for the header)."""
from datetime import datetime, timezone

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

import models
import schemas
from database import get_db

router = APIRouter(prefix="/api/dashboard", tags=["dashboard"])


@router.get("/summary", response_model=schemas.DashboardSummary)
def summary(db: Session = Depends(get_db)):
    total_readings = db.query(models.SensorReading).count()
    open_alerts = db.query(models.Alert).filter(models.Alert.status == "open").count()
    critical_alerts = (
        db.query(models.Alert)
        .filter(models.Alert.status == "open", models.Alert.severity == "critical")
        .count()
    )
    online_devices = db.query(models.Device).filter(models.Device.status == "online").count()
    latest = (
        db.query(models.SensorReading)
        .order_by(models.SensorReading.created_at.desc())
        .first()
    )

    # Fall back to "now" if no readings yet.
    updated_at = (
        latest.created_at
        if latest and latest.created_at
        else datetime.now(timezone.utc)
    )

    return schemas.DashboardSummary(
        total_readings=total_readings,
        open_alerts=open_alerts,
        critical_alerts=critical_alerts,
        online_devices=online_devices,
        latest_reading=latest,
        updated_at=updated_at,
    )
