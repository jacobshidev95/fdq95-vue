"""
直播 API

  POST   /api/live/start                          开播
  POST   /api/live/{room_id}/end                  结束直播
  GET    /api/live/active                         大厅列表
  GET    /api/live/{room_id}                      房间信息
  GET    /api/live/{room_id}/token                Jitsi JWT
  POST   /api/live/{room_id}/invite/{user_id}     邀请好友
  GET    /api/live/{room_id}/invitees             已邀请列表
"""
import os
import uuid
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy import select, desc
from sqlalchemy.ext.asyncio import AsyncSession

# ★ 引入可选用户依赖
from app.auth import current_active_user, current_user
from app.database import get_async_session
from app.models import (
    Friend,
    LiveInvite,
    LiveSession,
    Profile,
    User,
)
from app.services.jitsi_jwt import create_jitsi_token

router = APIRouter()


# ─────────────────────────────────────────────
# Schemas
# ─────────────────────────────────────────────
class LiveStartRequest(BaseModel):
    title: str = Field("", max_length=120)
    category: Optional[str] = None


class LiveSessionRead(BaseModel):
    room_id: str
    host_user_id: str
    host_uuid: uuid.UUID
    host_display_name: str
    host_avatar_url: Optional[str]
    title: str
    category: Optional[str]
    status: str
    started_at: datetime
    ended_at: Optional[datetime]
    viewer_count: int
    is_live: bool


class LiveTokenResponse(BaseModel):
    token: str
    room_id: str
    is_moderator: bool
    server_url: str
    expires_in: int

class LiveReplayRead(BaseModel):
    id: uuid.UUID
    room_id: str
    title: str
    category: Optional[str]
    started_at: datetime
    ended_at: Optional[datetime]
    viewer_count: int
    recorded_video_url: Optional[str]

# ─────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────
async def _get_live_by_room(
    session: AsyncSession, room_id: str
) -> Optional[LiveSession]:
    return await session.scalar(
        select(LiveSession)
        .where(LiveSession.room_id == room_id, LiveSession.status == "live")
        .order_by(desc(LiveSession.started_at))
        .limit(1)
    )


async def _build_read(
    session: AsyncSession, ls: LiveSession
) -> LiveSessionRead:
    host = await session.scalar(select(User).where(User.id == ls.host_user_id))
    prof = await session.scalar(
        select(Profile).where(Profile.user_id == ls.host_user_id)
    )
    if not host:
        raise HTTPException(status_code=500, detail="host not found")
    return LiveSessionRead(
        room_id=ls.room_id,
        host_user_id=host.user_id,
        host_uuid=host.id,
        host_display_name=(prof.display_name if prof else host.user_id) or host.user_id,
        host_avatar_url=(prof.avatar_url if prof else None),
        title=ls.title,
        category=ls.category,
        status=ls.status,
        started_at=ls.started_at,
        ended_at=ls.ended_at,
        viewer_count=ls.viewer_count,
        is_live=(ls.status == "live"),
    )


async def _can_view(session: AsyncSession, me: User, ls: LiveSession) -> bool:
    if me.id == ls.host_user_id:
        return True
    is_friend = await session.scalar(
        select(Friend).where(
            Friend.user_id == ls.host_user_id,
            Friend.friend_id == me.id,
        )
    )
    if is_friend:
        return True
    invite = await session.scalar(
        select(LiveInvite).where(
            LiveInvite.session_id == ls.id,
            LiveInvite.invitee_user_id == me.id,
        )
    )
    return bool(invite)


# ─────────────────────────────────────────────
# Endpoints
# ─────────────────────────────────────────────
@router.post("/start", response_model=LiveSessionRead)
async def start_live(
    body: LiveStartRequest,
    me: User = Depends(current_active_user),
    session: AsyncSession = Depends(get_async_session),
):
    """每人同时只能开一场，重复调用会复用现有直播。"""
    existing = await session.scalar(
        select(LiveSession).where(
            LiveSession.host_user_id == me.id,
            LiveSession.status == "live",
        )
    )
    if existing:
        if body.title:
            existing.title = body.title
        if body.category:
            existing.category = body.category
        await session.commit()
        await session.refresh(existing)
        return await _build_read(session, existing)

    ls = LiveSession(
        host_user_id=me.id,
        room_id=me.user_id,
        title=body.title or "",
        category=body.category,
        status="live",
        viewer_count=0,
    )
    session.add(ls)
    await session.commit()
    await session.refresh(ls)
    return await _build_read(session, ls)


@router.post("/{room_id}/end")
async def end_live(
    room_id: str,
    me: User = Depends(current_active_user),
    session: AsyncSession = Depends(get_async_session),
):
    ls = await _get_live_by_room(session, room_id)
    if not ls:
        raise HTTPException(status_code=404, detail="直播不存在或已结束")
    if ls.host_user_id != me.id:
        raise HTTPException(status_code=403, detail="只有主播可以结束直播")
    ls.status = "ended"
    ls.ended_at = datetime.now(timezone.utc)
    await session.commit()
    return {"ok": True, "status": "ended"}


# ★★★ 修改：可选登录，未登录也能看大厅
@router.get("/active", response_model=list[LiveSessionRead])
async def list_active(
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    me: Optional[User] = Depends(current_user),   # ★ 从 current_active_user 改为 current_user
    session: AsyncSession = Depends(get_async_session),
):
    rows = (
        await session.execute(
            select(LiveSession)
            .where(LiveSession.status == "live")
            .order_by(
                desc(LiveSession.viewer_count),
                desc(LiveSession.started_at),
            )
            .limit(limit)
            .offset(offset)
        )
    ).scalars().all()
    return [await _build_read(session, ls) for ls in rows]


@router.get("/{room_id}", response_model=LiveSessionRead)
async def get_room(
    room_id: str,
    me: User = Depends(current_active_user),
    session: AsyncSession = Depends(get_async_session),
):
    ls = await _get_live_by_room(session, room_id)
    if not ls:
        raise HTTPException(status_code=404, detail="直播不存在或已结束")
    if not await _can_view(session, me, ls):
        raise HTTPException(status_code=403, detail="你没有权限进入该直播间")
    return await _build_read(session, ls)


@router.get("/{room_id}/token", response_model=LiveTokenResponse)
async def get_token(
    room_id: str,
    me: User = Depends(current_active_user),
    session: AsyncSession = Depends(get_async_session),
):
    ls = await _get_live_by_room(session, room_id)
    if not ls:
        raise HTTPException(status_code=404, detail="直播不存在或已结束")
    if not await _can_view(session, me, ls):
        raise HTTPException(status_code=403, detail="你没有权限进入该直播间")

    is_moderator = (me.id == ls.host_user_id)
    if not is_moderator:
        ls.viewer_count = (ls.viewer_count or 0) + 1
        await session.commit()

    prof = await session.scalar(select(Profile).where(Profile.user_id == me.id))
    display_name = (prof.display_name if prof else None) or me.user_id
    avatar_url = prof.avatar_url if prof else None

    token = create_jitsi_token(
        user_id=me.user_id,
        user_name=display_name,
        user_email=me.email,
        avatar_url=avatar_url,
        room=ls.room_id,
        is_moderator=is_moderator,
        ttl_seconds=7200,
    )
    server_url = os.getenv(
        "JITSI_PUBLIC_URL", "https://video-broadcast.fdq95.com"
    )
    return LiveTokenResponse(
        token=token,
        room_id=ls.room_id,
        is_moderator=is_moderator,
        server_url=server_url,
        expires_in=7200,
    )


@router.post("/{room_id}/invite/{invitee_string_id}")
async def invite_friend(
    room_id: str,
    invitee_string_id: str,
    me: User = Depends(current_active_user),
    session: AsyncSession = Depends(get_async_session),
):
    ls = await _get_live_by_room(session, room_id)
    if not ls:
        raise HTTPException(status_code=404, detail="直播不存在或已结束")
    if ls.host_user_id != me.id:
        raise HTTPException(status_code=403, detail="只有主播可以邀请")

    invitee = await session.scalar(
        select(User).where(User.user_id == invitee_string_id)
    )
    if not invitee:
        raise HTTPException(status_code=404, detail="用户不存在")

    existing = await session.scalar(
        select(LiveInvite).where(
            LiveInvite.session_id == ls.id,
            LiveInvite.invitee_user_id == invitee.id,
        )
    )
    if existing:
        return {"ok": True, "status": "already_invited"}

    session.add(
        LiveInvite(
            session_id=ls.id,
            inviter_user_id=me.id,
            invitee_user_id=invitee.id,
        )
    )
    await session.commit()
    return {"ok": True, "status": "invited"}


@router.get("/{room_id}/invitees")
async def list_invitees(
    room_id: str,
    me: User = Depends(current_active_user),
    session: AsyncSession = Depends(get_async_session),
):
    ls = await _get_live_by_room(session, room_id)
    if not ls:
        raise HTTPException(status_code=404, detail="直播不存在或已结束")
    if ls.host_user_id != me.id:
        raise HTTPException(status_code=403, detail="只有主播可以查看")

    rows = (
        await session.execute(
            select(User, Profile)
            .join(LiveInvite, LiveInvite.invitee_user_id == User.id)
            .join(Profile, Profile.user_id == User.id, isouter=True)
            .where(LiveInvite.session_id == ls.id)
        )
    ).all()
    return [
        {
            "user_string_id": u.user_id,
            "display_name": (p.display_name if p else u.user_id),
            "avatar_url": (p.avatar_url if p else None),
        }
        for u, p in rows
    ]


@router.get("/replays/{user_string_id}", response_model=list[LiveReplayRead])
async def list_user_replays(
    user_string_id: str,
    me: User = Depends(current_active_user),
    session: AsyncSession = Depends(get_async_session),
):
    """某用户所有已结束的直播（可选带录制视频 URL）。"""
    host = await session.scalar(
        select(User).where(User.user_id == user_string_id)
    )
    if not host:
        raise HTTPException(status_code=404, detail="User not found")

    rows = (
        await session.execute(
            select(LiveSession)
            .where(
                LiveSession.host_user_id == host.id,
                LiveSession.status == "ended",
            )
            .order_by(desc(LiveSession.ended_at))
            .limit(100)
        )
    ).scalars().all()

    return [
        LiveReplayRead(
            id=ls.id,
            room_id=ls.room_id,
            title=ls.title or "",
            category=ls.category,
            started_at=ls.started_at,
            ended_at=ls.ended_at,
            viewer_count=ls.viewer_count or 0,
            recorded_video_url=getattr(ls, "recorded_video_url", None),
        )
        for ls in rows
    ]