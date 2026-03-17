from fastapi import APIRouter, HTTPException, Depends
from models.schemas import UserCreate, UserLogin, FamilyPinLogin, ChangePassword, ResetMemberPassword
from auth import (
    get_current_user, hash_password, verify_password, create_token,
    generate_pin, generate_user_pin, DEFAULT_FAMILY_SETTINGS,
    generate_reset_token, verify_reset_token, send_email
)
from database import db
from datetime import datetime, timezone
from collections import defaultdict
import time
import uuid

router = APIRouter(prefix="/api/auth", tags=["auth"])

# Simple in-memory rate limiter
_rate_limit = defaultdict(list)
RATE_LIMIT_WINDOW = 300  # 5 minutes
RATE_LIMIT_MAX = 10  # max attempts per window

def _check_rate_limit(key: str):
    now = time.time()
    _rate_limit[key] = [t for t in _rate_limit[key] if now - t < RATE_LIMIT_WINDOW]
    if len(_rate_limit[key]) >= RATE_LIMIT_MAX:
        raise HTTPException(status_code=429, detail="Too many attempts. Please try again later.")
    _rate_limit[key].append(now)


@router.post("/register")
async def register(user: UserCreate):
    _check_rate_limit(f"register:{user.email}")
    existing = await db.users.find_one({"email": user.email}, {"_id": 0})
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")

    user_pin = generate_user_pin()
    user_id = str(uuid.uuid4())
    family_id = None
    family_pin = None
    role = "member"

    if user.family_name:
        family_pin = generate_pin()
        family_id = str(uuid.uuid4())
        family_doc = {
            "id": family_id,
            "name": user.family_name,
            "pin": family_pin,
            "settings": DEFAULT_FAMILY_SETTINGS,
            "created_by": user_id,
            "created_at": datetime.now(timezone.utc).isoformat()
        }
        await db.families.insert_one(family_doc)
        role = "owner"

    user_doc = {
        "id": user_id,
        "name": user.name,
        "email": user.email,
        "password": hash_password(user.password),
        "role": role,
        "user_pin": user_pin,
        "avatar_seed": user.avatar_seed or str(uuid.uuid4()),
        "family_id": family_id,
        "points": 0,
        "google_tokens": None,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "last_login": datetime.now(timezone.utc).isoformat()
    }
    await db.users.insert_one(user_doc)

    token = create_token(user_id, family_id or "", role)
    response_doc = {k: v for k, v in user_doc.items() if k not in ["password", "_id"]}
    return {
        "user": response_doc,
        "token": token,
        "message": "Registration successful",
        "user_pin": user_pin,
        "family_pin": family_pin
    }


@router.post("/login")
async def login(credentials: UserLogin):
    _check_rate_limit(f"login:{credentials.email}")
    user = await db.users.find_one({"email": credentials.email}, {"_id": 0})
    if not user or not verify_password(credentials.password, user["password"]):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    await db.users.update_one({"id": user["id"]}, {"$set": {"last_login": datetime.now(timezone.utc).isoformat()}})
    token = create_token(user["id"], user.get("family_id", ""), user.get("role", "member"))
    response_user = {k: v for k, v in user.items() if k != "password"}
    return {"token": token, "user": response_user}


@router.post("/pin-login")
async def pin_login(data: FamilyPinLogin):
    family = await db.families.find_one({"pin": data.pin}, {"_id": 0})
    if not family:
        raise HTTPException(status_code=401, detail="Invalid PIN")
    token = create_token("guest", family["id"], "child")
    return {"token": token, "family": family}


@router.post("/user-pin-login")
async def user_pin_login(data: dict):
    user = await db.users.find_one({"user_pin": data.get("pin")}, {"_id": 0})
    if not user:
        raise HTTPException(status_code=401, detail="Invalid PIN")
    await db.users.update_one({"id": user["id"]}, {"$set": {"last_login": datetime.now(timezone.utc).isoformat()}})
    token = create_token(user["id"], user.get("family_id", ""), user.get("role", "member"))
    response_user = {k: v for k, v in user.items() if k != "password"}
    return {"token": token, "user": response_user}


@router.get("/me")
async def get_me(user: dict = Depends(get_current_user)):
    user_data = await db.users.find_one({"id": user["user_id"]}, {"_id": 0, "password": 0})
    if not user_data:
        return {"user_id": user["user_id"], "family_id": user["family_id"], "role": user.get("role", "member")}
    return user_data


@router.put("/hidden-modules")
async def update_hidden_modules(data: dict, user: dict = Depends(get_current_user)):
    hidden = data.get("hidden_modules", [])
    if not isinstance(hidden, list):
        raise HTTPException(status_code=400, detail="hidden_modules must be a list")
    await db.users.update_one(
        {"id": user["user_id"]},
        {"$set": {"hidden_modules": hidden}}
    )
    return {"hidden_modules": hidden}


@router.post("/change-password")
async def change_password(data: ChangePassword, user: dict = Depends(get_current_user)):
    if len(data.new_password) < 6:
        raise HTTPException(status_code=400, detail="New password must be at least 6 characters")
    user_doc = await db.users.find_one({"id": user["user_id"]}, {"_id": 0})
    if not user_doc:
        raise HTTPException(status_code=404, detail="User not found")
    if not verify_password(data.current_password, user_doc["password"]):
        raise HTTPException(status_code=400, detail="Current password is incorrect")
    await db.users.update_one(
        {"id": user["user_id"]},
        {"$set": {"password": hash_password(data.new_password)}}
    )
    return {"message": "Password changed successfully"}


@router.post("/reset-password")
async def reset_member_password(data: ResetMemberPassword, user: dict = Depends(get_current_user)):
    from auth import get_user_role
    role = await get_user_role(user)
    if role not in ["owner", "parent"]:
        raise HTTPException(status_code=403, detail="Only owners and parents can reset passwords")
    target = await db.users.find_one({"id": data.user_id, "family_id": user["family_id"]}, {"_id": 0})
    if not target:
        raise HTTPException(status_code=404, detail="Member not found")
    temp_password = ''.join(__import__('secrets').choice(__import__('string').ascii_letters + __import__('string').digits) for _ in range(12))
    await db.users.update_one(
        {"id": data.user_id},
        {"$set": {"password": hash_password(temp_password)}}
    )
    return {"message": f"Password reset for {target['name']}", "temp_password": temp_password}


@router.post("/forgot-password")
async def forgot_password(data: dict):
    email = data.get("email", "").strip().lower()
    if not email:
        raise HTTPException(status_code=400, detail="Email is required")
    _check_rate_limit(f"forgot:{email}")
    # Always return success to prevent email enumeration
    user = await db.users.find_one({"email": email}, {"_id": 0})
    if user:
        import os
        server_url = os.environ.get("SERVER_URL", "").rstrip("/")
        if not server_url:
            raise HTTPException(status_code=400, detail="Server URL not configured. Ask the hub owner to set it in Server settings.")
        token = generate_reset_token(email)
        reset_link = f"{server_url}/reset-password?token={token}"
        html = f"""
        <div style="font-family: sans-serif; max-width: 480px; margin: 0 auto; padding: 24px;">
            <h2 style="color: #2D3748;">Family Hub - Password Reset</h2>
            <p>Hi {user.get('name', 'there')},</p>
            <p>We received a request to reset your password. Click the button below to choose a new one:</p>
            <div style="text-align: center; margin: 32px 0;">
                <a href="{reset_link}" style="background-color: #E07A5F; color: white; padding: 12px 32px; border-radius: 8px; text-decoration: none; font-weight: bold;">
                    Reset Password
                </a>
            </div>
            <p style="color: #718096; font-size: 14px;">This link expires in 1 hour. If you didn't request this, you can safely ignore this email.</p>
        </div>
        """
        await send_email(email, "Family Hub - Password Reset", html)
    return {"message": "If an account with that email exists, a reset link has been sent."}


@router.post("/reset-password-token")
async def reset_password_with_token(data: dict):
    token = data.get("token", "")
    new_password = data.get("new_password", "")
    if not token or not new_password:
        raise HTTPException(status_code=400, detail="Token and new password are required")
    if len(new_password) < 6:
        raise HTTPException(status_code=400, detail="Password must be at least 6 characters")
    email = verify_reset_token(token)
    if not email:
        raise HTTPException(status_code=400, detail="Invalid or expired reset link. Please request a new one.")
    user = await db.users.find_one({"email": email}, {"_id": 0})
    if not user:
        raise HTTPException(status_code=400, detail="Account not found")
    await db.users.update_one(
        {"email": email},
        {"$set": {"password": hash_password(new_password)}}
    )
    return {"message": "Password has been reset successfully. You can now sign in."}
