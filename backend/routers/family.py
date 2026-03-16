from fastapi import APIRouter, HTTPException, Depends
from models.schemas import FamilyCreate, FamilyUpdate, UserInvite, UserRoleUpdate, QuickAddMember
from auth import (
    get_current_user, get_user_role, check_permission,
    generate_pin, generate_user_pin, hash_password, send_email,
    ROLES, get_smtp_config
)
from database import db
from datetime import datetime, timezone
import uuid
import secrets
import logging

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/family", tags=["family"])


@router.post("/create")
async def create_family(family: FamilyCreate, user: dict = Depends(get_current_user)):
    family_pin = generate_pin()
    family_doc = {
        "id": str(uuid.uuid4()),
        "name": family.name,
        "pin": family_pin,
        "settings": {},
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


@router.get("")
async def get_family(user: dict = Depends(get_current_user)):
    if not user.get("family_id"):
        return None
    family = await db.families.find_one({"id": user["family_id"]}, {"_id": 0})
    return family


@router.put("")
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


@router.post("/regenerate-pin")
async def regenerate_family_pin(user: dict = Depends(get_current_user)):
    user_role = await get_user_role(user)
    if user_role not in ["owner", "parent"]:
        raise HTTPException(status_code=403, detail="Not authorized")
    new_pin = generate_pin()
    await db.families.update_one({"id": user["family_id"]}, {"$set": {"pin": new_pin}})
    return {"pin": new_pin}


@router.get("/members")
async def get_family_members(user: dict = Depends(get_current_user)):
    if not user.get("family_id"):
        return []
    members = await db.users.find({"family_id": user["family_id"]}, {"_id": 0, "password": 0}).to_list(100)
    return members


@router.post("/invite")
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

    inviter = await db.users.find_one({"id": user["user_id"]}, {"_id": 0, "name": 1})
    inviter_name = inviter.get("name", "A family member") if inviter else "A family member"

    email_html = f"""
    <h2>Welcome to {family['name']} on Family Hub!</h2>
    <p>You've been invited by {inviter_name} to join the family.</p>
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


@router.post("/add-member")
async def quick_add_member(member: QuickAddMember, user: dict = Depends(get_current_user)):
    user_role = await get_user_role(user)
    if user_role not in ["owner", "parent"]:
        raise HTTPException(status_code=403, detail="Not authorized to add members")

    if member.email:
        existing = await db.users.find_one({"email": member.email}, {"_id": 0})
        if existing:
            raise HTTPException(status_code=400, detail="A user with this email already exists")

    user_pin = generate_user_pin()
    temp_password = secrets.token_urlsafe(12) if member.email else None

    new_user = {
        "id": str(uuid.uuid4()),
        "name": member.name,
        "email": member.email if member.email else None,
        "password": hash_password(temp_password) if temp_password else None,
        "role": member.role,
        "user_pin": user_pin,
        "avatar_seed": str(uuid.uuid4()),
        "family_id": user["family_id"],
        "points": 0,
        "added_by": user["user_id"],
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    await db.users.insert_one(new_user)

    result = {
        "id": new_user["id"],
        "name": member.name,
        "role": member.role,
        "user_pin": user_pin,
        "email_sent": False
    }

    smtp_host = get_smtp_config()['host']
    if member.email and smtp_host:
        try:
            family = await db.families.find_one({"id": user["family_id"]}, {"_id": 0})
            inviter = await db.users.find_one({"id": user["user_id"]}, {"_id": 0, "name": 1})
            inviter_name = inviter.get("name", "A family member") if inviter else "A family member"

            email_html = f"""
            <h2>Welcome to {family['name']} on Family Hub!</h2>
            <p>You've been invited by {inviter_name} to join the family.</p>
            <p><strong>Your login credentials:</strong></p>
            <ul>
                <li>Email: {member.email}</li>
                <li>Temporary Password: {temp_password}</li>
                <li>Your PIN: {user_pin}</li>
            </ul>
            """
            await send_email(member.email, f"You're invited to {family['name']} - Family Hub", email_html)
            result["email_sent"] = True
            result["temp_password"] = temp_password
        except Exception as e:
            logger.error(f"Failed to send invite email: {e}")
            result["email_error"] = "Email could not be sent. Check SMTP configuration."
    elif member.email and not smtp_host:
        result["email_error"] = "SMTP not configured. Share the PIN manually."

    return result


@router.put("/members/{member_id}/role")
async def update_member_role(member_id: str, role_update: UserRoleUpdate, user: dict = Depends(get_current_user)):
    user_role = await get_user_role(user)
    if user_role not in ["owner", "parent"]:
        raise HTTPException(status_code=403, detail="Not authorized")

    if role_update.role not in ROLES:
        raise HTTPException(status_code=400, detail="Invalid role")

    target_user = await db.users.find_one({"id": member_id, "family_id": user["family_id"]}, {"_id": 0})
    if not target_user:
        raise HTTPException(status_code=404, detail="Member not found")
    if target_user.get("role") == "owner":
        raise HTTPException(status_code=403, detail="Cannot change owner role")

    await db.users.update_one({"id": member_id}, {"$set": {"role": role_update.role}})
    return {"message": "Role updated"}


@router.delete("/members/{member_id}")
async def remove_member(member_id: str, user: dict = Depends(get_current_user)):
    user_role = await get_user_role(user)
    if user_role not in ["owner", "parent"]:
        raise HTTPException(status_code=403, detail="Not authorized")

    target_user = await db.users.find_one({"id": member_id, "family_id": user["family_id"]}, {"_id": 0})
    if not target_user:
        raise HTTPException(status_code=404, detail="Member not found")
    if target_user.get("role") == "owner":
        raise HTTPException(status_code=403, detail="Cannot remove owner")

    # If user never logged in (pending invite), fully delete them
    if not target_user.get("last_login"):
        await db.users.delete_one({"id": member_id})
        return {"message": "Pending invite removed"}

    # Fully delete the user so they can be re-invited later
    await db.users.delete_one({"id": member_id})
    return {"message": "Member removed"}


@router.post("/members/{member_id}/regenerate-pin")
async def regenerate_user_pin_route(member_id: str, user: dict = Depends(get_current_user)):
    user_role = await get_user_role(user)
    if user_role not in ["owner", "parent"] and user["user_id"] != member_id:
        raise HTTPException(status_code=403, detail="Not authorized")

    new_pin = generate_user_pin()
    await db.users.update_one({"id": member_id}, {"$set": {"user_pin": new_pin}})
    return {"pin": new_pin}
