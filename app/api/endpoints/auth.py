import os
import base64
import json
import hmac
import hashlib
import time
from fastapi import APIRouter, Depends, HTTPException, status, Header
from sqlalchemy.orm import Session
from pydantic import BaseModel
from app import models, database
from app.database import get_db, verify_password, hash_password

router = APIRouter()

SECRET_KEY = os.getenv("JWT_SECRET_KEY", "blue-learn-super-secret-key-139875418247")

def base64url_encode(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b'=').decode('utf-8')

def base64url_decode(data: str) -> bytes:
    padding = '=' * (4 - (len(data) % 4))
    return base64.urlsafe_b64decode(data + padding)

def create_jwt(payload: dict, expires_in: int = 86400 * 30) -> str:
    header = {"alg": "HS256", "typ": "JWT"}
    payload_copy = payload.copy()
    payload_copy["exp"] = int(time.time()) + expires_in
    
    header_b64 = base64url_encode(json.dumps(header).encode('utf-8'))
    payload_b64 = base64url_encode(json.dumps(payload_copy).encode('utf-8'))
    
    signature_input = f"{header_b64}.{payload_b64}".encode('utf-8')
    sig = hmac.new(SECRET_KEY.encode('utf-8'), signature_input, hashlib.sha256).digest()
    sig_b64 = base64url_encode(sig)
    
    return f"{header_b64}.{payload_b64}.{sig_b64}"

def decode_jwt(token: str) -> dict:
    try:
        parts = token.split('.')
        if len(parts) != 3:
            return None
        header_b64, payload_b64, sig_b64 = parts[0], parts[1], parts[2]
        
        signature_input = f"{header_b64}.{payload_b64}".encode('utf-8')
        expected_sig = hmac.new(SECRET_KEY.encode('utf-8'), signature_input, hashlib.sha256).digest()
        expected_sig_b64 = base64url_encode(expected_sig)
        
        if not hmac.compare_digest(sig_b64, expected_sig_b64):
            return None
            
        payload = json.loads(base64url_decode(payload_b64).decode('utf-8'))
        if payload.get("exp", 0) < time.time():
            return None
            
        return payload
    except Exception:
        return None

def get_current_user(authorization: str = Header(None), db: Session = Depends(get_db)) -> models.User:
    if not authorization:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing authorization header"
        )
    try:
        token_type, token = authorization.split(' ')
        if token_type.lower() != 'bearer':
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token type"
            )
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authorization format"
        )
        
    payload = decode_jwt(token)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token"
        )
        
    username = payload.get("sub")
    if not username:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload"
        )
        
    user = db.query(models.User).filter(models.User.username == username).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found"
        )
    return user

class AuthRequest(BaseModel):
    username: str
    password: str

class RegisterRequest(BaseModel):
    username: str
    password: str
    full_name: str
    age: str
    job_education: str = ""

@router.post("/register")
def register(req: RegisterRequest, db: Session = Depends(get_db)):
    # Clean username check
    username = req.username.strip()
    if not username:
        raise HTTPException(status_code=400, detail="Username cannot be empty")
    if len(username) < 3:
        raise HTTPException(status_code=400, detail="Username must be at least 3 characters")
    if len(req.password) < 4:
        raise HTTPException(status_code=400, detail="Password must be at least 4 characters")

    existing_user = db.query(models.User).filter(models.User.username == username).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="Username is already taken")

    # Create new user
    hashed = hash_password(req.password)
    user = models.User(username=username, password_hash=hashed)
    db.add(user)
    db.commit()
    db.refresh(user)

    # Initialize associated settings and profiles for the user
    full_name_clean = req.full_name.strip() if req.full_name else username
    age_clean = req.age.strip() if req.age else ""
    job_edu_clean = req.job_education.strip() if req.job_education else ""

    settings_obj = models.UserSettings(
        user_id=user.id,
        name=full_name_clean,
        age=age_clean,
        education=job_edu_clean,
        gemini_model="gemini-flash-latest"
    )
    db.add(settings_obj)
    
    profile_obj = models.UserProfile(
        user_id=user.id,
        name=full_name_clean,
        age=age_clean,
        education_level=job_edu_clean,
        primary_goals="یادگیری و توسعه فردی",
        background_experience="من تازه یادگیری را با بلو لرن شروع کرده‌ام."
    )
    db.add(profile_obj)
    db.commit()
    db.refresh(profile_obj)
    
    # Initialize cognitive profile
    cog_profile = models.CognitiveProfile(
        user_id=profile_obj.id,
        cognitive_data_json="{}",
        interests_json="[]",
        recommended_topics_json="[]",
        strength_areas_json="[]"
    )
    db.add(cog_profile)
    db.commit()

    token = create_jwt({"sub": user.username, "id": user.id})
    return {"token": token, "username": user.username, "id": user.id}

@router.post("/login")
def login(req: AuthRequest, db: Session = Depends(get_db)):
    username = req.username.strip()
    user = db.query(models.User).filter(models.User.username == username).first()
    if not user or not verify_password(req.password, user.password_hash):
        raise HTTPException(status_code=400, detail="Invalid username or password")

    token = create_jwt({"sub": user.username, "id": user.id})
    return {"token": token, "username": user.username, "id": user.id}

@router.get("/me")
def get_me(current_user: models.User = Depends(get_current_user)):
    return {"id": current_user.id, "username": current_user.username}
