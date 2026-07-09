from sqlalchemy import Column, String, DateTime, Boolean, Text
from app.database import Base
import uuid
import json
from datetime import datetime

class Command(Base):
    __tablename__ = "commands"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    device_id = Column(String(36), nullable=False, index=True)
    command_type = Column(String(50), nullable=False)
    command_data = Column(Text, default="{}")
    status = Column(String(20), default="pending")
    result = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    executed_at = Column(DateTime, nullable=True)
    
    def to_dict(self):
        return {
            "id": self.id,
            "command_type": self.command_type,
            "status": self.status,
            "result": json.loads(self.result) if self.result else None,
            "created_at": self.created_at.isoformat(),
            "executed_at": self.executed_at.isoformat() if self.executed_at else None
        }
