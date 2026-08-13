"""
Realtime Database Integration Module (Firebase Realtime DB + Local Memory Fallback)
"""
import time
import logging
from typing import Dict, Any, Optional

logger = logging.getLogger("voice_agent")

# In-memory storage for offline / dev fallback
_local_realtime_store: Dict[str, Dict[str, Any]] = {
    "users": {},
    "sessions": {},
    "events": []
}

def _get_db_ref(path: str):
    """Retrieve Firebase Realtime DB reference if available."""
    try:
        from firebase_admin import db
        return db.reference(path)
    except Exception as e:
        logger.debug("firebase_realtime_db_ref_unavailable", error=str(e))
        return None

def save_user_auth_realtime(
    uid: str,
    email: str,
    display_name: str = "",
    photo_url: str = "",
    status: str = "online",
    extra: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """Store/Update user authentication details in Realtime Database."""
    user_payload = {
        "uid": uid,
        "email": email,
        "displayName": display_name or email.split("@")[0],
        "photoURL": photo_url,
        "status": status,
        "lastLoginAt": int(time.time() * 1000),
        "updatedAt": int(time.time() * 1000),
    }
    if extra:
        user_payload.update(extra)

    # 1. Fallback memory store
    _local_realtime_store["users"][uid] = user_payload

    # 2. Sync to Firebase Realtime DB
    ref = _get_db_ref(f"users/{uid}")
    if ref:
        try:
            ref.update(user_payload)
            logger.info("realtime_user_auth_saved", uid=uid)
        except Exception as err:
            logger.warning("realtime_user_auth_firebase_failed", uid=uid, error=str(err))

    return user_payload

def get_user_auth_realtime(uid: str) -> Optional[Dict[str, Any]]:
    """Fetch user authentication & presence details from Realtime DB."""
    ref = _get_db_ref(f"users/{uid}")
    if ref:
        try:
            data = ref.get()
            if data:
                return data
        except Exception as err:
            logger.warning("realtime_get_user_firebase_failed", uid=uid, error=str(err))
    
    return _local_realtime_store["users"].get(uid)

def update_user_presence(uid: str, status: str = "online") -> bool:
    """Update user presence (online/offline/busy) in Realtime DB."""
    patch = {
        "status": status,
        "lastSeenAt": int(time.time() * 1000)
    }
    if uid in _local_realtime_store["users"]:
        _local_realtime_store["users"][uid].update(patch)

    ref = _get_db_ref(f"users/{uid}")
    if ref:
        try:
            ref.update(patch)
            return True
        except Exception as err:
            logger.warning("realtime_presence_update_failed", uid=uid, error=str(err))
    return True

def save_realtime_session(session_id: str, data: Dict[str, Any]) -> Dict[str, Any]:
    """Store realtime session state (voice streaming, transcriptions, agent activity)."""
    session_payload = {
        "sessionId": session_id,
        "timestamp": int(time.time() * 1000),
        **data
    }
    _local_realtime_store["sessions"][session_id] = session_payload

    ref = _get_db_ref(f"realtime_data/sessions/{session_id}")
    if ref:
        try:
            ref.update(session_payload)
        except Exception as err:
            logger.warning("realtime_session_save_failed", session_id=session_id, error=str(err))

    return session_payload

def get_realtime_session(session_id: str) -> Optional[Dict[str, Any]]:
    """Retrieve realtime session state."""
    ref = _get_db_ref(f"realtime_data/sessions/{session_id}")
    if ref:
        try:
            val = ref.get()
            if val:
                return val
        except Exception as err:
            logger.warning("realtime_get_session_failed", session_id=session_id, error=str(err))

    return _local_realtime_store["sessions"].get(session_id)

def push_realtime_event(channel: str, event_data: Dict[str, Any]) -> Dict[str, Any]:
    """Push realtime event notification."""
    payload = {
        "channel": channel,
        "timestamp": int(time.time() * 1000),
        "data": event_data
    }
    _local_realtime_store["events"].append(payload)
    if len(_local_realtime_store["events"]) > 100:
        _local_realtime_store["events"].pop(0)

    ref = _get_db_ref(f"realtime_data/events/{channel}")
    if ref:
        try:
            ref.push(payload)
        except Exception as err:
            logger.warning("realtime_push_event_failed", channel=channel, error=str(err))

    return payload
