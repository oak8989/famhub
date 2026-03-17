from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from typing import List
from models.schemas import NOKEntry
from auth import get_current_user
from database import db
import uuid
import os
import base64
import logging

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/nok-box", tags=["nok-box"])

UPLOAD_DIR = "/app/backend/uploads/nok"
os.makedirs(UPLOAD_DIR, exist_ok=True)


@router.get("")
async def get_entries(user: dict = Depends(get_current_user)):
    entries = await db.nok_entries.find({"family_id": user["family_id"]}, {"_id": 0}).to_list(500)
    return entries


@router.post("")
async def create_entry(entry: NOKEntry, user: dict = Depends(get_current_user)):
    doc = entry.model_dump()
    doc["family_id"] = user["family_id"]
    doc["created_by"] = user["user_id"]
    await db.nok_entries.insert_one(doc)
    doc.pop("_id", None)
    doc.pop("family_id", None)
    return doc


@router.put("/{entry_id}")
async def update_entry(entry_id: str, entry: NOKEntry, user: dict = Depends(get_current_user)):
    update_data = entry.model_dump()
    update_data.pop("id", None)
    result = await db.nok_entries.update_one(
        {"id": entry_id, "family_id": user["family_id"]},
        {"$set": update_data}
    )
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Entry not found")
    updated = await db.nok_entries.find_one({"id": entry_id}, {"_id": 0, "family_id": 0})
    return updated


@router.delete("/{entry_id}")
async def delete_entry(entry_id: str, user: dict = Depends(get_current_user)):
    entry = await db.nok_entries.find_one({"id": entry_id, "family_id": user["family_id"]}, {"_id": 0})
    if not entry:
        raise HTTPException(status_code=404, detail="Entry not found")
    if entry.get("file_url") and entry["file_url"].startswith("/api/nok-box/files/"):
        filename = entry["file_url"].split("/")[-1]
        filepath = os.path.join(UPLOAD_DIR, filename)
        if os.path.exists(filepath):
            os.remove(filepath)
    await db.nok_entries.delete_one({"id": entry_id, "family_id": user["family_id"]})
    return {"message": "Entry deleted"}


@router.post("/upload")
async def upload_file(file: UploadFile = File(...), user: dict = Depends(get_current_user)):
    if file.size > 10 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="File too large (max 10MB)")
    ext = os.path.splitext(file.filename)[1] or ".bin"
    safe_name = f"{uuid.uuid4()}{ext}"
    filepath = os.path.join(UPLOAD_DIR, safe_name)
    content = await file.read()
    with open(filepath, "wb") as f:
        f.write(content)
    return {
        "file_url": f"/api/nok-box/files/{safe_name}",
        "file_name": file.filename,
    }


@router.get("/files/{filename}")
async def serve_file(filename: str, user: dict = Depends(get_current_user)):
    from fastapi.responses import FileResponse
    filepath = os.path.join(UPLOAD_DIR, filename)
    if not os.path.exists(filepath):
        raise HTTPException(status_code=404, detail="File not found")
    return FileResponse(filepath, filename=filename)
