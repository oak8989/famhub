import os
import secrets
import string
from datetime import datetime, timezone
from fastapi import Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import jwt
import bcrypt
import logging
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from database import db

JWT_SECRET = os.environ.get('JWT_SECRET', 'family-hub-secret-key-2024')
JWT_ALGORITHM = "HS256"

SMTP_HOST = os.environ.get('SMTP_HOST', '')
SMTP_PORT = int(os.environ.get('SMTP_PORT', '587'))
SMTP_USER = os.environ.get('SMTP_USER', '')
SMTP_PASSWORD = os.environ.get('SMTP_PASSWORD', '')
SMTP_FROM = os.environ.get('SMTP_FROM', '')


def get_smtp_config():
    return {
        'host': os.environ.get('SMTP_HOST', ''),
        'port': int(os.environ.get('SMTP_PORT', '587')),
        'user': os.environ.get('SMTP_USER', ''),
        'password': os.environ.get('SMTP_PASSWORD', ''),
        'from_addr': os.environ.get('SMTP_FROM', ''),
    }

GOOGLE_CLIENT_ID = os.environ.get('GOOGLE_CLIENT_ID', '')
GOOGLE_CLIENT_SECRET = os.environ.get('GOOGLE_CLIENT_SECRET', '')
GOOGLE_REDIRECT_URI = os.environ.get('GOOGLE_REDIRECT_URI', '')


def get_google_config():
    return {
        'client_id': os.environ.get('GOOGLE_CLIENT_ID', ''),
        'client_secret': os.environ.get('GOOGLE_CLIENT_SECRET', ''),
        'redirect_uri': os.environ.get('GOOGLE_REDIRECT_URI', ''),
    }

EMERGENT_LLM_KEY = os.environ.get('EMERGENT_LLM_KEY', '')
OPENAI_API_KEY = os.environ.get('OPENAI_API_KEY', '')

logger = logging.getLogger(__name__)
security = HTTPBearer(auto_error=False)

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
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid token")

def check_permission(user_role: str, required_permission: str) -> bool:
    role_info = ROLES.get(user_role, ROLES["child"])
    return role_info.get(required_permission, False)

async def get_user_role(user: dict) -> str:
    user_data = await db.users.find_one({"id": user["user_id"]}, {"_id": 0})
    if not user_data:
        return user.get("role", "child")
    return user_data.get("role", "member")

async def send_email(to_email: str, subject: str, html_content: str):
    smtp = get_smtp_config()
    if not all([smtp['host'], smtp['user'], smtp['password']]):
        logger.warning("SMTP not configured, skipping email")
        return False
    try:
        msg = MIMEMultipart('alternative')
        msg['Subject'] = subject
        msg['From'] = smtp['from_addr'] or smtp['user']
        msg['To'] = to_email
        msg.attach(MIMEText(html_content, 'html'))
        with smtplib.SMTP(smtp['host'], smtp['port']) as server:
            server.starttls()
            server.login(smtp['user'], smtp['password'])
            server.send_message(msg)
        return True
    except Exception as e:
        logger.error(f"Failed to send email: {e}")
        return False
