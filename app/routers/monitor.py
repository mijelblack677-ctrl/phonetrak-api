from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.device import Device
from app.models.command import Command

router = APIRouter(prefix="/v1/monitor", tags=["monitor"])

@router.get("/location/{user_id}")
async def get_location(user_id: str, db: Session = Depends(get_db)):
    """Monitor app gets real-time location"""
    devices = db.query(Device).filter(
        Device.user_id == user_id,
        Device.is_online == True
    ).order_by(Device.last_seen.desc()).all()
    
    return [
        {
            "device_id": str(d.id),
            "device_name": d.device_name,
            "latitude": d.last_latitude,
            "longitude": d.last_longitude,
            "accuracy": d.last_accuracy,
            "battery": d.last_battery,
            "wifi": d.last_wifi,
            "last_seen": d.last_seen.isoformat(),
            "is_locked": d.is_locked
        }
        for d in devices
    ]

@router.get("/commands/{user_id}")
async def get_command_history(user_id: str, db: Session = Depends(get_db)):
    """Get command history for user's devices"""
    devices = db.query(Device).filter(Device.user_id == user_id).all()
    device_ids = [d.id for d in devices]
    
    commands = db.query(Command).filter(
        Command.device_id.in_(device_ids)
    ).order_by(Command.created_at.desc()).limit(50).all()
    
    return [c.to_dict() for c in commands]

@router.get("/photos/{user_id}")
async def get_captured_photos(user_id: str, db: Session = Depends(get_db)):
    """Get photos captured from camera commands"""
    devices = db.query(Device).filter(Device.user_id == user_id).all()
    device_ids = [d.id for d in devices]
    
    photo_commands = db.query(Command).filter(
        Command.device_id.in_(device_ids),
        Command.command_type.in_(["camera_front", "camera_back"]),
        Command.status == "executed"
    ).order_by(Command.executed_at.desc()).limit(20).all()
    
    return [
        {
            "command_id": str(c.id),
            "type": c.command_type,
            "result": c.result,
            "captured_at": c.executed_at.isoformat()
        }
        for c in photo_commands
    ]
