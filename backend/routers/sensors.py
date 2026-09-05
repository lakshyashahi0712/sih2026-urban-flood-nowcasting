"""REST endpoints for sensor readings."""
from datetime import datetime, timedelta
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import func

from backend import models
from backend import schemas
from backend.database import get_db
from backend.service import ingest_reading

router = APIRouter(prefix="/api/readings", tags=["sensors"])


@router.post("", response_model=schemas.Reading, status_code=201)
async def create_reading(
    payload: schemas.ReadingCreate,
    db: Session = Depends(get_db),
):
    """Ingest a new reading from a sensor device. Runs anomaly detection and
    broadcasts the result over the WebSocket in real time."""
    result = await ingest_reading(db, payload.model_dump())
    # Re-fetch with relationship info for the response model.
    return db.query(models.SensorReading).get(result["reading"]["id"])


@router.get("", response_model=schemas.ReadingList)
def list_readings(
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    device_id: Optional[str] = None,
    from_: Optional[datetime] = Query(None, alias="from"),
    to: Optional[datetime] = None,
    db: Session = Depends(get_db),
):
    """List readings with optional device / time filtering."""
    q = db.query(models.SensorReading)
    if device_id:
        q = q.filter(models.SensorReading.device_id == device_id)
    if from_:
        q = q.filter(models.SensorReading.created_at >= from_)
    if to:
        q = q.filter(models.SensorReading.created_at <= to)

    total = q.count()
    items = (
        q.order_by(models.SensorReading.created_at.desc())
        .offset(offset)
        .limit(limit)
        .all()
    )
    return schemas.ReadingList(total=total, items=items)


@router.get("/latest", response_model=schemas.Reading)
def latest_reading(db: Session = Depends(get_db)):
    reading = (
        db.query(models.SensorReading)
        .order_by(models.SensorReading.created_at.desc())
        .first()
    )
    if reading is None:
        raise HTTPException(status_code=404, detail="No readings available yet")
    return reading


@router.get("/stats", response_model=schemas.ReadingStats)
def reading_stats(
    parameter: str = Query(..., description="One of ph, temperature, turbidity, ..."),
    hours: int = Query(24, ge=1, le=720),
    db: Session = Depends(get_db),
):
    """Aggregate statistics for a single parameter over the last N hours."""
    param_col = getattr(models.SensorReading, parameter, None)
    if param_col is None:
        raise HTTPException(status_code=400, detail=f"Unknown parameter: {parameter}")

    since = datetime.utcnow() - timedelta(hours=hours)
    rows = (
        db.query(func.min(param_col), func.max(param_col),
                 func.avg(param_col), func.stddev(param_col))
        .filter(models.SensorReading.created_at >= since)
        .filter(param_col.isnot(None))
        .first()
    )
    latest = (
        db.query(param_col)
        .filter(models.SensorReading.created_at >= since)
        .filter(param_col.isnot(None))
        .order_by(models.SensorReading.created_at.desc())
        .first()
    )
    mn, mx, avg, std = rows
    if mn is None:
        raise HTTPException(status_code=404, detail="No data in this window")

    return schemas.ReadingStats(
        parameter=parameter,
        min=float(mn),
        max=float(mx),
        mean=float(avg),
        std=float(std or 0.0),
        current=float(latest[0]),
        count=db.query(models.SensorReading)
        .filter(models.SensorReading.created_at >= since)
        .filter(param_col.isnot(None))
        .count(),
    )
