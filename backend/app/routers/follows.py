import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import current_active_user
from app.database import get_async_session
from app.models import Follow, Follower, Profile, User
from app.schemas import ProfileRead

router = APIRouter()


async def _user_by_string(session: AsyncSession, sid: str) -> User:
    u = await session.scalar(select(User).where(User.user_id == sid))
    if not u:
        raise HTTPException(status_code=404, detail="User not found")
    return u


@router.post("/follow/{target_string_id}")
async def follow_user(
    target_string_id: str,
    me: User = Depends(current_active_user),
    session: AsyncSession = Depends(get_async_session),
) -> dict:
    target = await _user_by_string(session, target_string_id)
    if target.id == me.id:
        raise HTTPException(status_code=400, detail="Cannot follow yourself")

    exists = await session.scalar(
        select(Follow).where(
            Follow.follower_id == me.id,
            Follow.following_id == target.id,
        )
    )
    if exists:
        return {"following": True, "changed": False}

    session.add(Follow(follower_id=me.id, following_id=target.id))
    session.add(Follower(user_id=target.id, follower_id=me.id))
    await session.commit()
    return {"following": True, "changed": True}


@router.delete("/follow/{target_string_id}")
async def unfollow_user(
    target_string_id: str,
    me: User = Depends(current_active_user),
    session: AsyncSession = Depends(get_async_session),
) -> dict:
    target = await _user_by_string(session, target_string_id)
    await session.execute(
        delete(Follow).where(
            Follow.follower_id == me.id,
            Follow.following_id == target.id,
        )
    )
    await session.execute(
        delete(Follower).where(
            Follower.user_id == target.id,
            Follower.follower_id == me.id,
        )
    )
    await session.commit()
    return {"following": False, "changed": True}


@router.get("/follow/{target_string_id}/status")
async def follow_status(
    target_string_id: str,
    me: User = Depends(current_active_user),
    session: AsyncSession = Depends(get_async_session),
) -> dict:
    target = await _user_by_string(session, target_string_id)
    exists = await session.scalar(
        select(Follow).where(
            Follow.follower_id == me.id,
            Follow.following_id == target.id,
        )
    )
    return {"following": bool(exists)}