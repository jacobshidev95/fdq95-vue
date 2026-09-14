import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import current_active_user
from app.database import get_async_session
from app.models import ActivityVideo, User, Video
from app.schemas import ActivityVideoRead, VideoRead

router = APIRouter()


async def _user_by_string(session: AsyncSession, sid: str) -> User:
    u = await session.scalar(select(User).where(User.user_id == sid))
    if not u:
        raise HTTPException(status_code=404, detail="User not found")
    return u


@router.get("/user/{user_string_id}", response_model=list[VideoRead])
async def list_user_videos(
    user_string_id: str,
    session: AsyncSession = Depends(get_async_session),
) -> list[VideoRead]:
    user = await _user_by_string(session, user_string_id)
    rows = (
        await session.execute(
            select(Video)
            .where(Video.user_id == user.id)
            .order_by(Video.created_at.desc())
        )
    ).scalars().all()
    return [VideoRead.model_validate(v) for v in rows]


@router.get("/{video_id}", response_model=VideoRead)
async def get_video(
    video_id: uuid.UUID,
    session: AsyncSession = Depends(get_async_session),
) -> VideoRead:
    v = await session.scalar(select(Video).where(Video.id == video_id))
    if not v:
        raise HTTPException(status_code=404, detail="Video not found")

    v.views += 1
    await session.commit()
    await session.refresh(v)
    return VideoRead.model_validate(v)


@router.get(
    "/activity/user/{user_string_id}",
    response_model=list[ActivityVideoRead],
)
async def list_activity_videos(
    user_string_id: str,
    session: AsyncSession = Depends(get_async_session),
) -> list[ActivityVideoRead]:
    user = await _user_by_string(session, user_string_id)
    rows = (
        await session.execute(
            select(ActivityVideo)
            .where(ActivityVideo.user_id == user.id)
            .order_by(ActivityVideo.created_at.desc())
        )
    ).scalars().all()
    return [ActivityVideoRead.model_validate(v) for v in rows]