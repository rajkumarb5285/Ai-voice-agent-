from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime

from app.database import get_db
from app.models.schemas import UserCreate, UserLogin, Token, UserResponse
from app.services.auth_service import (
    authenticate_user,
    create_user,
    create_access_token,
    decode_token,
    get_user_by_id,
    get_user_by_email,
    get_user_by_username,
)
from app.utils.logger import logger

router = APIRouter(prefix="/auth", tags=["auth"])
security = HTTPBearer()


@router.post("/register", response_model=Token, status_code=status.HTTP_201_CREATED)
async def register(data: UserCreate, db: AsyncSession = Depends(get_db)):
    existing_email = await get_user_by_email(db, data.email)
    if existing_email:
        raise HTTPException(status_code=400, detail="Email already registered")

    existing_username = await get_user_by_username(db, data.username)
    if existing_username:
        raise HTTPException(status_code=400, detail="Username already taken")

    try:
        user = await create_user(
            db,
            email=data.email,
            username=data.username,
            password=data.password,
            full_name=data.full_name,
        )
    except Exception as err:
        await db.rollback()
        logger.error("registration_failed", error=str(err))
        raise HTTPException(
            status_code=400,
            detail="Could not create user account. Username or email may already be in use.",
        )

    token = create_access_token({"sub": str(user.id)})
    return Token(
        access_token=token,
        user=UserResponse.model_validate(user),
    )



@router.post("/login", response_model=Token)
async def login(data: UserLogin, db: AsyncSession = Depends(get_db)):
    user = await authenticate_user(db, data.email, data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )

    # Update last_seen
    user.last_seen_at = datetime.utcnow()
    await db.commit()

    token = create_access_token({"sub": str(user.id)})
    return Token(
        access_token=token,
        user=UserResponse.model_validate(user),
    )


@router.get("/me", response_model=UserResponse)
async def get_me(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db),
):
    token_data = decode_token(credentials.credentials)
    if not token_data:
        raise HTTPException(status_code=401, detail="Invalid token")

    user = await get_user_by_id(db, token_data.user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    return UserResponse.model_validate(user)


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db),
):
    """Dependency: extract and validate current user from JWT."""
    token_data = decode_token(credentials.credentials)
    if not token_data:
        raise HTTPException(status_code=401, detail="Invalid or expired token")

    user = await get_user_by_id(db, token_data.user_id)
    if not user or not user.is_active:
        raise HTTPException(status_code=401, detail="User not found or inactive")

    return user


class FirebaseLoginPayload(pydantic_schema_base_model if 'pydantic_schema_base_model' in globals() else object):
    id_token: str

@router.post("/firebase-login", response_model=Token)
async def firebase_login(data: dict, db: AsyncSession = Depends(get_db)):
    id_token = data.get("id_token")
    if not id_token:
        raise HTTPException(status_code=400, detail="Missing id_token")

    try:
        from app.firebase_config import verify_firebase_id_token
        from fastapi.security import HTTPAuthorizationCredentials
        decoded = await verify_firebase_id_token(HTTPAuthorizationCredentials(scheme="Bearer", credentials=id_token))
        email = decoded.get("email") or f"{decoded.get('uid')}@firebase.user"
        username = decoded.get("name") or decoded.get("uid") or email.split("@")[0]

        user = await get_user_by_email(db, email)
        if not user:
            user = await create_user(db, email=email, username=username[:20], password=id_token[:16], full_name=decoded.get("name", "Firebase User"))
        
        token = create_access_token({"sub": str(user.id)})
        return Token(access_token=token, token_type="bearer", user=UserResponse.model_validate(user))
    except Exception as e:
        logger.error("firebase_login_error", error=str(e))
        raise HTTPException(status_code=401, detail=f"Firebase login failed: {str(e)}")

