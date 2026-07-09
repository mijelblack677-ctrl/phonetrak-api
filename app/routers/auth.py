from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel, EmailStr
from passlib.context import CryptContext
from app.database import get_db
from app.models.user import User, Tier
import secrets
import string

router = APIRouter(prefix="/v1/auth", tags=["auth"])
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

class RegisterRequest(BaseModel):
    email: EmailStr
    passphrase: str
    tier: str = "free"

class LoginRequest(BaseModel):
    email: EmailStr
    passphrase: str

def generate_recovery_code():
    chars = string.ascii_uppercase + string.digits
    return ''.join(secrets.choice(chars) for _ in range(12))

@router.post("/register")
async def register(request: RegisterRequest, db: Session = Depends(get_db)):
    existing = db.query(User).filter(User.email == request.email).first()
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    recovery = generate_recovery_code()
    
    user = User(
        email=request.email,
        passphrase=pwd_context.hash(request.passphrase),
        tier=Tier(request.tier) if request.tier in [t.value for t in Tier] else Tier.FREE,
        recovery_code=recovery
    )
    
    db.add(user)
    db.commit()
    db.refresh(user)
    
    return {
        "user": user.to_dict(),
        "recovery_code": recovery,
        "message": "Save your recovery code! It cannot be recovered."
    }

@router.post("/login")
async def login(request: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == request.email).first()
    if not user or not pwd_context.verify(request.passphrase, user.passphrase):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    return {
        "user_id": str(user.id),
        "tier": user.tier.value,
        "recovery_code": user.recovery_code
    }

@router.post("/recover")
async def recover(email: str, recovery_code: str, db: Session = Depends(get_db)):
    user = db.query(User).filter(
        User.email == email,
        User.recovery_code == recovery_code
    ).first()
    if not user:
        raise HTTPException(status_code=401, detail="Invalid recovery details")
    
    return {"user_id": str(user.id), "tier": user.tier.value}
