from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import RedirectResponse
from typing import List
from models.schemas import CalendarEvent
from auth import get_current_user, GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET, GOOGLE_REDIRECT_URI
from database import db
from routers.websocket import notify_family
from routers.utilities import send_push_to_family
import os
import logging
import requests
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request as GoogleRequest
from googleapiclient.discovery import build

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/calendar", tags=["calendar"])


@router.get("", response_model=List[CalendarEvent])
async def get_events(user: dict = Depends(get_current_user)):
    events = await db.calendar_events.find({"family_id": user["family_id"]}, {"_id": 0}).to_list(1000)
    for e in events:
        e.pop("family_id", None)
    return events


@router.post("", response_model=CalendarEvent)
async def create_event(event: CalendarEvent, user: dict = Depends(get_current_user)):
    event_doc = event.model_dump()
    event_doc["family_id"] = user["family_id"]
    event_doc["created_by"] = user["user_id"]
    await db.calendar_events.insert_one(event_doc)
    del event_doc["_id"]
    del event_doc["family_id"]
    await notify_family(user["family_id"], "update", "calendar")
    await send_push_to_family(user["family_id"], "New Event", f"'{event_doc['title']}' on {event_doc['date']}", "/calendar")
    return event_doc


@router.put("/{event_id}")
async def update_event(event_id: str, event: CalendarEvent, user: dict = Depends(get_current_user)):
    event_doc = event.model_dump()
    await db.calendar_events.update_one({"id": event_id, "family_id": user["family_id"]}, {"$set": event_doc})
    return event_doc


@router.delete("/{event_id}")
async def delete_event(event_id: str, user: dict = Depends(get_current_user)):
    await db.calendar_events.delete_one({"id": event_id, "family_id": user["family_id"]})
    return {"message": "Event deleted"}


# Google Calendar
@router.get("/google/auth")
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


@router.get("/google/callback")
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
        return RedirectResponse("/settings?error=google_auth_failed")
    await db.users.update_one({"id": state}, {"$set": {"google_tokens": token_resp}})
    return RedirectResponse("/settings?google_connected=true")


@router.post("/google/sync")
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
            logger.error(f"Failed to sync event: {e}")
    return {"synced": synced}


@router.delete("/google/disconnect")
async def disconnect_google_calendar(user: dict = Depends(get_current_user)):
    await db.users.update_one({"id": user["user_id"]}, {"$set": {"google_tokens": None}})
    return {"message": "Google Calendar disconnected"}
