import secrets
import uuid
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, EmailStr, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import UserManager, current_active_user, get_user_manager
from app.config import settings
from app.database import get_async_session
from app.models import ProviderLevel, User
from app.schemas import (
    AvailabilityCheck,
    AvailabilityResult,
    FaceEnrollRequest,
    FaceLoginRequest,
)

router = APIRouter()

# In production, use Redis for reset tokens
_reset_tokens: dict[str, dict] = {}

ADMIN_LEVELS = (
    ProviderLevel.SYSTEM_ADMIN,
    ProviderLevel.NATIONAL_ADMIN,
    ProviderLevel.REGIONAL_ADMIN,
)


# ------------------------------------------------------------------ availability
@router.post("/check-availability", response_model=AvailabilityResult)
async def check_availability(
    payload: AvailabilityCheck,
    session: AsyncSession = Depends(get_async_session),
) -> AvailabilityResult:
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


# ------------------------------------------------------------------ change email
class ChangeEmailRequest(BaseModel):
    new_email: EmailStr
    password: str = Field(..., min_length=1)


class ChangeEmailResponse(BaseModel):
    ok: bool
    email: str
    is_verified: bool


@router.post("/change-email", response_model=ChangeEmailResponse)
async def change_email(
    payload: ChangeEmailRequest,
    me: User = Depends(current_active_user),
    session: AsyncSession = Depends(get_async_session),
    user_manager: UserManager = Depends(get_user_manager),
) -> ChangeEmailResponse:
    """Change the current admin's email address.

    - Only administrators may call this endpoint
    - Requires password confirmation
    - Rejects if the new email is already in use
    - Resets `is_verified` and sends a fresh verification email
    """
    if me.provider_level not in ADMIN_LEVELS:
        raise HTTPException(403, "Admin access required")

    # 1. Verify password
    from fastapi_users.password import PasswordHelper

    helper = PasswordHelper()
    verified, _ = helper.verify_and_update(payload.password, me.hashed_password)
    if not verified:
        raise HTTPException(400, "Password is incorrect")

    new_email = payload.new_email.strip().lower()

    if new_email == me.email.lower():
        raise HTTPException(
            400, "New email is the same as the current email"
        )

    # 2. Check uniqueness
    existing = await session.scalar(
        select(User).where(User.email == new_email)
    )
    if existing and existing.id != me.id:
        raise HTTPException(400, "Email is already registered")

    # 3. Update
    old_email = me.email
    me.email = new_email
    me.is_verified = False
    await session.commit()
    await session.refresh(me)

    # 4. Send verification email to the new address
    try:
        await user_manager.request_verify(me)
    except Exception as e:  # noqa: BLE001
        print(f"[EMAIL] verify request failed: {e}")

    print(
        f"[AUTH] user {me.user_id} changed email "
        f"from {old_email} to {new_email}"
    )
    return ChangeEmailResponse(
        ok=True, email=me.email, is_verified=me.is_verified
    )


# ------------------------------------------------------------------ password reset
@router.post("/forgot-password")
async def forgot_password(
    payload: dict,
    session: AsyncSession = Depends(get_async_session),
) -> dict:
    email = (payload.get("email") or "").strip().lower()
    if not email:
        raise HTTPException(status_code=400, detail="Email is required")

    user = await session.scalar(select(User).where(User.email == email))
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
    except Exception as e:  # noqa: BLE001
        print(f"[AUTH] reset email failed: {e}")

    return {"ok": True, "detail": "If the email exists, a reset link was sent."}


@router.post("/reset-password")
async def reset_password(
    payload: dict,
    session: AsyncSession = Depends(get_async_session),
) -> dict:
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
    me.face_enrolled = True
    me.face_credential_id = payload.face_credential_id
    await session.commit()
    return {"ok": True, "face_enrolled": True}


@router.post("/face/login")
async def face_login(
    payload: FaceLoginRequest,
    session: AsyncSession = Depends(get_async_session),
) -> dict:
    user = await session.scalar(
        select(User).where(User.face_credential_id == payload.face_credential_id)
    )
    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Face credential not recognised",
        )
    if getattr(user, "is_frozen", False):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is frozen",
        )

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