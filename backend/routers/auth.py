from fastapi import APIRouter, HTTPException, Depends
from models.schemas import UserCreate, UserLogin, FamilyPinLogin, ChangePassword, ResetMemberPassword
from auth import (
    get_current_user, hash_password, verify_password, create_token,
    generate_pin, generate_user_pin, DEFAULT_FAMILY_SETTINGS
)
from database import db
from datetime import datetime, timezone
import uuid

router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.post("/register")
async def register(user: UserCreate):
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
