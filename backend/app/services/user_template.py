import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Profile, User

DEFAULT_AVATAR = None


async def create_profile_for_user(session: AsyncSession, user: User) -> Profile:
    """Create a Profile row from the user template (idempotent)."""
    existing = await session.scalar(
        select(Profile).where(Profile.user_id == user.id)
    )
    if existing:
        return existing

    display_name = user.real_name or user.user_id
    line1 = f"@{user.user_id}"
    line2_parts = []
    if user.country:
        line2_parts.append(user.country)
    if user.role:
        line2_parts.append(user.role.value.capitalize())
    line2 = " · ".join(line2_parts) or "Welcome to FDQ95"

    profile = Profile(
        id=uuid.uuid4(),
        user_id=user.id,
        display_name=display_name,
        avatar_url=DEFAULT_AVATAR,
        bio_line_1=line1,
        bio_line_2=line2,
        real_verified=False,
    )
    session.add(profile)
    await session.commit()
    await session.refresh(profile)
    return profile