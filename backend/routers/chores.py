from fastapi import APIRouter, HTTPException, Depends
from models.schemas import Chore, Reward, RewardClaim
from auth import get_current_user, get_user_role, DEFAULT_FAMILY_SETTINGS
from database import db
from routers.websocket import notify_family
from routers.utilities import send_push_to_family
from datetime import datetime, timezone
import uuid

router = APIRouter(prefix="/api", tags=["chores"])


@router.get("/chores")
async def get_chores(user: dict = Depends(get_current_user)):
    chores = await db.chores.find({"family_id": user["family_id"]}, {"_id": 0}).to_list(1000)
    for c in chores:
        c.pop("family_id", None)
    return chores


@router.post("/chores")
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


@router.put("/chores/{chore_id}")
async def update_chore(chore_id: str, chore: Chore, user: dict = Depends(get_current_user)):
    chore_doc = chore.model_dump()
    if chore.assigned_to:
        assigned_user = await db.users.find_one({"id": chore.assigned_to}, {"_id": 0})
        if assigned_user:
            chore_doc["assigned_to_name"] = assigned_user.get("name")
    await db.chores.update_one({"id": chore_id, "family_id": user["family_id"]}, {"$set": chore_doc})
    return chore_doc


@router.post("/chores/{chore_id}/complete")
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
    await db.users.update_one({"id": completer_id}, {"$inc": {"points": chore.get("points", 10)}})
    await notify_family(user["family_id"], "update", "chores")
    await send_push_to_family(user["family_id"], "Chore Complete!", f"'{chore['title']}' done! +{chore.get('points', 10)} points", "/chores")
    return {"message": "Chore completed", "points_earned": chore.get("points", 10)}


@router.delete("/chores/{chore_id}")
async def delete_chore(chore_id: str, user: dict = Depends(get_current_user)):
    await db.chores.delete_one({"id": chore_id, "family_id": user["family_id"]})
    return {"message": "Chore deleted"}


@router.get("/rewards")
async def get_rewards(user: dict = Depends(get_current_user)):
    rewards = await db.rewards.find({"family_id": user["family_id"]}, {"_id": 0}).to_list(100)
    for r in rewards:
        r.pop("family_id", None)
    return rewards


@router.post("/rewards")
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


@router.post("/rewards/claim")
async def claim_reward(claim: RewardClaim, user: dict = Depends(get_current_user)):
    reward = await db.rewards.find_one({"id": claim.reward_id, "family_id": user["family_id"]}, {"_id": 0})
    if not reward:
        raise HTTPException(status_code=404, detail="Reward not found")
    claimer = await db.users.find_one({"id": claim.user_id}, {"_id": 0})
    if not claimer or claimer.get("family_id") != user["family_id"]:
        raise HTTPException(status_code=404, detail="User not found")
    if claimer.get("points", 0) < reward["points_required"]:
        raise HTTPException(status_code=400, detail="Not enough points")

    await db.users.update_one({"id": claim.user_id}, {"$inc": {"points": -reward["points_required"]}})
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


@router.get("/reward-claims")
async def get_reward_claims(user: dict = Depends(get_current_user)):
    claims = await db.reward_claims.find(
        {"family_id": user["family_id"]}, {"_id": 0}
    ).sort("claimed_at", -1).to_list(200)
    user_ids = list({c["user_id"] for c in claims})
    users = {}
    if user_ids:
        user_docs = await db.users.find({"id": {"$in": user_ids}}, {"_id": 0, "id": 1, "name": 1}).to_list(100)
        users = {u["id"]: u["name"] for u in user_docs}
    for c in claims:
        c["user_name"] = users.get(c["user_id"], "Unknown")
        c.pop("family_id", None)
    return claims




@router.get("/leaderboard")
async def get_leaderboard(user: dict = Depends(get_current_user)):
    members = await db.users.find(
        {"family_id": user["family_id"]},
        {"_id": 0, "id": 1, "name": 1, "points": 1, "avatar_seed": 1}
    ).sort("points", -1).to_list(100)
    return members


@router.delete("/rewards/{reward_id}")
async def delete_reward(reward_id: str, user: dict = Depends(get_current_user)):
    user_role = await get_user_role(user)
    if user_role not in ["owner", "parent"]:
        raise HTTPException(status_code=403, detail="Not authorized")
    await db.rewards.delete_one({"id": reward_id, "family_id": user["family_id"]})
    return {"message": "Reward deleted"}
