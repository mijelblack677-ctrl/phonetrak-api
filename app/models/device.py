from sqlalchemy import Column, String, Float, DateTime, Boolean, Integer
from app.database import Base
import uuid
from datetime import datetime

class Device(Base):
    __tablename__ = "devices"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), nullable=False, index=True)
    device_name = Column(String(255))
    device_id = Column(String(255), unique=True)
    sim_serial = Column(String(100))
    phone_number = Column(String(20))
    last_latitude = Column(Float)
    last_longitude = Column(Float)
    last_accuracy = Column(Float)
    last_battery = Column(Integer)
    last_wifi = Column(String(255))
    last_ip = Column(String(50))
    is_online = Column(Boolean, default=False)
    is_locked = Column(Boolean, default=False)
    tier_enabled = Column(String(20), default="free")
    last_seen = Column(DateTime, default=datetime.utcnow)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            "id": self.id,
            "device_name": self.device_name,
            "last_latitude": self.last_latitude,
            "last_longitude": self.last_longitude,
            "last_accuracy": self.last_accuracy,
            "last_battery": self.last_battery,
            "last_wifi": self.last_wifi,
            "is_online": self.is_online,
            "is_locked": self.is_locked,
            "tier_enabled": self.tier_enabled,
            "last_seen": self.last_seen.isoformat() if self.last_seen else None
        }
