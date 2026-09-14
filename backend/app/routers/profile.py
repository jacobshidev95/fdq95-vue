import uuid
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import current_active_user
from app.database import get_async_session
from app.models import Profile, User
from app.schemas import ProfileRead, ProfileUpdate
from app.services.user_template import create_profile_for_user

router = APIRouter()


async def _profile_by_user_id(
    session: AsyncSession, user_string_id: str
) -> tuple[User, Profile]:
    user = await session.scalar(
        select(User).where(User.user_id == user_string_id)
    )
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    profile = await session.scalar(
        select(Profile).where(Profile.user_id == user.id)
    )
    if not profile:
        profile = await create_profile_for_user(session, user)
    return user, profile


def _to_read(user: User, profile: Profile) -> ProfileRead:
    return ProfileRead(
        id=profile.id,
        user_id=profile.user_id,
        user_string_id=user.user_id,
        display_name=profile.display_name,
        avatar_url=profile.avatar_url,
        bio_line_1=profile.bio_line_1,
        bio_line_2=profile.bio_line_2,
        real_verified=profile.real_verified,
        created_at=profile.created_at,
    )


@router.get("/me", response_model=ProfileRead)
async def get_my_profile(
    user: User = Depends(current_active_user),
    session: AsyncSession = Depends(get_async_session),
) -> ProfileRead:
    profile = await session.scalar(
        select(Profile).where(Profile.user_id == user.id)
    )
    if not profile:
        profile = await create_profile_for_user(session, user)
    return _to_read(user, profile)


@router.patch("/me", response_model=ProfileRead)
async def update_my_profile(
    payload: ProfileUpdate,
    user: User = Depends(current_active_user),
    session: AsyncSession = Depends(get_async_session),
) -> ProfileRead:
    profile = await session.scalar(
        select(Profile).where(Profile.user_id == user.id)
    )
    if not profile:
        profile = await create_profile_for_user(session, user)

    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(profile, field, value)

    await session.commit()
    await session.refresh(profile)
    return _to_read(user, profile)


@router.get("/user/{user_string_id}", response_model=ProfileRead)
async def get_user_profile(
    user_string_id: str,
    session: AsyncSession = Depends(get_async_session),
) -> ProfileRead:
    user, profile = await _profile_by_user_id(session, user_string_id)
    return _to_read(user, profile)