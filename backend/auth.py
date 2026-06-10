from fastapi import APIRouter, Depends, HTTPException, status, Header
from sqlalchemy.orm import Session
from pydantic import BaseModel, EmailStr
from datetime import datetime, timedelta
import jwt
import os
import hashlib

from models import User, get_db

SECRET_KEY = os.getenv("SECRET_KEY", "incident-router-secret-key-change-in-production")
ALGORITHM = "HS256"

router = APIRouter(prefix="/auth", tags=["auth"])

class UserRegister(BaseModel):
    email: EmailStr
    password: str
    full_name: str

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user_id: int
    email: str

def hash_password(password: str) -> str:
    """Simple SHA-256 hashing for hackathon MVP."""
    return hashlib.sha256(password.encode()).hexdigest()

def create_access_token(data: dict):
    """Create JWT token and ensure 'sub' is a string."""
    to_encode = data.copy()
    
    # FIX: JWT requires 'sub' (subject) to be a string!
    if "sub" in to_encode:
        to_encode["sub"] = str(to_encode["sub"])
        
    expire = datetime.utcnow() + timedelta(days=30)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def get_current_user(authorization: str = Header(None), db: Session = Depends(get_db)):
    """Verify JWT token from Authorization header"""
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Invalid or missing Authorization header")
    
    token = authorization.split(" ")[1]
    
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id_str = payload.get("sub")
        if user_id_str is None:
            raise HTTPException(status_code=401, detail="Invalid token: missing subject")
        
        # Parse back to int for database lookup
        user_id = int(user_id_str)
    except jwt.PyJWTError as e:
        raise HTTPException(status_code=401, detail=f"Invalid token format: {str(e)}")
    except ValueError:
        raise HTTPException(status_code=401, detail="Invalid token: subject is not a valid ID")

    user = db.query(User).filter(User.id == user_id).first()
    if user is None:
        raise HTTPException(status_code=401, detail="User not found")
    
    return user

@router.post("/register", response_model=Token)
def register(user_data: UserRegister, db: Session = Depends(get_db)):
    # Check if user exists
    existing_user = db.query(User).filter(User.email == user_data.email).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered")
        
    # Create user
    new_user = User(
        email=user_data.email,
        password=hash_password(user_data.password),
        full_name=user_data.full_name
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    
    # Generate token
    token = create_access_token(data={"sub": new_user.id})
    return {"access_token": token, "user_id": new_user.id, "email": new_user.email}

@router.post("/login", response_model=Token)
def login(user_data: UserLogin, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == user_data.email).first()
    if not user or user.password != hash_password(user_data.password):
        raise HTTPException(status_code=401, detail="Invalid email or password")
        
    token = create_access_token(data={"sub": user.id})
    return {"access_token": token, "user_id": user.id, "email": user.email}