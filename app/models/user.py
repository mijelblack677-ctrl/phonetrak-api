from sqlalchemy import Column, String, DateTime
from app.database import Base
import uuid
import enum
from datetime import datetime

class Tier(str, enum.Enum):
    FREE = "free"
    PRO = "pro"
    ULTIMATE = "ultimate"

class User(Base):
    __tablename__ = "users"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    email = Column(String(255), unique=True, nullable=False)
    passphrase = Column(String(255), nullable=False)
    tier = Column(String(20), default=Tier.FREE.value)
    recovery_code = Column(String(16), unique=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            "id": self.id,
            "email": self.email,
            "tier": self.tier,
            "created_at": self.created_at.isoformat()
        }
