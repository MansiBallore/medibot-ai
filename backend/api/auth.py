"""
MediBot AI — Authentication API
Register, login, profile management
"""

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, EmailStr, Field
from typing import Optional
import uuid

from core.auth import hash_password, verify_password, create_access_token, require_auth, get_current_user
from core.database import db_insert, db_find_one, db_update_one

router = APIRouter()


class RegisterRequest(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    email: EmailStr
    password: str = Field(..., min_length=6)
    full_name: Optional[str] = None
    age: Optional[int] = Field(None, ge=1, le=120)
    gender: Optional[str] = None


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class ProfileUpdateRequest(BaseModel):
    full_name: Optional[str] = None
    age: Optional[int] = Field(None, ge=1, le=120)
    gender: Optional[str] = None
    known_conditions: Optional[list] = None
    allergies: Optional[list] = None


@router.post("/register", status_code=201)
async def register(body: RegisterRequest):
    # Check duplicate
    existing = await db_find_one("users", {"email": body.email})
    if existing:
        raise HTTPException(status_code=409, detail="Email already registered")

    user = {
        "_id": str(uuid.uuid4()),
        "username": body.username,
        "email": body.email,
        "password_hash": hash_password(body.password),
        "full_name": body.full_name,
        "age": body.age,
        "gender": body.gender,
        "role": "user",
        "known_conditions": [],
        "allergies": [],
    }
    user_id = await db_insert("users", user)
    token = create_access_token({"user_id": user_id, "username": body.username, "role": "user"})

    return {
        "message": "Registration successful",
        "token": token,
        "user": {"user_id": user_id, "username": body.username, "email": body.email},
    }


@router.post("/login")
async def login(body: LoginRequest):
    user = await db_find_one("users", {"email": body.email})
    if not user or not verify_password(body.password, user["password_hash"]):
        raise HTTPException(status_code=401, detail="Invalid email or password")

    token = create_access_token({
        "user_id": user["_id"],
        "username": user["username"],
        "role": user.get("role", "user"),
    })
    return {
        "token": token,
        "user": {
            "user_id": user["_id"],
            "username": user["username"],
            "email": user["email"],
            "full_name": user.get("full_name"),
        },
    }


@router.get("/me")
async def get_profile(user: dict = Depends(require_auth)):
    db_user = await db_find_one("users", {"_id": user["user_id"]})
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")
    db_user.pop("password_hash", None)
    return db_user


@router.put("/me")
async def update_profile(body: ProfileUpdateRequest, user: dict = Depends(require_auth)):
    updates = {k: v for k, v in body.dict().items() if v is not None}
    await db_update_one("users", {"_id": user["user_id"]}, updates)
    return {"message": "Profile updated successfully"}


@router.post("/guest-token")
async def guest_token():
    """Issue a temporary guest token for anonymous use."""
    token = create_access_token({"user_id": "guest", "username": "Guest", "role": "guest"})
    return {"token": token, "message": "Guest session created"}
