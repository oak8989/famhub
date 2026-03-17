from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import RedirectResponse
from typing import List
from models.schemas import CalendarEvent
from auth import get_current_user, get_google_config
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
    g = get_google_config()
    if not g['client_id'] or not g['client_secret']:
        raise HTTPException(status_code=400, detail="Google Calendar not configured. Ask the hub owner to set up Google API credentials in Settings > Server > Google.")
    if g['client_id'] in ('test-client-id', 'test-client-id.apps.googleusercontent.com', ''):
        raise HTTPException(status_code=400, detail="Google Calendar has placeholder credentials. The hub owner needs to add real Google OAuth credentials in Settings > Server > Google.")
    server_url = os.environ.get("SERVER_URL", "").rstrip("/")
    redirect_uri = g['redirect_uri'] or (f"{server_url}/api/calendar/google/callback" if server_url else "")
    if not redirect_uri:
        raise HTTPException(status_code=400, detail="Server URL is not configured. The hub owner must set the Server URL in Settings > Server before Google Calendar can work.")
    auth_url = (
        f"https://accounts.google.com/o/oauth2/auth?"
        f"client_id={g['client_id']}&"
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
    g = get_google_config()
    server_url = os.environ.get("SERVER_URL", "").rstrip("/")
    redirect_uri = g['redirect_uri'] or (f"{server_url}/api/calendar/google/callback" if server_url else "")
    token_resp = requests.post('https://oauth2.googleapis.com/token', data={
        'code': code,
        'client_id': g['client_id'],
        'client_secret': g['client_secret'],
        'redirect_uri': redirect_uri,
        'grant_type': 'authorization_code'
    }).json()
    if 'error' in token_resp:
        return RedirectResponse("/calendar?error=google_auth_failed")
    await db.users.update_one({"id": state}, {"$set": {"google_tokens": token_resp}})
    return RedirectResponse("/calendar?google_connected=true")


@router.post("/google/sync")
async def sync_google_calendar(user: dict = Depends(get_current_user)):
    g = get_google_config()
    user_data = await db.users.find_one({"id": user["user_id"]}, {"_id": 0})
    if not user_data.get("google_tokens"):
        raise HTTPException(status_code=400, detail="Google Calendar not connected")
    tokens = user_data["google_tokens"]
    creds = Credentials(
        token=tokens.get('access_token'),
        refresh_token=tokens.get('refresh_token'),
        token_uri='https://oauth2.googleapis.com/token',
        client_id=g['client_id'],
        client_secret=g['client_secret']
    )
    if creds.expired and creds.refresh_token:
        creds.refresh(GoogleRequest())
        await db.users.update_one(
            {"id": user["user_id"]},
            {"$set": {"google_tokens.access_token": creds.token}}
        )
    service = build('calendar', 'v3', credentials=creds)

    pushed = 0
    imported = 0

    # Push local events to Google
    local_events = await db.calendar_events.find({"family_id": user["family_id"]}, {"_id": 0}).to_list(1000)
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
            pushed += 1
        except Exception as e:
            logger.error(f"Failed to push event: {e}")

    # Import events from Google
    try:
        from datetime import datetime, timezone, timedelta
        import uuid
        now = datetime.now(timezone.utc)
        time_min = now.isoformat()
        time_max = (now + timedelta(days=90)).isoformat()
        google_events = service.events().list(
            calendarId='primary',
            timeMin=time_min,
            timeMax=time_max,
            maxResults=100,
            singleEvents=True,
            orderBy='startTime'
        ).execute().get('items', [])

        existing_google_ids = {e.get("google_event_id") for e in local_events if e.get("google_event_id")}
        for ge in google_events:
            if ge['id'] in existing_google_ids:
                continue
            start = ge.get('start', {})
            date_str = start.get('date') or (start.get('dateTime', '')[:10])
            time_str = start.get('dateTime', '')[11:16] if start.get('dateTime') else ''
            if not date_str:
                continue
            new_event = {
                "id": str(uuid.uuid4()),
                "title": ge.get('summary', 'Google Event'),
                "description": ge.get('description', ''),
                "date": date_str,
                "time": time_str,
                "color": "#4285F4",
                "family_id": user["family_id"],
                "created_by": user["user_id"],
                "google_event_id": ge['id'],
            }
            await db.calendar_events.insert_one(new_event)
            imported += 1
    except Exception as e:
        logger.error(f"Failed to import Google events: {e}")

    return {"message": f"Synced! {pushed} pushed to Google, {imported} imported from Google.", "pushed": pushed, "imported": imported}


@router.delete("/google/disconnect")
async def disconnect_google_calendar(user: dict = Depends(get_current_user)):
    await db.users.update_one({"id": user["user_id"]}, {"$set": {"google_tokens": None}})
    return {"message": "Google Calendar disconnected"}
