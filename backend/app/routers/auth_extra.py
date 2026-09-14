import secrets
import uuid
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi_users.jwt import decode_jwt, generate_jwt
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import current_active_user
from app.config import settings
from app.database import get_async_session
from app.models import User
from app.schemas import (
    AvailabilityCheck,
    AvailabilityResult,
    FaceEnrollRequest,
    FaceLoginRequest,
)

router = APIRouter()

# In production, use Redis for reset tokens
_reset_tokens: dict[str, dict] = {}


# ------------------------------------------------------------------ availability
@router.post("/check-availability", response_model=AvailabilityResult)
async def check_availability(
    payload: AvailabilityCheck,
    session: AsyncSession = Depends(get_async_session),
) -> AvailabilityResult:
    """Check if a user_id and/or email is already taken."""
    result = AvailabilityResult()

    if payload.user_id:
        existing = await session.scalar(
            select(User).where(User.user_id == payload.user_id)
        )
        if existing:
            result.user_id_taken = True

    if payload.email:
        existing = await session.scalar(
            select(User).where(User.email == payload.email)
        )
        if existing:
            result.email_taken = True

    result.available = not (result.user_id_taken or result.email_taken)
    return result


# ------------------------------------------------------------------ password reset
@router.post("/forgot-password")
async def forgot_password(
    payload: dict,
    session: AsyncSession = Depends(get_async_session),
) -> dict:
    """Request a password reset link via email."""
    email = (payload.get("email") or "").strip().lower()
    if not email:
        raise HTTPException(status_code=400, detail="Email is required")

    user = await session.scalar(select(User).where(User.email == email))
    # Always return 202 to avoid user enumeration
    if not user or not user.is_active:
        return {"ok": True, "detail": "If the email exists, a reset link was sent."}

    token = secrets.token_urlsafe(32)
    _reset_tokens[token] = {
        "user_id": str(user.id),
        "expires": datetime.now(timezone.utc) + timedelta(hours=1),
    }

    try:
        from app.email_service import send_password_reset_email

        await send_password_reset_email(user.email, token)
    except Exception as e:
        print(f"[AUTH] reset email failed: {e}")

    return {"ok": True, "detail": "If the email exists, a reset link was sent."}


@router.post("/reset-password")
async def reset_password(
    payload: dict,
    session: AsyncSession = Depends(get_async_session),
) -> dict:
    """Reset password using a valid token."""
    token = (payload.get("token") or "").strip()
    new_password = (payload.get("password") or "").strip()

    if not token or not new_password:
        raise HTTPException(status_code=400, detail="Token and password required")
    if len(new_password) < 8:
        raise HTTPException(
            status_code=400, detail="Password must be at least 8 characters"
        )

    entry = _reset_tokens.get(token)
    if not entry:
        raise HTTPException(status_code=400, detail="Invalid or expired token")
    if entry["expires"] < datetime.now(timezone.utc):
        _reset_tokens.pop(token, None)
        raise HTTPException(status_code=400, detail="Token expired")

    user = await session.scalar(
        select(User).where(User.id == uuid.UUID(entry["user_id"]))
    )
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    from fastapi_users.password import PasswordHelper

    helper = PasswordHelper()
    user.hashed_password = helper.hash(new_password)
    await session.commit()

    _reset_tokens.pop(token, None)
    return {"ok": True, "detail": "Password updated successfully"}


# ------------------------------------------------------------------ face recognition
@router.post("/face/enroll")
async def enroll_face(
    payload: FaceEnrollRequest,
    me: User = Depends(current_active_user),
    session: AsyncSession = Depends(get_async_session),
) -> dict:
    """Register a face credential for the current user (optional)."""
    me.face_enrolled = True
    me.face_credential_id = payload.face_credential_id
    await session.commit()
    return {"ok": True, "face_enrolled": True}


@router.post("/face/login")
async def face_login(
    payload: FaceLoginRequest,
    session: AsyncSession = Depends(get_async_session),
) -> dict:
    """Look up a user by their face credential and issue a JWT."""
    user = await session.scalar(
        select(User).where(User.face_credential_id == payload.face_credential_id)
    )
    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Face credential not recognised",
        )

    # Issue a JWT via the existing auth backend
    from app.auth import get_jwt_strategy

    strategy = get_jwt_strategy()
    token = await strategy.write_token(user)
    return {"access_token": token, "token_type": "bearer"}


@router.delete("/face/enroll")
async def disable_face(
    me: User = Depends(current_active_user),
    session: AsyncSession = Depends(get_async_session),
) -> dict:
    me.face_enrolled = False
    me.face_credential_id = None
    await session.commit()
    return {"ok": True, "face_enrolled": False}