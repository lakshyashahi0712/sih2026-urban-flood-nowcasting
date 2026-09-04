"""REST endpoints for alerts."""
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from datetime import datetime, timezone

import models
import schemas
from database import get_db
from service import alert_to_dict
from websocket_manager import manager

router = APIRouter(prefix="/api/alerts", tags=["alerts"])


@router.get("", response_model=schemas.AlertList)
def list_alerts(
    status: Optional[str] = Query(None, description="open | resolved"),
    severity: Optional[str] = None,
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
):
    q = db.query(models.Alert)
    if status:
        q = q.filter(models.Alert.status == status)
    if severity:
        q = q.filter(models.Alert.severity == severity)

    total = q.count()
    open_count = db.query(models.Alert).filter(models.Alert.status == "open").count()
    items = q.order_by(models.Alert.created_at.desc()).offset(offset).limit(limit).all()
    return schemas.AlertList(total=total, open_count=open_count, items=items)


@router.get("/{alert_id}", response_model=schemas.Alert)
def get_alert(alert_id: int, db: Session = Depends(get_db)):
    alert = db.query(models.Alert).get(alert_id)
    if alert is None:
        raise HTTPException(status_code=404, detail="Alert not found")
    return alert


@router.patch("/{alert_id}/resolve", response_model=schemas.Alert)
async def resolve_alert(alert_id: int, db: Session = Depends(get_db)):
    """Mark an alert as resolved (e.g. operator confirms issue is handled)."""
    alert = db.query(models.Alert).get(alert_id)
    if alert is None:
        raise HTTPException(status_code=404, detail="Alert not found")
    alert.status = "resolved"
    alert.resolved_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(alert)
    await manager.broadcast({"type": "alert_update", "data": alert_to_dict(alert)})
    return alert


@router.patch("/{alert_id}/read", response_model=schemas.Alert)
def mark_read(alert_id: int, db: Session = Depends(get_db)):
    alert = db.query(models.Alert).get(alert_id)
    if alert is None:
        raise HTTPException(status_code=404, detail="Alert not found")
    alert.is_read = True
    db.commit()
    db.refresh(alert)
    return alert
