"""Admin user management.

Access is granted to any user whose `provider_level` is one of:
  level_0 — System Administrator (global)   → manages everyone
  level_1 — National Administrator          → manages users in `admin_scope_country`
  level_2 — Regional Administrator          → manages users in
                                               (`admin_scope_country`, `admin_scope_region`)

The same level hierarchy prevents a lower-level admin from acting on
a peer or superior:
  level_1 can only act on level_2/3/4 users in their country
  level_2 can only act on level_3/4 users in their region
"""

import uuid
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import current_active_user
from app.database import get_async_session
from app.models import Profile, ProviderLevel, User
from app.schemas import AdminActionResponse, AdminUserListResponse, AdminUserRow

router = APIRouter()


ADMIN_LEVELS = {
    ProviderLevel.SYSTEM_ADMIN,
    ProviderLevel.NATIONAL_ADMIN,
    ProviderLevel.REGIONAL_ADMIN,
}


# ---------------------------------------------------------------- helpers
async def get_admin_user(
    user: User = Depends(current_active_user),
) -> User:
    if user.provider_level not in ADMIN_LEVELS:
        raise HTTPException(status_code=403, detail="Admin access required")
    return user


def can_manage(admin: User, target: User) -> bool:
    """Return True if `admin` is allowed to modify `target`."""
    if admin.id == target.id:
        return False

    if admin.provider_level == ProviderLevel.SYSTEM_ADMIN:
        # global admin manages everyone except themselves
        return True

    if admin.provider_level == ProviderLevel.NATIONAL_ADMIN:
        # cannot touch level_0 or level_1
        if target.provider_level in (
            ProviderLevel.SYSTEM_ADMIN,
            ProviderLevel.NATIONAL_ADMIN,
        ):
            return False
        return (
            bool(admin.admin_scope_country)
            and target.country == admin.admin_scope_country
        )

    if admin.provider_level == ProviderLevel.REGIONAL_ADMIN:
        # cannot touch level_0/1/2
        if target.provider_level in (
            ProviderLevel.SYSTEM_ADMIN,
            ProviderLevel.NATIONAL_ADMIN,
            ProviderLevel.REGIONAL_ADMIN,
        ):
            return False
        return (
            bool(admin.admin_scope_country)
            and bool(admin.admin_scope_region)
            and target.country == admin.admin_scope_country
            and target.region == admin.admin_scope_region
        )

    return False


def _visible_filter(admin: User):
    """SQLAlchemy filter matching the set of users `admin` can see."""
    if admin.provider_level == ProviderLevel.SYSTEM_ADMIN:
        return None

    if admin.provider_level == ProviderLevel.NATIONAL_ADMIN:
        return User.country == admin.admin_scope_country

    if admin.provider_level == ProviderLevel.REGIONAL_ADMIN:
        return (
            (User.country == admin.admin_scope_country)
            & (User.region == admin.admin_scope_region)
        )

    return User.id == uuid.UUID(int=0)  # matches nothing


# ---------------------------------------------------------------- endpoints
@router.get("/users", response_model=AdminUserListResponse)
async def list_users(
    q: Optional[str] = Query(None, description="search by user_id or email"),
    only_frozen: Optional[bool] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    admin: User = Depends(get_admin_user),
    session: AsyncSession = Depends(get_async_session),
) -> AdminUserListResponse:
    stmt = select(User)
    count_stmt = select(func.count(User.id))

    visible = _visible_filter(admin)
    if visible is not None:
        stmt = stmt.where(visible)
        count_stmt = count_stmt.where(visible)

    if q:
        pattern = f"%{q.strip()}%"
        search = or_(User.user_id.ilike(pattern), User.email.ilike(pattern))
        stmt = stmt.where(search)
        count_stmt = count_stmt.where(search)

    if only_frozen is True:
        stmt = stmt.where(User.is_frozen.is_(True))
        count_stmt = count_stmt.where(User.is_frozen.is_(True))
    elif only_frozen is False:
        stmt = stmt.where(User.is_frozen.is_(False))
        count_stmt = count_stmt.where(User.is_frozen.is_(False))

    stmt = stmt.order_by(User.created_at.desc().nullslast(), User.id)
    stmt = stmt.offset((page - 1) * page_size).limit(page_size)

    rows = (await session.execute(stmt)).scalars().all()
    total = (await session.execute(count_stmt)).scalar() or 0

    return AdminUserListResponse(
        total=total,
        page=page,
        page_size=page_size,
        users=[AdminUserRow.model_validate(u) for u in rows],
    )


@router.post("/users/{user_pk}/freeze", response_model=AdminActionResponse)
async def freeze_user(
    user_pk: uuid.UUID,
    admin: User = Depends(get_admin_user),
    session: AsyncSession = Depends(get_async_session),
) -> AdminActionResponse:
    target = await session.scalar(select(User).where(User.id == user_pk))
    if not target:
        raise HTTPException(status_code=404, detail="User not found")
    if not can_manage(admin, target):
        raise HTTPException(status_code=403, detail="Not authorised")

    target.is_frozen = True
    await session.commit()
    print(f"[ADMIN] {admin.user_id} froze {target.user_id}")
    return AdminActionResponse(ok=True, detail="User frozen")


@router.post("/users/{user_pk}/unfreeze", response_model=AdminActionResponse)
async def unfreeze_user(
    user_pk: uuid.UUID,
    admin: User = Depends(get_admin_user),
    session: AsyncSession = Depends(get_async_session),
) -> AdminActionResponse:
    target = await session.scalar(select(User).where(User.id == user_pk))
    if not target:
        raise HTTPException(status_code=404, detail="User not found")
    if not can_manage(admin, target):
        raise HTTPException(status_code=403, detail="Not authorised")

    target.is_frozen = False
    await session.commit()
    print(f"[ADMIN] {admin.user_id} unfroze {target.user_id}")
    return AdminActionResponse(ok=True, detail="User unfrozen")


@router.delete("/users/{user_pk}", response_model=AdminActionResponse)
async def delete_user(
    user_pk: uuid.UUID,
    admin: User = Depends(get_admin_user),
    session: AsyncSession = Depends(get_async_session),
) -> AdminActionResponse:
    target = await session.scalar(select(User).where(User.id == user_pk))
    if not target:
        raise HTTPException(status_code=404, detail="User not found")
    if not can_manage(admin, target):
        raise HTTPException(status_code=403, detail="Not authorised")

    deleted_uid = target.user_id
    await session.delete(target)
    await session.commit()
    print(f"[ADMIN] {admin.user_id} deleted {deleted_uid}")
    return AdminActionResponse(ok=True, detail="User deleted")