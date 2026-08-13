from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from typing import Optional, Dict, Any

from app.realtime_db import (
    save_user_auth_realtime,
    get_user_auth_realtime,
    update_user_presence,
    save_realtime_session,
    get_realtime_session,
    push_realtime_event,
)

router = APIRouter(prefix="/realtime", tags=["realtime"])

class SyncAuthRequest(BaseModel):
    uid: str
    email: str
    display_name: Optional[str] = ""
    photo_url: Optional[str] = ""
    status: Optional[str] = "online"
    extra: Optional[Dict[str, Any]] = None

class PresenceRequest(BaseModel):
    uid: str
    status: str

class SessionRequest(BaseModel):
    session_id: str
    data: Dict[str, Any]

class EventRequest(BaseModel):
    channel: str
    event_data: Dict[str, Any]


@router.post("/sync-auth")
async def sync_auth(req: SyncAuthRequest):
    """Sync user auth details into Realtime Database."""
    try:
        res = save_user_auth_realtime(
            uid=req.uid,
            email=req.email,
            display_name=req.display_name or "",
            photo_url=req.photo_url or "",
            status=req.status or "online",
            extra=req.extra
        )
        return {"status": "success", "user": res}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/user/{uid}")
async def get_user_realtime(uid: str):
    """Retrieve realtime auth details for a specific user ID."""
    user = get_user_auth_realtime(uid)
    if not user:
        raise HTTPException(status_code=404, detail="User not found in Realtime DB")
    return user


@router.post("/presence")
async def set_presence(req: PresenceRequest):
    """Update user online/offline presence status."""
    updated = update_user_presence(req.uid, req.status)
    return {"status": "success", "updated": updated}


@router.post("/session/{session_id}")
async def save_session(session_id: str, req: SessionRequest):
    """Save or update active voice/chat session data in Realtime DB."""
    res = save_realtime_session(session_id, req.data)
    return {"status": "success", "session": res}


@router.get("/session/{session_id}")
async def get_session(session_id: str):
    """Fetch active session state from Realtime DB."""
    session = get_realtime_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found in Realtime DB")
    return session


@router.post("/events/push")
async def push_event(req: EventRequest):
    """Push a realtime event notification to a channel."""
    res = push_realtime_event(req.channel, req.event_data)
    return {"status": "success", "event": res}
