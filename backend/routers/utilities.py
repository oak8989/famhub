from fastapi import APIRouter, HTTPException, Depends, Query, UploadFile, File
from fastapi.responses import StreamingResponse
from models.schemas import PushSubscription
from auth import get_current_user
from database import db
from datetime import datetime, timezone
import os
import io
import json
import qrcode
import base64
import logging

logger = logging.getLogger(__name__)

try:
    from pywebpush import webpush, WebPushException
    WEBPUSH_AVAILABLE = True
except ImportError:
    WEBPUSH_AVAILABLE = False
    logger.info("pywebpush not available - push notifications disabled")

VAPID_PRIVATE_KEY = os.environ.get('VAPID_PRIVATE_KEY', 'E-nV2cLmXz45Sjw1AEI9McBBDAxsT8A-UYJLVllZ-Bg')
VAPID_PUBLIC_KEY = os.environ.get('VAPID_PUBLIC_KEY', 'BFmcNw6Is75p9_i8pfadTILCoDFCT9nWeCSQAAadDB7CPWKdRPJSNZszz9KtfGW1RpRsAdlrze9YKHW5u-yODOI')
VAPID_CLAIMS_EMAIL = os.environ.get('VAPID_EMAIL', 'mailto:admin@familyhub.local')

router = APIRouter(prefix="/api", tags=["utilities"])


# ==================== Push Notifications ====================

async def send_push_to_family(family_id: str, title: str, body: str, url: str = "/"):
    """Send push notification to all subscribed members of a family."""
    if not WEBPUSH_AVAILABLE:
        return
    subscriptions = await db.push_subscriptions.find(
        {"family_id": family_id}, {"_id": 0}
    ).to_list(100)

    dead_subs = []
    for sub in subscriptions:
        try:
            payload = json.dumps({
                "title": title,
                "body": body,
                "url": url,
                "timestamp": datetime.now(timezone.utc).isoformat()
            })
            webpush(
                subscription_info=sub["subscription"],
                data=payload,
                vapid_private_key=VAPID_PRIVATE_KEY,
                vapid_claims={"sub": VAPID_CLAIMS_EMAIL}
            )
        except WebPushException as e:
            if e.response and e.response.status_code in (404, 410):
                dead_subs.append(sub["user_id"])
            logger.debug(f"Push failed for {sub['user_id']}: {e}")
        except Exception as e:
            logger.debug(f"Push error: {e}")

    # Clean up expired subscriptions
    for uid in dead_subs:
        await db.push_subscriptions.delete_one({"user_id": uid})


@router.post("/notifications/subscribe")
async def subscribe_push(subscription: PushSubscription, user: dict = Depends(get_current_user)):
    await db.push_subscriptions.update_one(
        {"user_id": user["user_id"]},
        {"$set": {
            "user_id": user["user_id"],
            "family_id": user["family_id"],
            "subscription": subscription.model_dump(),
            "updated_at": datetime.now(timezone.utc).isoformat()
        }},
        upsert=True
    )
    return {"message": "Subscribed to notifications"}


@router.delete("/notifications/unsubscribe")
async def unsubscribe_push(user: dict = Depends(get_current_user)):
    await db.push_subscriptions.delete_one({"user_id": user["user_id"]})
    return {"message": "Unsubscribed from notifications"}


@router.get("/notifications/vapid-key")
async def get_vapid_public_key():
    return {"public_key": VAPID_PUBLIC_KEY}


# ==================== QR Code ====================

@router.get("/qr-code")
async def generate_qr_code(url: str = Query(..., description="Server URL to encode")):
    qr = qrcode.QRCode(version=1, box_size=10, border=4)
    qr.add_data(url)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    buffer = io.BytesIO()
    img.save(buffer, format="PNG")
    buffer.seek(0)
    return StreamingResponse(buffer, media_type="image/png")


@router.get("/qr-code/base64")
async def get_qr_code_base64(url: str = Query(..., description="Server URL to encode")):
    qr = qrcode.QRCode(version=1, box_size=8, border=2)
    qr.add_data(url)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    buffer = io.BytesIO()
    img.save(buffer, format="PNG")
    buffer.seek(0)
    base64_str = base64.b64encode(buffer.getvalue()).decode()
    return {"qr_code": f"data:image/png;base64,{base64_str}", "url": url}


# ==================== Data Export ====================

COLLECTION_MAP = {
    "calendar_events": "calendar_events",
    "shopping_items": "shopping_items",
    "tasks": "tasks",
    "chores": "chores",
    "rewards": "rewards",
    "notes": "notes",
    "budget_entries": "budget_entries",
    "meal_plans": "meal_plans",
    "recipes": "recipes",
    "grocery_items": "grocery_items",
    "contacts": "contacts",
    "pantry_items": "pantry_items",
}


@router.get("/export/data")
async def export_family_data(user: dict = Depends(get_current_user)):
    family_id = user["family_id"]
    data = {
        "exported_at": datetime.now(timezone.utc).isoformat(),
        "exported_by": user["user_id"],
        "version": "2.2.0",
        "family": await db.families.find_one({"id": family_id}, {"_id": 0}),
        "members": await db.users.find({"family_id": family_id}, {"_id": 0, "password": 0}).to_list(100),
    }
    for key, collection_name in COLLECTION_MAP.items():
        data[key] = await db[collection_name].find({"family_id": family_id}, {"_id": 0}).to_list(1000)

    json_str = json.dumps(data, indent=2, default=str)
    return StreamingResponse(
        io.BytesIO(json_str.encode()),
        media_type="application/json",
        headers={"Content-Disposition": f"attachment; filename=famhub-backup-{datetime.now().strftime('%Y%m%d')}.json"}
    )


@router.get("/export/csv/{module}")
async def export_module_csv(module: str, user: dict = Depends(get_current_user)):
    family_id = user["family_id"]
    collections = {
        "calendar": ("calendar_events", ["id", "title", "description", "date", "time", "color"]),
        "shopping": ("shopping_items", ["id", "name", "quantity", "category", "checked"]),
        "tasks": ("tasks", ["id", "title", "description", "priority", "assigned_to", "due_date", "completed"]),
        "chores": ("chores", ["id", "title", "description", "difficulty", "points", "assigned_to", "completed"]),
        "budget": ("budget_entries", ["id", "description", "amount", "type", "category", "date"]),
        "contacts": ("contacts", ["id", "name", "email", "phone", "address"]),
        "pantry": ("pantry_items", ["id", "name", "quantity", "unit", "category", "expiry_date"]),
    }
    if module not in collections:
        raise HTTPException(status_code=400, detail=f"Invalid module. Choose from: {', '.join(collections.keys())}")

    collection_name, fields = collections[module]
    items = await db[collection_name].find({"family_id": family_id}, {"_id": 0}).to_list(1000)
    output = io.StringIO()
    output.write(",".join(fields) + "\n")
    for item in items:
        row = [str(item.get(f, "")).replace(",", ";").replace("\n", " ") for f in fields]
        output.write(",".join(row) + "\n")
    return StreamingResponse(
        io.BytesIO(output.getvalue().encode()),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename={module}-export-{datetime.now().strftime('%Y%m%d')}.csv"}
    )


# ==================== Data Import (Merge) ====================

@router.post("/import/data")
async def import_family_data(user: dict = Depends(get_current_user), file: UploadFile = File(...)):
    family_id = user["family_id"]
    if not family_id:
        raise HTTPException(status_code=400, detail="No family associated")

    try:
        content = await file.read()
        data = json.loads(content)
    except (json.JSONDecodeError, UnicodeDecodeError):
        raise HTTPException(status_code=400, detail="Invalid JSON file")

    stats = {}

    for key, collection_name in COLLECTION_MAP.items():
        items = data.get(key, [])
        if not items or not isinstance(items, list):
            continue

        imported = 0
        skipped = 0
        for item in items:
            if not isinstance(item, dict) or "id" not in item:
                skipped += 1
                continue
            # Check for duplicates by id
            existing = await db[collection_name].find_one(
                {"id": item["id"], "family_id": family_id}, {"_id": 0}
            )
            if existing:
                skipped += 1
                continue
            item["family_id"] = family_id
            item.pop("_id", None)
            await db[collection_name].insert_one(item)
            imported += 1

        if imported > 0 or skipped > 0:
            stats[key] = {"imported": imported, "skipped": skipped}

    # Import family settings if present
    if data.get("family") and isinstance(data["family"], dict):
        settings = data["family"].get("settings")
        if settings:
            await db.families.update_one(
                {"id": family_id},
                {"$set": {"settings": settings}},
            )
            stats["settings"] = {"imported": 1, "skipped": 0}

    total_imported = sum(s["imported"] for s in stats.values())
    total_skipped = sum(s["skipped"] for s in stats.values())

    return {
        "message": f"Import complete: {total_imported} items imported, {total_skipped} duplicates skipped",
        "total_imported": total_imported,
        "total_skipped": total_skipped,
        "details": stats
    }
