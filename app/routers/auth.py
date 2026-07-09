from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from passlib.context import CryptContext
from app.database import get_db
from app.models.user import User, Tier
import secrets
import string
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/v1/auth", tags=["auth"])

# Configure bcrypt with shorter passwords
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto", bcrypt__truncate_error=True)

class RegisterRequest(BaseModel):
    email: str
    passphrase: str
    tier: str = "free"

class LoginRequest(BaseModel):
    email: str
    passphrase: str

def generate_recovery_code():
    chars = string.ascii_uppercase + string.digits
    return ''.join(secrets.choice(chars) for _ in range(12))

def hash_password(password: str) -> str:
    """Hash password, truncating to 72 bytes for bcrypt"""
    # Ensure password is not too long for bcrypt
    password_bytes = password.encode('utf-8')
    if len(password_bytes) > 72:
        password_bytes = password_bytes[:72]
    return pwd_context.hash(password_bytes.decode('utf-8', errors='ignore'))

def verify_password(password: str, hashed: str) -> bool:
    """Verify password with truncation"""
    password_bytes = password.encode('utf-8')
    if len(password_bytes) > 72:
        password_bytes = password_bytes[:72]
    return pwd_context.verify(password_bytes.decode('utf-8', errors='ignore'), hashed)

@router.post("/register")
async def register(request: RegisterRequest, db: Session = Depends(get_db)):
    try:
        existing = db.query(User).filter(User.email == request.email).first()
        if existing:
            raise HTTPException(status_code=400, detail="Email already registered")
        
        recovery = generate_recovery_code()
        
        user = User(
            email=request.email,
            passphrase=hash_password(request.passphrase),
            tier=request.tier if request.tier in [t.value for t in Tier] else Tier.FREE.value,
            recovery_code=recovery
        )
        
        db.add(user)
        db.commit()
        db.refresh(user)
        
        return {
            "user": user.to_dict(),
            "recovery_code": recovery,
            "message": "Save your recovery code!"
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Registration error: {e}", exc_info=True)
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Registration failed: {str(e)}")

@router.post("/login")
async def login(request: LoginRequest, db: Session = Depends(get_db)):
    try:
        user = db.query(User).filter(User.email == request.email).first()
        if not user:
            raise HTTPException(status_code=401, detail="Invalid credentials")
        
        if not verify_password(request.passphrase, user.passphrase):
            raise HTTPException(status_code=401, detail="Invalid credentials")
        
        return {
            "user_id": user.id,
            "tier": user.tier,
            "recovery_code": user.recovery_code
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Login error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Login failed: {str(e)}")

@router.post("/recover")
async def recover(email: str, recovery_code: str, db: Session = Depends(get_db)):
    user = db.query(User).filter(
        User.email == email,
        User.recovery_code == recovery_code
    ).first()
    if not user:
        raise HTTPException(status_code=401, detail="Invalid recovery details")
    return {"user_id": user.id, "tier": user.tier}
