from fastapi import FastAPI, APIRouter, HTTPException, Depends, UploadFile, File, Form, Query
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, RedirectResponse
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from pathlib import Path
from pydantic import BaseModel, Field, ConfigDict
from typing import List, Optional, Dict, Any
import uuid
import secrets
import string
from datetime import datetime, timezone
from jose import jwt
import bcrypt
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request as GoogleRequest
from googleapiclient.discovery import build
import requests

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

FRONTEND_BUILD_DIR = ROOT_DIR.parent / 'frontend' / 'build'

mongo_url = os.environ.get('MONGO_URL', 'mongodb://localhost:27017')
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ.get('DB_NAME', 'family_hub')]

JWT_SECRET = os.environ.get('JWT_SECRET', 'family-hub-secret-key-2024')
JWT_ALGORITHM = "HS256"

# Google Calendar Config
GOOGLE_CLIENT_ID = os.environ.get('GOOGLE_CLIENT_ID', '')
GOOGLE_CLIENT_SECRET = os.environ.get('GOOGLE_CLIENT_SECRET', '')
GOOGLE_REDIRECT_URI = os.environ.get('GOOGLE_REDIRECT_URI', '')

# SMTP Config
SMTP_HOST = os.environ.get('SMTP_HOST', '')
SMTP_PORT = int(os.environ.get('SMTP_PORT', '587'))
SMTP_USER = os.environ.get('SMTP_USER', '')
SMTP_PASSWORD = os.environ.get('SMTP_PASSWORD', '')
SMTP_FROM = os.environ.get('SMTP_FROM', '')

app = FastAPI()
api_router = APIRouter(prefix="/api")
security = HTTPBearer(auto_error=False)

# ============== ROLE DEFINITIONS ==============
ROLES = {
    "owner": {"level": 4, "can_manage_family": True, "can_manage_users": True, "can_manage_settings": True},
    "parent": {"level": 3, "can_manage_family": False, "can_manage_users": True, "can_manage_settings": True},
    "member": {"level": 2, "can_manage_family": False, "can_manage_users": False, "can_manage_settings": False},
    "child": {"level": 1, "can_manage_family": False, "can_manage_users": False, "can_manage_settings": False},
}

DEFAULT_FAMILY_SETTINGS = {
    "modules": {
        "calendar": {"enabled": True, "visible_to": ["owner", "parent", "member", "child"]},
        "shopping": {"enabled": True, "visible_to": ["owner", "parent", "member", "child"]},
        "tasks": {"enabled": True, "visible_to": ["owner", "parent", "member", "child"]},
        "notes": {"enabled": True, "visible_to": ["owner", "parent", "member", "child"]},
        "budget": {"enabled": True, "visible_to": ["owner", "parent", "member"]},
        "meals": {"enabled": True, "visible_to": ["owner", "parent", "member", "child"]},
        "recipes": {"enabled": True, "visible_to": ["owner", "parent", "member", "child"]},
        "grocery": {"enabled": True, "visible_to": ["owner", "parent", "member", "child"]},
        "contacts": {"enabled": True, "visible_to": ["owner", "parent", "member"]},
        "pantry": {"enabled": True, "visible_to": ["owner", "parent", "member", "child"]},
        "suggestions": {"enabled": True, "visible_to": ["owner", "parent", "member", "child"]},
        "chores": {"enabled": True, "visible_to": ["owner", "parent", "member", "child"]},
    },
    "permissions": {
        "owner": {"can_add": True, "can_edit": True, "can_delete": True},
        "parent": {"can_add": True, "can_edit": True, "can_delete": True},
        "member": {"can_add": True, "can_edit": True, "can_delete": False},
        "child": {"can_add": False, "can_edit": False, "can_delete": False},
    },
    "theme": {
        "primary_color": "#E07A5F",
        "accent_color": "#81B29A",
        "background_color": "#FDF8F3",
    },
    "chore_rewards": {
        "enabled": True,
        "point_values": {"easy": 5, "medium": 10, "hard": 20},
    }
}

# ============== MODELS ==============

class UserCreate(BaseModel):
    name: str
    email: str
    password: str
    role: str = "member"
    avatar_seed: Optional[str] = None

class UserLogin(BaseModel):
    email: str
    password: str

class UserInvite(BaseModel):
    email: str
    name: str
    role: str = "member"

class UserRoleUpdate(BaseModel):
    role: str

class FamilyCreate(BaseModel):
    name: str

class FamilyUpdate(BaseModel):
    name: Optional[str] = None

class FamilyPinLogin(BaseModel):
    pin: str

class CalendarEvent(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    title: str
    description: Optional[str] = ""
    date: str
    time: Optional[str] = ""
    color: Optional[str] = "#E07A5F"
    created_by: Optional[str] = None
    google_event_id: Optional[str] = None

class ShoppingItem(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    quantity: Optional[str] = "1"
    category: Optional[str] = "General"
    checked: bool = False
    added_by: Optional[str] = None

class Task(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    title: str
    description: Optional[str] = ""
    assigned_to: Optional[str] = None
    assigned_to_name: Optional[str] = None
    due_date: Optional[str] = None
    priority: str = "medium"
    completed: bool = False
    created_by: Optional[str] = None

class Chore(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    title: str
    description: Optional[str] = ""
    assigned_to: Optional[str] = None
    assigned_to_name: Optional[str] = None
    due_date: Optional[str] = None
    difficulty: str = "medium"
    points: int = 10
    completed: bool = False
    completed_at: Optional[str] = None
    recurring: Optional[str] = None
    created_by: Optional[str] = None

class RewardClaim(BaseModel):
    reward_id: str
    user_id: str

class Reward(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    description: Optional[str] = ""
    points_required: int
    available: bool = True
    created_by: Optional[str] = None

class Note(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    title: str
    content: str
    color: Optional[str] = "#F2CC8F"
    created_by: Optional[str] = None
    updated_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

class BudgetEntry(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    description: str
    amount: float
    category: str
    type: str
    date: str
    created_by: Optional[str] = None

class MealPlan(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    date: str
    meal_type: str
    recipe_id: Optional[str] = None
    recipe_name: str
    notes: Optional[str] = ""

class Recipe(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    description: Optional[str] = ""
    ingredients: List[str]
    instructions: List[str]
    prep_time: Optional[str] = ""
    cook_time: Optional[str] = ""
    servings: Optional[int] = 4
    category: Optional[str] = "Main Course"
    image_url: Optional[str] = ""
    created_by: Optional[str] = None

class GroceryItem(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    quantity: Optional[str] = "1"
    checked: bool = False

class Contact(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    relationship: Optional[str] = ""
    phone: Optional[str] = ""
    email: Optional[str] = ""
    address: Optional[str] = ""
    notes: Optional[str] = ""
    avatar_seed: str = Field(default_factory=lambda: str(uuid.uuid4()))

class PantryItem(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    barcode: Optional[str] = ""
    quantity: int = 1
    unit: Optional[str] = "pcs"
    category: Optional[str] = "Other"
    expiry_date: Optional[str] = None
    added_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

class FamilySettings(BaseModel):
    modules: Optional[Dict[str, Any]] = None
    permissions: Optional[Dict[str, Any]] = None
    theme: Optional[Dict[str, Any]] = None
    chore_rewards: Optional[Dict[str, Any]] = None

class ServerSettings(BaseModel):
    smtp_host: Optional[str] = None
    smtp_port: Optional[int] = None
    smtp_user: Optional[str] = None
    smtp_password: Optional[str] = None
    smtp_from: Optional[str] = None
    google_client_id: Optional[str] = None
    google_client_secret: Optional[str] = None

# ============== HELPERS ==============

def generate_pin(length: int = 6) -> str:
    return ''.join(secrets.choice(string.digits) for _ in range(length))

def generate_user_pin(length: int = 4) -> str:
    return ''.join(secrets.choice(string.digits) for _ in range(length))

def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()

def verify_password(password: str, hashed: str) -> bool:
    return bcrypt.checkpw(password.encode(), hashed.encode())

def create_token(user_id: str, family_id: str, role: str = "member") -> str:
    return jwt.encode({"user_id": user_id, "family_id": family_id, "role": role}, JWT_SECRET, algorithm=JWT_ALGORITHM)

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    if not credentials:
        raise HTTPException(status_code=401, detail="Not authenticated")
    try:
        payload = jwt.decode(credentials.credentials, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        return payload
    except:
        raise HTTPException(status_code=401, detail="Invalid token")

def check_permission(user_role: str, required_permission: str) -> bool:
    role_info = ROLES.get(user_role, ROLES["child"])
    return role_info.get(required_permission, False)

async def get_user_role(user: dict) -> str:
    """Get user role - handles guest users from family PIN login"""
    user_data = await db.users.find_one({"id": user["user_id"]}, {"_id": 0})
    if not user_data:
        # Guest user from family PIN login - use role from token
        return user.get("role", "child")
    return user_data.get("role", "member")

async def send_email(to_email: str, subject: str, html_content: str):
    if not all([SMTP_HOST, SMTP_USER, SMTP_PASSWORD]):
        logging.warning("SMTP not configured, skipping email")
        return False
    try:
        msg = MIMEMultipart('alternative')
        msg['Subject'] = subject
        msg['From'] = SMTP_FROM or SMTP_USER
        msg['To'] = to_email
        msg.attach(MIMEText(html_content, 'html'))
        
        with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
            server.starttls()
            server.login(SMTP_USER, SMTP_PASSWORD)
            server.send_message(msg)
        return True
    except Exception as e:
        logging.error(f"Failed to send email: {e}")
        return False

# ============== AUTH ROUTES ==============

@api_router.post("/auth/register")
async def register(user: UserCreate):
    existing = await db.users.find_one({"email": user.email}, {"_id": 0})
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    user_pin = generate_user_pin()
    user_doc = {
        "id": str(uuid.uuid4()),
        "name": user.name,
        "email": user.email,
        "password": hash_password(user.password),
        "role": user.role,
        "user_pin": user_pin,
        "avatar_seed": user.avatar_seed or str(uuid.uuid4()),
        "family_id": None,
        "points": 0,
        "google_tokens": None,
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    await db.users.insert_one(user_doc)
    response_doc = {k: v for k, v in user_doc.items() if k not in ["password", "_id"]}
    return {"user": response_doc, "message": "Registration successful", "user_pin": user_pin}

@api_router.post("/auth/login")
async def login(credentials: UserLogin):
    user = await db.users.find_one({"email": credentials.email}, {"_id": 0})
    if not user or not verify_password(credentials.password, user["password"]):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    token = create_token(user["id"], user.get("family_id", ""), user.get("role", "member"))
    response_user = {k: v for k, v in user.items() if k != "password"}
    return {"token": token, "user": response_user}

@api_router.post("/auth/pin-login")
async def pin_login(data: FamilyPinLogin):
    family = await db.families.find_one({"pin": data.pin}, {"_id": 0})
    if not family:
        raise HTTPException(status_code=401, detail="Invalid PIN")
    
    token = create_token("guest", family["id"], "child")
    return {"token": token, "family": family}

@api_router.post("/auth/user-pin-login")
async def user_pin_login(data: dict):
    user = await db.users.find_one({"user_pin": data.get("pin")}, {"_id": 0})
    if not user:
        raise HTTPException(status_code=401, detail="Invalid PIN")
    
    token = create_token(user["id"], user.get("family_id", ""), user.get("role", "member"))
    response_user = {k: v for k, v in user.items() if k != "password"}
    return {"token": token, "user": response_user}

@api_router.get("/auth/me")
async def get_me(user: dict = Depends(get_current_user)):
    user_data = await db.users.find_one({"id": user["user_id"]}, {"_id": 0, "password": 0})
    if not user_data:
        return {"user_id": user["user_id"], "family_id": user["family_id"], "role": user.get("role", "member")}
    return user_data

# ============== FAMILY ROUTES ==============

@api_router.post("/family/create")
async def create_family(family: FamilyCreate, user: dict = Depends(get_current_user)):
    family_pin = generate_pin()
    family_doc = {
        "id": str(uuid.uuid4()),
        "name": family.name,
        "pin": family_pin,
        "settings": DEFAULT_FAMILY_SETTINGS,
        "created_by": user["user_id"],
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    await db.families.insert_one(family_doc)
    await db.users.update_one(
        {"id": user["user_id"]}, 
        {"$set": {"family_id": family_doc["id"], "role": "owner"}}
    )
    response_doc = {k: v for k, v in family_doc.items() if k != "_id"}
    return response_doc

@api_router.get("/family")
async def get_family(user: dict = Depends(get_current_user)):
    if not user.get("family_id"):
        return None
    family = await db.families.find_one({"id": user["family_id"]}, {"_id": 0})
    return family

@api_router.put("/family")
async def update_family(update: FamilyUpdate, user: dict = Depends(get_current_user)):
    user_role = await get_user_role(user)
    if not check_permission(user_role, "can_manage_family"):
        if user_role not in ["owner", "parent"]:
            raise HTTPException(status_code=403, detail="Not authorized to update family")
    
    update_data = {k: v for k, v in update.model_dump().items() if v is not None}
    if update_data:
        await db.families.update_one({"id": user["family_id"]}, {"$set": update_data})
    
    family = await db.families.find_one({"id": user["family_id"]}, {"_id": 0})
    return family

@api_router.post("/family/regenerate-pin")
async def regenerate_family_pin(user: dict = Depends(get_current_user)):
    user_role = await get_user_role(user)
    if user_role not in ["owner", "parent"]:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    new_pin = generate_pin()
    await db.families.update_one({"id": user["family_id"]}, {"$set": {"pin": new_pin}})
    return {"pin": new_pin}

@api_router.get("/family/members")
async def get_family_members(user: dict = Depends(get_current_user)):
    if not user.get("family_id"):
        return []
    members = await db.users.find({"family_id": user["family_id"]}, {"_id": 0, "password": 0}).to_list(100)
    return members

@api_router.post("/family/invite")
async def invite_member(invite: UserInvite, user: dict = Depends(get_current_user)):
    user_role = await get_user_role(user)
    if user_role not in ["owner", "parent"]:
        raise HTTPException(status_code=403, detail="Not authorized to invite members")
    
    existing = await db.users.find_one({"email": invite.email}, {"_id": 0})
    if existing:
        raise HTTPException(status_code=400, detail="User already exists")
    
    family = await db.families.find_one({"id": user["family_id"]}, {"_id": 0})
    temp_password = secrets.token_urlsafe(12)
    user_pin = generate_user_pin()
    
    new_user = {
        "id": str(uuid.uuid4()),
        "name": invite.name,
        "email": invite.email,
        "password": hash_password(temp_password),
        "role": invite.role,
        "user_pin": user_pin,
        "avatar_seed": str(uuid.uuid4()),
        "family_id": user["family_id"],
        "points": 0,
        "invited_by": user["user_id"],
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    await db.users.insert_one(new_user)
    
    email_html = f"""
    <h2>Welcome to {family['name']} on Family Hub!</h2>
    <p>You've been invited by {user_data['name']} to join the family.</p>
    <p><strong>Your login credentials:</strong></p>
    <ul>
        <li>Email: {invite.email}</li>
        <li>Temporary Password: {temp_password}</li>
        <li>Your PIN: {user_pin}</li>
    </ul>
    <p>Please change your password after logging in.</p>
    """
    await send_email(invite.email, f"You're invited to {family['name']} - Family Hub", email_html)
    
    return {"message": "Invitation sent", "user_id": new_user["id"], "user_pin": user_pin, "temp_password": temp_password}

class QuickAddMember(BaseModel):
    name: str
    role: str = "member"

@api_router.post("/family/add-member")
async def quick_add_member(member: QuickAddMember, user: dict = Depends(get_current_user)):
    """Add a family member without email - just creates a PIN for them to login"""
    user_role = await get_user_role(user)
    if user_role not in ["owner", "parent"]:
        raise HTTPException(status_code=403, detail="Not authorized to add members")
    
    user_pin = generate_user_pin()
    
    new_user = {
        "id": str(uuid.uuid4()),
        "name": member.name,
        "email": None,
        "password": None,
        "role": member.role,
        "user_pin": user_pin,
        "avatar_seed": str(uuid.uuid4()),
        "family_id": user["family_id"],
        "points": 0,
        "added_by": user["user_id"],
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    await db.users.insert_one(new_user)
    
    return {
        "message": f"{member.name} added to family!", 
        "user_id": new_user["id"], 
        "user_pin": user_pin,
        "name": member.name,
        "role": member.role
    }

@api_router.put("/family/members/{member_id}/role")
async def update_member_role(member_id: str, role_update: UserRoleUpdate, user: dict = Depends(get_current_user)):
    user_role = await get_user_role(user)
    if user_role not in ["owner", "parent"]:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    if role_update.role not in ROLES:
        raise HTTPException(status_code=400, detail="Invalid role")
    
    target_user = await db.users.find_one({"id": member_id, "family_id": user["family_id"]}, {"_id": 0})
    if not target_user:
        raise HTTPException(status_code=404, detail="Member not found")
    
    if target_user.get("role") == "owner" and user_role != "owner":
        raise HTTPException(status_code=403, detail="Cannot change owner role")
    
    await db.users.update_one({"id": member_id}, {"$set": {"role": role_update.role}})
    return {"message": "Role updated"}

@api_router.delete("/family/members/{member_id}")
async def remove_member(member_id: str, user: dict = Depends(get_current_user)):
    user_role = await get_user_role(user)
    if user_role not in ["owner", "parent"]:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    target_user = await db.users.find_one({"id": member_id, "family_id": user["family_id"]}, {"_id": 0})
    if not target_user:
        raise HTTPException(status_code=404, detail="Member not found")
    
    if target_user.get("role") == "owner":
        raise HTTPException(status_code=403, detail="Cannot remove owner")
    
    await db.users.update_one({"id": member_id}, {"$set": {"family_id": None}})
    return {"message": "Member removed"}

@api_router.post("/family/members/{member_id}/regenerate-pin")
async def regenerate_user_pin(member_id: str, user: dict = Depends(get_current_user)):
    user_role = await get_user_role(user)
    if user_role not in ["owner", "parent"] and user["user_id"] != member_id:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    new_pin = generate_user_pin()
    await db.users.update_one({"id": member_id}, {"$set": {"user_pin": new_pin}})
    return {"pin": new_pin}

# ============== SETTINGS ROUTES ==============

@api_router.get("/settings")
async def get_settings(user: dict = Depends(get_current_user)):
    family = await db.families.find_one({"id": user["family_id"]}, {"_id": 0})
    if not family:
        return DEFAULT_FAMILY_SETTINGS
    return family.get("settings", DEFAULT_FAMILY_SETTINGS)

@api_router.put("/settings")
async def update_settings(settings: FamilySettings, user: dict = Depends(get_current_user)):
    if not user.get("family_id"):
        raise HTTPException(status_code=400, detail="No family associated with user")
    
    user_role = await get_user_role(user)
    if user_role not in ["owner", "parent"]:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    update_data = {}
    if settings.modules:
        update_data["settings.modules"] = settings.modules
    if settings.permissions:
        update_data["settings.permissions"] = settings.permissions
    if settings.theme:
        update_data["settings.theme"] = settings.theme
    if settings.chore_rewards:
        update_data["settings.chore_rewards"] = settings.chore_rewards
    
    if update_data:
        await db.families.update_one({"id": user["family_id"]}, {"$set": update_data})
    
    family = await db.families.find_one({"id": user["family_id"]}, {"_id": 0})
    if not family:
        raise HTTPException(status_code=404, detail="Family not found")
    return family.get("settings", DEFAULT_FAMILY_SETTINGS)

@api_router.get("/settings/server")
async def get_server_settings(user: dict = Depends(get_current_user)):
    user_role = await get_user_role(user)
    if user_role != "owner":
        raise HTTPException(status_code=403, detail="Only owner can view server settings")
    
    return {
        "smtp_configured": bool(SMTP_HOST),
        "google_configured": bool(GOOGLE_CLIENT_ID),
        "smtp_host": SMTP_HOST,
        "smtp_port": SMTP_PORT,
        "smtp_user": SMTP_USER,
        "smtp_from": SMTP_FROM,
    }

# ============== CALENDAR ROUTES ==============

@api_router.get("/calendar", response_model=List[CalendarEvent])
async def get_events(user: dict = Depends(get_current_user)):
    events = await db.calendar_events.find({"family_id": user["family_id"]}, {"_id": 0}).to_list(1000)
    for e in events:
        e.pop("family_id", None)
    return events

@api_router.post("/calendar", response_model=CalendarEvent)
async def create_event(event: CalendarEvent, user: dict = Depends(get_current_user)):
    event_doc = event.model_dump()
    event_doc["family_id"] = user["family_id"]
    event_doc["created_by"] = user["user_id"]
    await db.calendar_events.insert_one(event_doc)
    del event_doc["_id"]
    del event_doc["family_id"]
    return event_doc

@api_router.put("/calendar/{event_id}")
async def update_event(event_id: str, event: CalendarEvent, user: dict = Depends(get_current_user)):
    event_doc = event.model_dump()
    await db.calendar_events.update_one({"id": event_id, "family_id": user["family_id"]}, {"$set": event_doc})
    return event_doc

@api_router.delete("/calendar/{event_id}")
async def delete_event(event_id: str, user: dict = Depends(get_current_user)):
    await db.calendar_events.delete_one({"id": event_id, "family_id": user["family_id"]})
    return {"message": "Event deleted"}

# ============== GOOGLE CALENDAR SYNC ==============

@api_router.get("/calendar/google/auth")
async def google_calendar_auth(user: dict = Depends(get_current_user)):
    if not GOOGLE_CLIENT_ID or not GOOGLE_CLIENT_SECRET:
        raise HTTPException(status_code=400, detail="Google Calendar not configured")
    
    redirect_uri = GOOGLE_REDIRECT_URI or f"{os.environ.get('REACT_APP_BACKEND_URL', '')}/api/calendar/google/callback"
    
    auth_url = (
        f"https://accounts.google.com/o/oauth2/auth?"
        f"client_id={GOOGLE_CLIENT_ID}&"
        f"redirect_uri={redirect_uri}&"
        f"response_type=code&"
        f"scope=https://www.googleapis.com/auth/calendar https://www.googleapis.com/auth/userinfo.email&"
        f"access_type=offline&"
        f"prompt=consent&"
        f"state={user['user_id']}"
    )
    return {"authorization_url": auth_url}

@api_router.get("/calendar/google/callback")
async def google_calendar_callback(code: str, state: str):
    redirect_uri = GOOGLE_REDIRECT_URI or f"{os.environ.get('REACT_APP_BACKEND_URL', '')}/api/calendar/google/callback"
    
    token_resp = requests.post('https://oauth2.googleapis.com/token', data={
        'code': code,
        'client_id': GOOGLE_CLIENT_ID,
        'client_secret': GOOGLE_CLIENT_SECRET,
        'redirect_uri': redirect_uri,
        'grant_type': 'authorization_code'
    }).json()
    
    if 'error' in token_resp:
        return RedirectResponse(f"/settings?error=google_auth_failed")
    
    await db.users.update_one(
        {"id": state},
        {"$set": {"google_tokens": token_resp}}
    )
    
    return RedirectResponse(f"/settings?google_connected=true")

@api_router.post("/calendar/google/sync")
async def sync_google_calendar(user: dict = Depends(get_current_user)):
    user_data = await db.users.find_one({"id": user["user_id"]}, {"_id": 0})
    if not user_data.get("google_tokens"):
        raise HTTPException(status_code=400, detail="Google Calendar not connected")
    
    tokens = user_data["google_tokens"]
    creds = Credentials(
        token=tokens.get('access_token'),
        refresh_token=tokens.get('refresh_token'),
        token_uri='https://oauth2.googleapis.com/token',
        client_id=GOOGLE_CLIENT_ID,
        client_secret=GOOGLE_CLIENT_SECRET
    )
    
    if creds.expired and creds.refresh_token:
        creds.refresh(GoogleRequest())
        await db.users.update_one(
            {"id": user["user_id"]},
            {"$set": {"google_tokens.access_token": creds.token}}
        )
    
    service = build('calendar', 'v3', credentials=creds)
    
    local_events = await db.calendar_events.find({"family_id": user["family_id"]}, {"_id": 0}).to_list(1000)
    
    synced = 0
    for event in local_events:
        if event.get("google_event_id"):
            continue
        
        try:
            start_datetime = f"{event['date']}T{event.get('time', '00:00')}:00"
            google_event = service.events().insert(
                calendarId='primary',
                body={
                    'summary': event['title'],
                    'description': event.get('description', ''),
                    'start': {'dateTime': start_datetime, 'timeZone': 'UTC'},
                    'end': {'dateTime': start_datetime, 'timeZone': 'UTC'},
                }
            ).execute()
            
            await db.calendar_events.update_one(
                {"id": event["id"]},
                {"$set": {"google_event_id": google_event['id']}}
            )
            synced += 1
        except Exception as e:
            logging.error(f"Failed to sync event: {e}")
    
    return {"synced": synced}

@api_router.delete("/calendar/google/disconnect")
async def disconnect_google_calendar(user: dict = Depends(get_current_user)):
    await db.users.update_one({"id": user["user_id"]}, {"$set": {"google_tokens": None}})
    return {"message": "Google Calendar disconnected"}

# ============== SHOPPING LIST ROUTES ==============

@api_router.get("/shopping", response_model=List[ShoppingItem])
async def get_shopping_items(user: dict = Depends(get_current_user)):
    items = await db.shopping_items.find({"family_id": user["family_id"]}, {"_id": 0}).to_list(1000)
    for i in items:
        i.pop("family_id", None)
    return items

@api_router.post("/shopping", response_model=ShoppingItem)
async def create_shopping_item(item: ShoppingItem, user: dict = Depends(get_current_user)):
    item_doc = item.model_dump()
    item_doc["family_id"] = user["family_id"]
    item_doc["added_by"] = user["user_id"]
    await db.shopping_items.insert_one(item_doc)
    del item_doc["_id"]
    del item_doc["family_id"]
    return item_doc

@api_router.put("/shopping/{item_id}")
async def update_shopping_item(item_id: str, item: ShoppingItem, user: dict = Depends(get_current_user)):
    item_doc = item.model_dump()
    await db.shopping_items.update_one({"id": item_id, "family_id": user["family_id"]}, {"$set": item_doc})
    return item_doc

@api_router.delete("/shopping/{item_id}")
async def delete_shopping_item(item_id: str, user: dict = Depends(get_current_user)):
    await db.shopping_items.delete_one({"id": item_id, "family_id": user["family_id"]})
    return {"message": "Item deleted"}

@api_router.delete("/shopping")
async def clear_shopping_list(user: dict = Depends(get_current_user)):
    await db.shopping_items.delete_many({"family_id": user["family_id"], "checked": True})
    return {"message": "Checked items cleared"}

# ============== TASKS ROUTES ==============

@api_router.get("/tasks", response_model=List[Task])
async def get_tasks(user: dict = Depends(get_current_user)):
    tasks = await db.tasks.find({"family_id": user["family_id"]}, {"_id": 0}).to_list(1000)
    for t in tasks:
        t.pop("family_id", None)
    return tasks

@api_router.post("/tasks", response_model=Task)
async def create_task(task: Task, user: dict = Depends(get_current_user)):
    task_doc = task.model_dump()
    task_doc["family_id"] = user["family_id"]
    task_doc["created_by"] = user["user_id"]
    
    if task.assigned_to:
        assigned_user = await db.users.find_one({"id": task.assigned_to}, {"_id": 0})
        if assigned_user:
            task_doc["assigned_to_name"] = assigned_user.get("name")
    
    await db.tasks.insert_one(task_doc)
    del task_doc["_id"]
    del task_doc["family_id"]
    return task_doc

@api_router.put("/tasks/{task_id}")
async def update_task(task_id: str, task: Task, user: dict = Depends(get_current_user)):
    task_doc = task.model_dump()
    
    if task.assigned_to:
        assigned_user = await db.users.find_one({"id": task.assigned_to}, {"_id": 0})
        if assigned_user:
            task_doc["assigned_to_name"] = assigned_user.get("name")
    
    await db.tasks.update_one({"id": task_id, "family_id": user["family_id"]}, {"$set": task_doc})
    return task_doc

@api_router.delete("/tasks/{task_id}")
async def delete_task(task_id: str, user: dict = Depends(get_current_user)):
    await db.tasks.delete_one({"id": task_id, "family_id": user["family_id"]})
    return {"message": "Task deleted"}

# ============== CHORES & REWARDS ROUTES ==============

@api_router.get("/chores")
async def get_chores(user: dict = Depends(get_current_user)):
    chores = await db.chores.find({"family_id": user["family_id"]}, {"_id": 0}).to_list(1000)
    for c in chores:
        c.pop("family_id", None)
    return chores

@api_router.post("/chores")
async def create_chore(chore: Chore, user: dict = Depends(get_current_user)):
    if not user.get("family_id"):
        raise HTTPException(status_code=400, detail="No family associated with user")
    
    chore_doc = chore.model_dump()
    chore_doc["family_id"] = user["family_id"]
    chore_doc["created_by"] = user["user_id"]
    
    family = await db.families.find_one({"id": user["family_id"]}, {"_id": 0})
    if not family:
        raise HTTPException(status_code=404, detail="Family not found")
    
    settings = family.get("settings", DEFAULT_FAMILY_SETTINGS)
    point_values = settings.get("chore_rewards", {}).get("point_values", {"easy": 5, "medium": 10, "hard": 20})
    chore_doc["points"] = point_values.get(chore.difficulty, 10)
    
    if chore.assigned_to:
        assigned_user = await db.users.find_one({"id": chore.assigned_to}, {"_id": 0})
        if assigned_user:
            chore_doc["assigned_to_name"] = assigned_user.get("name")
    
    await db.chores.insert_one(chore_doc)
    del chore_doc["_id"]
    del chore_doc["family_id"]
    return chore_doc

@api_router.put("/chores/{chore_id}")
async def update_chore(chore_id: str, chore: Chore, user: dict = Depends(get_current_user)):
    chore_doc = chore.model_dump()
    
    if chore.assigned_to:
        assigned_user = await db.users.find_one({"id": chore.assigned_to}, {"_id": 0})
        if assigned_user:
            chore_doc["assigned_to_name"] = assigned_user.get("name")
    
    await db.chores.update_one({"id": chore_id, "family_id": user["family_id"]}, {"$set": chore_doc})
    return chore_doc

@api_router.post("/chores/{chore_id}/complete")
async def complete_chore(chore_id: str, user: dict = Depends(get_current_user)):
    chore = await db.chores.find_one({"id": chore_id, "family_id": user["family_id"]}, {"_id": 0})
    if not chore:
        raise HTTPException(status_code=404, detail="Chore not found")
    
    if chore.get("completed"):
        raise HTTPException(status_code=400, detail="Chore already completed")
    
    completer_id = chore.get("assigned_to") or user["user_id"]
    
    await db.chores.update_one(
        {"id": chore_id},
        {"$set": {"completed": True, "completed_at": datetime.now(timezone.utc).isoformat()}}
    )
    
    await db.users.update_one(
        {"id": completer_id},
        {"$inc": {"points": chore.get("points", 10)}}
    )
    
    return {"message": "Chore completed", "points_earned": chore.get("points", 10)}

@api_router.delete("/chores/{chore_id}")
async def delete_chore(chore_id: str, user: dict = Depends(get_current_user)):
    await db.chores.delete_one({"id": chore_id, "family_id": user["family_id"]})
    return {"message": "Chore deleted"}

@api_router.get("/rewards")
async def get_rewards(user: dict = Depends(get_current_user)):
    rewards = await db.rewards.find({"family_id": user["family_id"]}, {"_id": 0}).to_list(100)
    for r in rewards:
        r.pop("family_id", None)
    return rewards

@api_router.post("/rewards")
async def create_reward(reward: Reward, user: dict = Depends(get_current_user)):
    user_role = await get_user_role(user)
    if user_role not in ["owner", "parent"]:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    reward_doc = reward.model_dump()
    reward_doc["family_id"] = user["family_id"]
    reward_doc["created_by"] = user["user_id"]
    await db.rewards.insert_one(reward_doc)
    del reward_doc["_id"]
    del reward_doc["family_id"]
    return reward_doc

@api_router.post("/rewards/claim")
async def claim_reward(claim: RewardClaim, user: dict = Depends(get_current_user)):
    reward = await db.rewards.find_one({"id": claim.reward_id, "family_id": user["family_id"]}, {"_id": 0})
    if not reward:
        raise HTTPException(status_code=404, detail="Reward not found")
    
    claimer = await db.users.find_one({"id": claim.user_id}, {"_id": 0})
    if not claimer or claimer.get("family_id") != user["family_id"]:
        raise HTTPException(status_code=404, detail="User not found")
    
    if claimer.get("points", 0) < reward["points_required"]:
        raise HTTPException(status_code=400, detail="Not enough points")
    
    await db.users.update_one(
        {"id": claim.user_id},
        {"$inc": {"points": -reward["points_required"]}}
    )
    
    claim_record = {
        "id": str(uuid.uuid4()),
        "reward_id": claim.reward_id,
        "reward_name": reward["name"],
        "user_id": claim.user_id,
        "points_spent": reward["points_required"],
        "claimed_at": datetime.now(timezone.utc).isoformat(),
        "family_id": user["family_id"]
    }
    await db.reward_claims.insert_one(claim_record)
    
    return {"message": "Reward claimed", "points_spent": reward["points_required"]}

@api_router.get("/leaderboard")
async def get_leaderboard(user: dict = Depends(get_current_user)):
    members = await db.users.find(
        {"family_id": user["family_id"]},
        {"_id": 0, "id": 1, "name": 1, "points": 1, "avatar_seed": 1}
    ).sort("points", -1).to_list(100)
    return members

@api_router.delete("/rewards/{reward_id}")
async def delete_reward(reward_id: str, user: dict = Depends(get_current_user)):
    user_role = await get_user_role(user)
    if user_role not in ["owner", "parent"]:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    await db.rewards.delete_one({"id": reward_id, "family_id": user["family_id"]})
    return {"message": "Reward deleted"}

# ============== NOTES ROUTES ==============

@api_router.get("/notes", response_model=List[Note])
async def get_notes(user: dict = Depends(get_current_user)):
    notes = await db.notes.find({"family_id": user["family_id"]}, {"_id": 0}).to_list(1000)
    for n in notes:
        n.pop("family_id", None)
    return notes

@api_router.post("/notes", response_model=Note)
async def create_note(note: Note, user: dict = Depends(get_current_user)):
    note_doc = note.model_dump()
    note_doc["family_id"] = user["family_id"]
    note_doc["created_by"] = user["user_id"]
    await db.notes.insert_one(note_doc)
    del note_doc["_id"]
    del note_doc["family_id"]
    return note_doc

@api_router.put("/notes/{note_id}")
async def update_note(note_id: str, note: Note, user: dict = Depends(get_current_user)):
    note_doc = note.model_dump()
    note_doc["updated_at"] = datetime.now(timezone.utc).isoformat()
    await db.notes.update_one({"id": note_id, "family_id": user["family_id"]}, {"$set": note_doc})
    return note_doc

@api_router.delete("/notes/{note_id}")
async def delete_note(note_id: str, user: dict = Depends(get_current_user)):
    await db.notes.delete_one({"id": note_id, "family_id": user["family_id"]})
    return {"message": "Note deleted"}

# ============== BUDGET ROUTES ==============

@api_router.get("/budget", response_model=List[BudgetEntry])
async def get_budget_entries(user: dict = Depends(get_current_user)):
    entries = await db.budget_entries.find({"family_id": user["family_id"]}, {"_id": 0}).to_list(1000)
    for e in entries:
        e.pop("family_id", None)
    return entries

@api_router.post("/budget", response_model=BudgetEntry)
async def create_budget_entry(entry: BudgetEntry, user: dict = Depends(get_current_user)):
    entry_doc = entry.model_dump()
    entry_doc["family_id"] = user["family_id"]
    entry_doc["created_by"] = user["user_id"]
    await db.budget_entries.insert_one(entry_doc)
    del entry_doc["_id"]
    del entry_doc["family_id"]
    return entry_doc

@api_router.put("/budget/{entry_id}")
async def update_budget_entry(entry_id: str, entry: BudgetEntry, user: dict = Depends(get_current_user)):
    entry_doc = entry.model_dump()
    await db.budget_entries.update_one({"id": entry_id, "family_id": user["family_id"]}, {"$set": entry_doc})
    return entry_doc

@api_router.delete("/budget/{entry_id}")
async def delete_budget_entry(entry_id: str, user: dict = Depends(get_current_user)):
    await db.budget_entries.delete_one({"id": entry_id, "family_id": user["family_id"]})
    return {"message": "Entry deleted"}

@api_router.get("/budget/summary")
async def get_budget_summary(user: dict = Depends(get_current_user)):
    entries = await db.budget_entries.find({"family_id": user["family_id"]}, {"_id": 0}).to_list(1000)
    
    total_income = sum(e["amount"] for e in entries if e["type"] == "income")
    total_expenses = sum(e["amount"] for e in entries if e["type"] == "expense")
    
    categories = {}
    monthly = {}
    
    for e in entries:
        cat = e.get("category", "Other")
        if cat not in categories:
            categories[cat] = {"income": 0, "expense": 0}
        categories[cat][e["type"]] += e["amount"]
        
        month = e.get("date", "")[:7]
        if month:
            if month not in monthly:
                monthly[month] = {"income": 0, "expense": 0}
            monthly[month][e["type"]] += e["amount"]
    
    return {
        "total_income": total_income,
        "total_expenses": total_expenses,
        "balance": total_income - total_expenses,
        "by_category": categories,
        "by_month": monthly
    }

# ============== MEAL PLANNER ROUTES ==============

@api_router.get("/meals", response_model=List[MealPlan])
async def get_meal_plans(user: dict = Depends(get_current_user)):
    plans = await db.meal_plans.find({"family_id": user["family_id"]}, {"_id": 0}).to_list(1000)
    for p in plans:
        p.pop("family_id", None)
    return plans

@api_router.post("/meals", response_model=MealPlan)
async def create_meal_plan(plan: MealPlan, user: dict = Depends(get_current_user)):
    plan_doc = plan.model_dump()
    plan_doc["family_id"] = user["family_id"]
    await db.meal_plans.insert_one(plan_doc)
    del plan_doc["_id"]
    del plan_doc["family_id"]
    return plan_doc

@api_router.put("/meals/{plan_id}")
async def update_meal_plan(plan_id: str, plan: MealPlan, user: dict = Depends(get_current_user)):
    plan_doc = plan.model_dump()
    await db.meal_plans.update_one({"id": plan_id, "family_id": user["family_id"]}, {"$set": plan_doc})
    return plan_doc

@api_router.delete("/meals/{plan_id}")
async def delete_meal_plan(plan_id: str, user: dict = Depends(get_current_user)):
    await db.meal_plans.delete_one({"id": plan_id, "family_id": user["family_id"]})
    return {"message": "Plan deleted"}

# ============== RECIPES ROUTES ==============

@api_router.get("/recipes", response_model=List[Recipe])
async def get_recipes(user: dict = Depends(get_current_user)):
    recipes = await db.recipes.find({"family_id": user["family_id"]}, {"_id": 0}).to_list(1000)
    for r in recipes:
        r.pop("family_id", None)
    return recipes

@api_router.post("/recipes", response_model=Recipe)
async def create_recipe(recipe: Recipe, user: dict = Depends(get_current_user)):
    recipe_doc = recipe.model_dump()
    recipe_doc["family_id"] = user["family_id"]
    recipe_doc["created_by"] = user["user_id"]
    await db.recipes.insert_one(recipe_doc)
    del recipe_doc["_id"]
    del recipe_doc["family_id"]
    return recipe_doc

@api_router.get("/recipes/{recipe_id}")
async def get_recipe(recipe_id: str, user: dict = Depends(get_current_user)):
    recipe = await db.recipes.find_one({"id": recipe_id, "family_id": user["family_id"]}, {"_id": 0})
    if not recipe:
        raise HTTPException(status_code=404, detail="Recipe not found")
    return recipe

@api_router.put("/recipes/{recipe_id}")
async def update_recipe(recipe_id: str, recipe: Recipe, user: dict = Depends(get_current_user)):
    recipe_doc = recipe.model_dump()
    await db.recipes.update_one({"id": recipe_id, "family_id": user["family_id"]}, {"$set": recipe_doc})
    return recipe_doc

@api_router.delete("/recipes/{recipe_id}")
async def delete_recipe(recipe_id: str, user: dict = Depends(get_current_user)):
    await db.recipes.delete_one({"id": recipe_id, "family_id": user["family_id"]})
    return {"message": "Recipe deleted"}

# ============== GROCERY LIST ROUTES ==============

@api_router.get("/grocery", response_model=List[GroceryItem])
async def get_grocery_items(user: dict = Depends(get_current_user)):
    items = await db.grocery_items.find({"family_id": user["family_id"]}, {"_id": 0}).to_list(1000)
    for i in items:
        i.pop("family_id", None)
    return items

@api_router.post("/grocery", response_model=GroceryItem)
async def create_grocery_item(item: GroceryItem, user: dict = Depends(get_current_user)):
    item_doc = item.model_dump()
    item_doc["family_id"] = user["family_id"]
    await db.grocery_items.insert_one(item_doc)
    del item_doc["_id"]
    del item_doc["family_id"]
    return item_doc

@api_router.put("/grocery/{item_id}")
async def update_grocery_item(item_id: str, item: GroceryItem, user: dict = Depends(get_current_user)):
    item_doc = item.model_dump()
    await db.grocery_items.update_one({"id": item_id, "family_id": user["family_id"]}, {"$set": item_doc})
    return item_doc

@api_router.delete("/grocery/{item_id}")
async def delete_grocery_item(item_id: str, user: dict = Depends(get_current_user)):
    await db.grocery_items.delete_one({"id": item_id, "family_id": user["family_id"]})
    return {"message": "Item deleted"}

@api_router.delete("/grocery")
async def clear_grocery_list(user: dict = Depends(get_current_user)):
    await db.grocery_items.delete_many({"family_id": user["family_id"], "checked": True})
    return {"message": "Checked items cleared"}

# ============== CONTACTS ROUTES ==============

@api_router.get("/contacts", response_model=List[Contact])
async def get_contacts(user: dict = Depends(get_current_user)):
    contacts = await db.contacts.find({"family_id": user["family_id"]}, {"_id": 0}).to_list(1000)
    for c in contacts:
        c.pop("family_id", None)
    return contacts

@api_router.post("/contacts", response_model=Contact)
async def create_contact(contact: Contact, user: dict = Depends(get_current_user)):
    contact_doc = contact.model_dump()
    contact_doc["family_id"] = user["family_id"]
    await db.contacts.insert_one(contact_doc)
    del contact_doc["_id"]
    del contact_doc["family_id"]
    return contact_doc

@api_router.put("/contacts/{contact_id}")
async def update_contact(contact_id: str, contact: Contact, user: dict = Depends(get_current_user)):
    contact_doc = contact.model_dump()
    await db.contacts.update_one({"id": contact_id, "family_id": user["family_id"]}, {"$set": contact_doc})
    return contact_doc

@api_router.delete("/contacts/{contact_id}")
async def delete_contact(contact_id: str, user: dict = Depends(get_current_user)):
    await db.contacts.delete_one({"id": contact_id, "family_id": user["family_id"]})
    return {"message": "Contact deleted"}

# ============== PANTRY TRACKER ROUTES ==============

@api_router.get("/pantry", response_model=List[PantryItem])
async def get_pantry_items(user: dict = Depends(get_current_user)):
    items = await db.pantry_items.find({"family_id": user["family_id"]}, {"_id": 0}).to_list(1000)
    for i in items:
        i.pop("family_id", None)
    return items

@api_router.post("/pantry", response_model=PantryItem)
async def create_pantry_item(item: PantryItem, user: dict = Depends(get_current_user)):
    item_doc = item.model_dump()
    item_doc["family_id"] = user["family_id"]
    await db.pantry_items.insert_one(item_doc)
    del item_doc["_id"]
    del item_doc["family_id"]
    return item_doc

@api_router.put("/pantry/{item_id}")
async def update_pantry_item(item_id: str, item: PantryItem, user: dict = Depends(get_current_user)):
    item_doc = item.model_dump()
    await db.pantry_items.update_one({"id": item_id, "family_id": user["family_id"]}, {"$set": item_doc})
    return item_doc

@api_router.delete("/pantry/{item_id}")
async def delete_pantry_item(item_id: str, user: dict = Depends(get_current_user)):
    await db.pantry_items.delete_one({"id": item_id, "family_id": user["family_id"]})
    return {"message": "Item deleted"}

@api_router.get("/pantry/barcode/{barcode}")
async def lookup_barcode(barcode: str):
    try:
        response = requests.get(f"https://world.openfoodfacts.org/api/v0/product/{barcode}.json", timeout=5)
        data = response.json()
        if data.get("status") == 1:
            product = data.get("product", {})
            return {
                "found": True,
                "name": product.get("product_name", "Unknown Product"),
                "brand": product.get("brands", ""),
                "category": product.get("categories_tags", ["Other"])[0] if product.get("categories_tags") else "Other"
            }
    except:
        pass
    return {"found": False}

# ============== MEAL SUGGESTIONS ==============

@api_router.get("/suggestions")
async def get_meal_suggestions(user: dict = Depends(get_current_user)):
    pantry_items = await db.pantry_items.find({"family_id": user["family_id"]}, {"_id": 0}).to_list(1000)
    recipes = await db.recipes.find({"family_id": user["family_id"]}, {"_id": 0}).to_list(1000)
    
    pantry_names = [p["name"].lower() for p in pantry_items]
    suggestions = []
    
    for recipe in recipes:
        recipe_ingredients = [i.lower() for i in recipe.get("ingredients", [])]
        matches = sum(1 for ing in recipe_ingredients if any(p in ing for p in pantry_names))
        total = len(recipe_ingredients) if recipe_ingredients else 1
        match_percent = (matches / total) * 100
        
        if matches > 0:
            suggestions.append({
                "recipe": recipe,
                "matches": matches,
                "total_ingredients": total,
                "match_percent": round(match_percent, 1),
                "missing": [ing for ing in recipe_ingredients if not any(p in ing for p in pantry_names)]
            })
    
    suggestions.sort(key=lambda x: x["match_percent"], reverse=True)
    return suggestions[:10]

# ============== STATUS ROUTES ==============

@api_router.get("/")
async def root():
    return {"message": "Family Hub API", "status": "running", "version": "2.0.0"}

@api_router.get("/health")
async def health_check():
    return {"status": "healthy"}

# Include router and configure app
app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ.get('CORS_ORIGINS', '*').split(','),
    allow_methods=["*"],
    allow_headers=["*"],
)

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

if FRONTEND_BUILD_DIR.exists():
    static_dir = FRONTEND_BUILD_DIR / "static"
    if static_dir.exists():
        app.mount("/static", StaticFiles(directory=static_dir), name="static")
    
    @app.get("/")
    async def serve_root():
        return FileResponse(FRONTEND_BUILD_DIR / "index.html")
    
    @app.get("/{full_path:path}")
    async def serve_frontend(full_path: str):
        if full_path.startswith("api"):
            raise HTTPException(status_code=404, detail="Not found")
        
        file_path = FRONTEND_BUILD_DIR / full_path
        if file_path.is_file():
            return FileResponse(file_path)
        
        return FileResponse(FRONTEND_BUILD_DIR / "index.html")

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()
