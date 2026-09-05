"""REST endpoints for registered IoT devices."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from backend import models
from backend import schemas
from backend.database import get_db

router = APIRouter(prefix="/api/devices", tags=["devices"])


@router.get("", response_model=list[schemas.Device])
def list_devices(db: Session = Depends(get_db)):
    return db.query(models.Device).order_by(models.Device.created_at).all()


@router.get("/{device_id}", response_model=schemas.Device)
def get_device(device_id: str, db: Session = Depends(get_db)):
    device = db.query(models.Device).filter_by(device_id=device_id).first()
    if device is None:
        raise HTTPException(status_code=404, detail="Device not found")
    return device
