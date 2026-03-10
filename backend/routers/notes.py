from fastapi import APIRouter, Depends
from typing import List
from models.schemas import Note
from auth import get_current_user
from database import db
from routers.websocket import notify_family
from routers.utilities import send_push_to_family
from datetime import datetime, timezone

router = APIRouter(prefix="/api/notes", tags=["notes"])


@router.get("", response_model=List[Note])
async def get_notes(user: dict = Depends(get_current_user)):
    notes = await db.notes.find({"family_id": user["family_id"]}, {"_id": 0}).to_list(1000)
    for n in notes:
        n.pop("family_id", None)
    return notes


@router.post("", response_model=Note)
async def create_note(note: Note, user: dict = Depends(get_current_user)):
    note_doc = note.model_dump()
    note_doc["family_id"] = user["family_id"]
    note_doc["created_by"] = user["user_id"]
    await db.notes.insert_one(note_doc)
    del note_doc["_id"]
    del note_doc["family_id"]
    await notify_family(user["family_id"], "update", "notes")
    await send_push_to_family(user["family_id"], "New Note", f"'{note_doc['title']}' was shared", "/notes")
    return note_doc


@router.put("/{note_id}")
async def update_note(note_id: str, note: Note, user: dict = Depends(get_current_user)):
    note_doc = note.model_dump()
    note_doc["updated_at"] = datetime.now(timezone.utc).isoformat()
    await db.notes.update_one({"id": note_id, "family_id": user["family_id"]}, {"$set": note_doc})
    return note_doc


@router.delete("/{note_id}")
async def delete_note(note_id: str, user: dict = Depends(get_current_user)):
    await db.notes.delete_one({"id": note_id, "family_id": user["family_id"]})
    return {"message": "Note deleted"}
