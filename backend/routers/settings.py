from fastapi import APIRouter, HTTPException, Depends
from models.schemas import FamilySettings
from auth import get_current_user, get_user_role, DEFAULT_FAMILY_SETTINGS, get_smtp_config
from database import db
import os

router = APIRouter(prefix="/api/settings", tags=["settings"])


@router.get("")
async def get_settings(user: dict = Depends(get_current_user)):
    family = await db.families.find_one({"id": user["family_id"]}, {"_id": 0})
    if not family:
        return DEFAULT_FAMILY_SETTINGS
    
    # Merge stored settings with defaults to ensure all modules are present
    stored_settings = family.get("settings", {})
    merged = {**DEFAULT_FAMILY_SETTINGS}
    
    # Merge modules - keep defaults for missing modules, override with stored values
    if stored_settings.get("modules"):
        merged["modules"] = {**DEFAULT_FAMILY_SETTINGS["modules"]}
        for key, val in stored_settings["modules"].items():
            merged["modules"][key] = val
    
    # Merge other sections
    if stored_settings.get("permissions"):
        merged["permissions"] = stored_settings["permissions"]
    if stored_settings.get("theme"):
        merged["theme"] = stored_settings["theme"]
    if stored_settings.get("chore_rewards"):
        merged["chore_rewards"] = stored_settings["chore_rewards"]
    
    return merged


@router.put("")
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


@router.get("/server")
async def get_server_settings(user: dict = Depends(get_current_user)):
    user_role = await get_user_role(user)
    if user_role != "owner":
        raise HTTPException(status_code=403, detail="Only owner can view server settings")
    smtp = get_smtp_config()
    return {
        "smtp_configured": bool(smtp['host']),
        "google_configured": bool(os.environ.get('GOOGLE_CLIENT_ID', '')),
        "smtp_host": smtp['host'],
        "smtp_port": smtp['port'],
        "smtp_user": smtp['user'],
        "smtp_from": smtp['from_addr'],
    }
