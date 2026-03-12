from fastapi import APIRouter, HTTPException, Depends
from auth import get_current_user, get_user_role
from database import db
from pathlib import Path
from dotenv import load_dotenv, set_key
from pydantic import BaseModel
import os
import subprocess
import smtplib
import logging

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/admin", tags=["admin"])

ROOT_DIR = Path(__file__).parent.parent
ENV_FILE = ROOT_DIR / '.env'


def _get_env(key: str, default: str = "") -> str:
    return os.environ.get(key, default)


def _save_env(key: str, value: str):
    if ENV_FILE.exists():
        set_key(str(ENV_FILE), key, value)
    os.environ[key] = value


async def require_owner(user: dict = Depends(get_current_user)):
    role = await get_user_role(user)
    if role != "owner":
        raise HTTPException(status_code=403, detail="Owner access required")
    return user


# --- Models ---

class SMTPConfig(BaseModel):
    smtp_host: str = ""
    smtp_port: int = 587
    smtp_user: str = ""
    smtp_password: str = ""
    smtp_from: str = ""


class GoogleConfig(BaseModel):
    google_client_id: str = ""
    google_client_secret: str = ""
    google_redirect_uri: str = ""


class OpenAIConfig(BaseModel):
    openai_api_key: str = ""


class ServerConfig(BaseModel):
    jwt_secret: str = ""
    cors_origins: str = "*"
    db_name: str = "family_hub"
    server_url: str = ""


# --- Endpoints ---

@router.get("/status")
async def get_status(user: dict = Depends(require_owner)):
    backend_running = True  # If we're responding, backend is running

    db_connected = False
    try:
        from motor.motor_asyncio import AsyncIOMotorClient
        test_client = AsyncIOMotorClient(
            _get_env("MONGO_URL", "mongodb://localhost:27017"),
            serverSelectionTimeoutMS=2000
        )
        await test_client.server_info()
        db_connected = True
        test_client.close()
    except Exception:
        pass

    return {
        "backend": backend_running,
        "database": db_connected,
        "smtp": bool(_get_env("SMTP_HOST")),
        "openai": bool(_get_env("OPENAI_API_KEY")),
        "google": bool(_get_env("GOOGLE_CLIENT_ID")),
    }


@router.get("/config")
async def get_config(user: dict = Depends(require_owner)):
    return {
        "smtp_host": _get_env("SMTP_HOST"),
        "smtp_port": int(_get_env("SMTP_PORT", "587")),
        "smtp_user": _get_env("SMTP_USER"),
        "smtp_from": _get_env("SMTP_FROM"),
        "google_client_id": _get_env("GOOGLE_CLIENT_ID"),
        "google_redirect_uri": _get_env("GOOGLE_REDIRECT_URI"),
        "openai_api_key": "***" if _get_env("OPENAI_API_KEY") else "",
        "jwt_secret": "***" if _get_env("JWT_SECRET") else "",
        "cors_origins": _get_env("CORS_ORIGINS", "*"),
        "db_name": _get_env("DB_NAME", "family_hub"),
        "server_url": _get_env("SERVER_URL", ""),
    }


@router.post("/config/smtp")
async def save_smtp(config: SMTPConfig, user: dict = Depends(require_owner)):
    _save_env("SMTP_HOST", config.smtp_host)
    _save_env("SMTP_PORT", str(config.smtp_port))
    _save_env("SMTP_USER", config.smtp_user)
    if config.smtp_password:
        _save_env("SMTP_PASSWORD", config.smtp_password)
    _save_env("SMTP_FROM", config.smtp_from)
    return {"success": True, "message": "SMTP settings saved"}


@router.post("/config/google")
async def save_google(config: GoogleConfig, user: dict = Depends(require_owner)):
    _save_env("GOOGLE_CLIENT_ID", config.google_client_id)
    if config.google_client_secret:
        _save_env("GOOGLE_CLIENT_SECRET", config.google_client_secret)
    _save_env("GOOGLE_REDIRECT_URI", config.google_redirect_uri)
    return {"success": True, "message": "Google Calendar settings saved"}


@router.post("/config/openai")
async def save_openai(config: OpenAIConfig, user: dict = Depends(require_owner)):
    if config.openai_api_key:
        _save_env("OPENAI_API_KEY", config.openai_api_key)
    return {"success": True, "message": "OpenAI settings saved"}


@router.post("/config/server")
async def save_server(config: ServerConfig, user: dict = Depends(require_owner)):
    if config.jwt_secret:
        _save_env("JWT_SECRET", config.jwt_secret)
    _save_env("CORS_ORIGINS", config.cors_origins)
    _save_env("DB_NAME", config.db_name)
    if config.server_url is not None:
        _save_env("SERVER_URL", config.server_url.rstrip("/"))
    return {"success": True, "message": "Server settings saved"}


@router.post("/test-email")
async def test_email(user: dict = Depends(require_owner)):
    try:
        smtp_host = _get_env("SMTP_HOST")
        smtp_port = int(_get_env("SMTP_PORT", "587"))
        smtp_user = _get_env("SMTP_USER")
        smtp_password = _get_env("SMTP_PASSWORD")
        if not smtp_host:
            return {"success": False, "message": "SMTP not configured"}
        server = smtplib.SMTP(smtp_host, smtp_port, timeout=10)
        server.starttls()
        server.login(smtp_user, smtp_password)
        server.quit()
        return {"success": True, "message": "SMTP connection successful!"}
    except Exception as e:
        return {"success": False, "message": f"SMTP test failed: {str(e)}"}


@router.get("/logs")
async def get_logs(type: str = "backend", user: dict = Depends(require_owner)):
    log_files = {
        "backend": ["/var/log/supervisor/familyhub.log", "/var/log/supervisor/backend.out.log"],
        "frontend": ["/var/log/supervisor/frontend.log", "/var/log/supervisor/frontend.out.log"],
        "error": ["/var/log/supervisor/familyhub_err.log", "/var/log/supervisor/backend.err.log", "/var/log/supervisor/frontend.err.log"],
    }
    paths = log_files.get(type, log_files["backend"])
    for log_file in paths:
        try:
            if os.path.exists(log_file):
                with open(log_file, 'r') as f:
                    lines = f.readlines()
                    return {"logs": "".join(lines[-100:])}
        except Exception:
            continue
    return {"logs": f"No log files found. Checked: {', '.join(paths)}"}


@router.post("/reboot")
async def reboot_server(user: dict = Depends(require_owner)):
    try:
        subprocess.Popen(
            ["supervisorctl", "restart", "all"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )
        return {"success": True, "message": "Server is restarting..."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
