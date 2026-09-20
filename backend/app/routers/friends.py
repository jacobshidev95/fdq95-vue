import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import current_active_user
from app.database import get_async_session
from app.email_service import (
    send_friend_request_email,
    send_friend_accepted_email,
    send_friend_rejected_email,
)
from app.models import (
    Friend,
    FriendRequestInbox,
    FriendRequestOutbox,
    Profile,
    RequestStatus,
    User,
)
from app.schemas import FriendRead, FriendRequestRead

router = APIRouter()


async def _user_by_string(session: AsyncSession, sid: str) -> User:
    u = await session.scalar(select(User).where(User.user_id == sid))
    if not u:
        raise HTTPException(status_code=404, detail="User not found")
    return u


@router.post("/request/{target_string_id}")
async def send_friend_request(
    target_string_id: str,
    me: User = Depends(current_active_user),
    session: AsyncSession = Depends(get_async_session),
) -> dict:
    target = await _user_by_string(session, target_string_id)
    if target.id == me.id:
        raise HTTPException(status_code=400, detail="Cannot add yourself")

    existing_friend = await session.scalar(
        select(Friend).where(
            Friend.user_id == me.id, Friend.friend_id == target.id
        )
    )
    if existing_friend:
        return {"status": "already_friends"}

    existing = await session.scalar(
        select(FriendRequestOutbox).where(
            FriendRequestOutbox.sender_id == me.id,
            FriendRequestOutbox.recipient_id == target.id,
            FriendRequestOutbox.status == RequestStatus.PENDING,
        )
    )
    if existing:
        return {"status": "pending"}

    session.add(
        FriendRequestOutbox(
            sender_id=me.id,
            recipient_id=target.id,
            status=RequestStatus.PENDING,
        )
    )
    session.add(
        FriendRequestInbox(
            sender_id=me.id,
            recipient_id=target.id,
            status=RequestStatus.PENDING,
        )
    )
    await session.commit()

    try:
        ok = await send_friend_request_email(
            to=target.email,
            from_user_id=me.user_id,
            from_user_name=me.first_name or me.user_id,
            target_user_id=target.user_id,
        )
        print(f"[FRIEND] request email to {target.email} -> {ok}")
    except Exception as e:
        print(f"[FRIEND] email failed: {type(e).__name__}: {e}")

    return {"status": "sent"}


# ★★★ 关键新增：三态按钮依赖这个端点
@router.get("/pending/{target_string_id}")
async def check_pending_request(
    target_string_id: str,
    me: User = Depends(current_active_user),
    session: AsyncSession = Depends(get_async_session),
) -> dict:
    target = await _user_by_string(session, target_string_id)

    is_friend = await session.scalar(
        select(Friend).where(
            Friend.user_id == me.id,
            Friend.friend_id == target.id,
        )
    )
    pending = await session.scalar(
        select(FriendRequestOutbox).where(
            FriendRequestOutbox.sender_id == me.id,
            FriendRequestOutbox.recipient_id == target.id,
            FriendRequestOutbox.status == RequestStatus.PENDING,
        )
    )
    return {
        "is_friend": bool(is_friend),
        "has_pending": bool(pending),
    }


@router.get("/check/{target_string_id}")
async def check_friend(
    target_string_id: str,
    me: User = Depends(current_active_user),
    session: AsyncSession = Depends(get_async_session),
) -> dict:
    target = await _user_by_string(session, target_string_id)
    exists = await session.scalar(
        select(Friend).where(
            Friend.user_id == me.id,
            Friend.friend_id == target.id,
        )
    )
    return {"is_friend": bool(exists)}


@router.get("/requests/inbox", response_model=list[FriendRequestRead])
async def list_incoming_requests(
    me: User = Depends(current_active_user),
    session: AsyncSession = Depends(get_async_session),
) -> list[FriendRequestRead]:
    rows = (
        await session.execute(
            select(FriendRequestInbox, User, Profile)
            .join(User, User.id == FriendRequestInbox.sender_id)
            .join(Profile, Profile.user_id == User.id, isouter=True)
            .where(FriendRequestInbox.recipient_id == me.id)
            .order_by(FriendRequestInbox.created_at.desc())
        )
    ).all()
    return [
        FriendRequestRead(
            id=req.id,
            other_id=sender.id,
            other_string_id=sender.user_id,
            other_display_name=(prof.display_name if prof else sender.user_id),
            status=req.status,
            created_at=req.created_at,
        )
        for req, sender, prof in rows
    ]


@router.post("/requests/{request_id}/accept")
async def accept_request(
    request_id: uuid.UUID,
    me: User = Depends(current_active_user),
    session: AsyncSession = Depends(get_async_session),
) -> dict:
    req = await session.scalar(
        select(FriendRequestInbox).where(
            FriendRequestInbox.id == request_id,
            FriendRequestInbox.recipient_id == me.id,
        )
    )
    if not req:
        raise HTTPException(status_code=404, detail="Request not found")
    if req.status != RequestStatus.PENDING:
        raise HTTPException(status_code=400, detail="Already resolved")

    req.status = RequestStatus.ACCEPTED

    out = await session.scalar(
        select(FriendRequestOutbox).where(
            FriendRequestOutbox.sender_id == req.sender_id,
            FriendRequestOutbox.recipient_id == me.id,
        )
    )
    if out:
        out.status = RequestStatus.ACCEPTED

    session.add(Friend(user_id=me.id, friend_id=req.sender_id))
    session.add(Friend(user_id=req.sender_id, friend_id=me.id))
    await session.commit()

    try:
        sender = await session.scalar(
            select(User).where(User.id == req.sender_id)
        )
        if sender:
            ok = await send_friend_accepted_email(
                to=sender.email,
                accepter_user_id=me.user_id,
                accepter_user_name=me.first_name or me.user_id,
            )
            print(f"[FRIEND] accept email to {sender.email} -> {ok}")
    except Exception as e:
        print(f"[FRIEND] accept email failed: {type(e).__name__}: {e}")

    return {"status": "accepted"}


@router.post("/requests/{request_id}/reject")
async def reject_request(
    request_id: uuid.UUID,
    me: User = Depends(current_active_user),
    session: AsyncSession = Depends(get_async_session),
) -> dict:
    req = await session.scalar(
        select(FriendRequestInbox).where(
            FriendRequestInbox.id == request_id,
            FriendRequestInbox.recipient_id == me.id,
        )
    )
    if not req:
        raise HTTPException(status_code=404, detail="Request not found")

    req.status = RequestStatus.REJECTED
    out = await session.scalar(
        select(FriendRequestOutbox).where(
            FriendRequestOutbox.sender_id == req.sender_id,
            FriendRequestOutbox.recipient_id == me.id,
        )
    )
    if out:
        out.status = RequestStatus.REJECTED
    await session.commit()

    try:
        sender = await session.scalar(
            select(User).where(User.id == req.sender_id)
        )
        if sender:
            ok = await send_friend_rejected_email(
                to=sender.email,
                rejecter_user_id=me.user_id,
                rejecter_user_name=me.first_name or me.user_id,
            )
            print(f"[FRIEND] reject email to {sender.email} -> {ok}")
    except Exception as e:
        print(f"[FRIEND] reject email failed: {type(e).__name__}: {e}")

    return {"status": "rejected"}


@router.get("/list", response_model=list[FriendRead])
async def list_friends(
    me: User = Depends(current_active_user),
    session: AsyncSession = Depends(get_async_session),
) -> list[FriendRead]:
    rows = (
        await session.execute(
            select(User, Profile)
            .join(Friend, Friend.friend_id == User.id)
            .join(Profile, Profile.user_id == User.id, isouter=True)
            .where(Friend.user_id == me.id)
            .order_by(Friend.created_at.desc())
        )
    ).all()
    return [
        FriendRead(
            user_id=u.id,
            user_string_id=u.user_id,
            display_name=(p.display_name if p else u.user_id),
            avatar_url=(p.avatar_url if p else None),
        )
        for u, p in rows
    ]