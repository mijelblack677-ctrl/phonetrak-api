from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.database import init_db
from app.routers import auth, devices, commands, monitor

app = FastAPI(
    title="PhoneTrak API",
    description="Anti-Theft Device Tracking Platform",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(devices.router)
app.include_router(commands.router)
app.include_router(monitor.router)

@app.on_event("startup")
async def startup():
    init_db()

@app.get("/")
async def root():
    return {"service": "PhoneTrak API", "status": "operational"}

@app.get("/health")
async def health():
    return {"status": "healthy"}

# WebSocket Dashboard
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
import os

# Mount static files
if os.path.exists("static"):
    app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard():
    static_path = os.path.join(os.path.dirname(__file__), "..", "static", "dashboard.html")
    if os.path.exists(static_path):
        with open(static_path) as f:
            return f.read()
    return "<h1>Dashboard not found</h1>"

# Proxy WebSocket HTTP endpoints
from app.websocket_server import handle_http_request
from fastapi import Request

@app.get("/ws/devices")
async def ws_get_devices():
    result = await handle_http_request("GET", "/ws/devices")
    return result

@app.get("/ws/data")
async def ws_get_data(device_id: str = "", data_type: str = "all"):
    result = await handle_http_request("GET", "/ws/data", {"device_id": device_id, "data_type": data_type})
    return result

@app.post("/ws/command")
async def ws_post_command(request: Request):
    body = await request.json()
    result = await handle_http_request("POST", "/ws/command", body)
    return result
