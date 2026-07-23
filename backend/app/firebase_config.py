import os
import logging
import firebase_admin
from firebase_admin import credentials, auth as firebase_auth
from fastapi import HTTPException, Security, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

logger = logging.getLogger("voice_agent")
security = HTTPBearer(auto_error=False)

# Initialize Firebase Admin SDK
_firebase_app = None

def init_firebase():
    global _firebase_app
    if _firebase_app:
        return _firebase_app

    cred_path = os.getenv("FIREBASE_SERVICE_ACCOUNT_PATH", "")
    if cred_path and os.path.exists(cred_path):
        cred = credentials.Certificate(cred_path)
        _firebase_app = firebase_admin.initialize_app(cred)
        logger.info("firebase_admin_initialized", method="service_account_file")
    else:
        # Initialize with default/environment configuration
        project_id = os.getenv("FIREBASE_PROJECT_ID", "ai-voice-agent-app")
        try:
            _firebase_app = firebase_admin.initialize_app(options={"projectId": project_id})
            logger.info("firebase_admin_initialized", method="default_project", project_id=project_id)
        except Exception as e:
            logger.warning("firebase_admin_init_fallback", error=str(e))
            _firebase_app = None

    return _firebase_app

# Initialize on module import
init_firebase()

async def verify_firebase_id_token(credentials: HTTPAuthorizationCredentials = Security(security)) -> dict:
    """FastAPI Dependency to verify Firebase ID Token in Authorization header."""
    if not credentials or not credentials.credentials:
        raise HTTPException(status_code=401, detail="Missing authorization token")

    id_token = credentials.credentials
    try:
        decoded_token = firebase_auth.verify_id_token(id_token)
        return decoded_token
    except Exception as e:
        logger.error("firebase_token_verification_failed", error=str(e))
        raise HTTPException(status_code=401, detail=f"Invalid Firebase Token: {str(e)}")
