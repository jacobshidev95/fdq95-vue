import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import current_active_user
from app.database import get_async_session
from app.models import (
    MessageInbox,
    MessageOutbox,
    MessageType,
    Profile,
    User,
)
from app.schemas import MessageRead, MessageSend

router = APIRouter()


async def _user_by_string(session: AsyncSession, sid: str) -> User:
    u = await session.scalar(select(User).where(User.user_id == sid))
    if not u:
        raise HTTPException(status_code=404, detail="User not found")
    return u


def _serialize(
    msg: MessageInbox | MessageOutbox,
    sender: User,
    sender_profile: Profile | None,
    read: bool,
) -> MessageRead:
    return MessageRead(
        id=msg.id,
        sender_id=sender.id,
        sender_string_id=sender.user_id,
        sender_display_name=(
            sender_profile.display_name if sender_profile else sender.user_id
        ),
        content=msg.content,
        content_type=msg.content_type,
        media_url=msg.media_url,
        read=read,
        created_at=msg.created_at,
    )


@router.get("/{target_string_id}", response_model=list[MessageRead])
async def get_conversation(
    target_string_id: str,
    me: User = Depends(current_active_user),
    session: AsyncSession = Depends(get_async_session),
) -> list[MessageRead]:
    """Return the full conversation between me and target (chronological)."""
    target = await _user_by_string(session, target_string_id)

    # All messages in both directions
    out_rows = (
        await session.execute(
            select(MessageOutbox, User, Profile)
            .join(User, User.id == MessageOutbox.sender_id)
            .join(Profile, Profile.user_id == User.id, isouter=True)
            .where(
                MessageOutbox.sender_id == me.id,
                MessageOutbox.recipient_id == target.id,
            )
        )
    ).all()

    in_rows = (
        await session.execute(
            select(MessageInbox, User, Profile)
            .join(User, User.id == MessageInbox.sender_id)
            .join(Profile, Profile.user_id == User.id, isouter=True)
            .where(
                MessageInbox.sender_id == target.id,
                MessageInbox.recipient_id == me.id,
            )
        )
    ).all()

    # Mark incoming as read
    changed = False
    for msg, _u, _p in in_rows:
        if not msg.read:
            msg.read = True
            changed = True
    if changed:
        await session.commit()

    items = [
        _serialize(msg, u, p, read=True) for msg, u, p in out_rows
    ] + [
        _serialize(msg, u, p, read=True) for msg, u, p in in_rows
    ]
    items.sort(key=lambda m: m.created_at)
    return items


@router.post("/{target_string_id}", response_model=MessageRead)
async def send_message(
    target_string_id: str,
    payload: MessageSend,
    me: User = Depends(current_active_user),
    session: AsyncSession = Depends(get_async_session),
) -> MessageRead:
    target = await _user_by_string(session, target_string_id)
    if target.id == me.id:
        raise HTTPException(status_code=400, detail="Cannot message yourself")

    # ---- Business rule: until the recipient replies, the visitor can send
    #      at most ONE message. ----
    has_they_replied = await session.scalar(
        select(MessageInbox).where(
            MessageInbox.sender_id == target.id,
            MessageInbox.recipient_id == me.id,
        ).limit(1)
    )
    if not has_they_replied:
        already_sent = await session.scalar(
            select(MessageOutbox).where(
                MessageOutbox.sender_id == me.id,
                MessageOutbox.recipient_id == target.id,
            ).limit(1)
        )
        if already_sent:
            raise HTTPException(
                status_code=403,
                detail="Only one message allowed before the recipient replies.",
            )

    out = MessageOutbox(
        sender_id=me.id,
        recipient_id=target.id,
        content=payload.content,
        content_type=payload.content_type,
        media_url=payload.media_url,
        delivered=True,
    )
    inbox = MessageInbox(
        sender_id=me.id,
        recipient_id=target.id,
        content=payload.content,
        content_type=payload.content_type,
        media_url=payload.media_url,
        read=False,
    )
    session.add(out)
    session.add(inbox)
    await session.commit()
    await session.refresh(out)

    sender_profile = await session.scalar(
        select(Profile).where(Profile.user_id == me.id)
    )
    return _serialize(out, me, sender_profile, read=True)