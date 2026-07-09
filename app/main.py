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
