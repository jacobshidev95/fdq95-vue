"""Admin user management API.

Roles and permissions:
  level_0  System Administrator (global)
           → create / see / freeze / unfreeze / delete level_1 and level_2

  level_1  National Administrator (scoped to `admin_scope_country`)
           → create level_2 in own country
           → see / freeze / unfreeze / delete level_2 in own country

  level_2  Regional Administrator (scoped to country + region)
           → see / freeze / unfreeze / delete other level_2 in same region
           → CANNOT create anyone
"""

import uuid
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, EmailStr, Field
from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import current_active_user, get_user_manager, UserManager
from app.database import get_async_session
from app.models import ProviderLevel, User, UserRole
from app.schemas import UserCreate

router = APIRouter()

ADMIN_LEVELS = {
    ProviderLevel.SYSTEM_ADMIN,
    ProviderLevel.NATIONAL_ADMIN,
    ProviderLevel.REGIONAL_ADMIN,
}


# ---------------------------------------------------------------- auth dep
async def get_admin_user(user: User = Depends(current_active_user)) -> User:
    if user.provider_level not in ADMIN_LEVELS:
        raise HTTPException(status_code=403, detail="Admin access required")
    if user.is_frozen:
        raise HTTPException(status_code=403, detail="Account is frozen")
    return user


# ---------------------------------------------------------------- permissions
def visible_filter(admin: User):
    """SQLAlchemy filter for users `admin` can *see*."""
    if admin.provider_level == ProviderLevel.SYSTEM_ADMIN:
        return User.provider_level.in_(
            [ProviderLevel.NATIONAL_ADMIN, ProviderLevel.REGIONAL_ADMIN]
        )

    if admin.provider_level == ProviderLevel.NATIONAL_ADMIN:
        return (
            (User.provider_level == ProviderLevel.REGIONAL_ADMIN)
            & (User.admin_scope_country == admin.admin_scope_country)
        )

    if admin.provider_level == ProviderLevel.REGIONAL_ADMIN:
        return (
            (User.provider_level == ProviderLevel.REGIONAL_ADMIN)
            & (User.admin_scope_country == admin.admin_scope_country)
            & (User.admin_scope_region == admin.admin_scope_region)
            & (User.id != admin.id)
        )

    return User.id == uuid.UUID(int=0)  # matches nothing


def can_create_level(admin: User) -> list[ProviderLevel]:
    """Which admin levels `admin` is allowed to create."""
    if admin.provider_level == ProviderLevel.SYSTEM_ADMIN:
        return [ProviderLevel.NATIONAL_ADMIN, ProviderLevel.REGIONAL_ADMIN]
    if admin.provider_level == ProviderLevel.NATIONAL_ADMIN:
        return [ProviderLevel.REGIONAL_ADMIN]
    return []


def can_manage(admin: User, target: User) -> bool:
    """Whether `admin` can freeze / unfreeze / delete `target`."""
    if admin.id == target.id:
        return False

    if admin.provider_level == ProviderLevel.SYSTEM_ADMIN:
        return target.provider_level in (
            ProviderLevel.NATIONAL_ADMIN,
            ProviderLevel.REGIONAL_ADMIN,
        )

    if admin.provider_level == ProviderLevel.NATIONAL_ADMIN:
        return (
            target.provider_level == ProviderLevel.REGIONAL_ADMIN
            and target.admin_scope_country == admin.admin_scope_country
        )

    if admin.provider_level == ProviderLevel.REGIONAL_ADMIN:
        return (
            target.provider_level == ProviderLevel.REGIONAL_ADMIN
            and target.admin_scope_country == admin.admin_scope_country
            and target.admin_scope_region == admin.admin_scope_region
        )

    return False


# ---------------------------------------------------------------- schemas
class AdminCreatePayload(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=8)
    user_id: str = Field(..., min_length=3, max_length=64)
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    provider_level: ProviderLevel
    admin_scope_country: Optional[str] = None
    admin_scope_region: Optional[str] = None


class AdminUserItem(BaseModel):
    id: uuid.UUID
    email: str
    user_id: str
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    provider_level: Optional[ProviderLevel] = None
    admin_scope_country: Optional[str] = None
    admin_scope_region: Optional[str] = None
    is_frozen: bool = False
    is_active: bool = True
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class AdminUserListResponse(BaseModel):
    total: int
    page: int
    page_size: int
    users: list[AdminUserItem]


class AdminActionResponse(BaseModel):
    ok: bool
    detail: str = ""


# ---------------------------------------------------------------- endpoints
@router.get("/me")
async def admin_me(admin: User = Depends(get_admin_user)) -> dict:
    """Return the current admin's profile and capabilities."""
    return {
        "id": str(admin.id),
        "user_id": admin.user_id,
        "email": admin.email,
        "provider_level": admin.provider_level.value
        if admin.provider_level
        else None,
        "admin_scope_country": admin.admin_scope_country,
        "admin_scope_region": admin.admin_scope_region,
        "can_create": [lvl.value for lvl in can_create_level(admin)],
        "can_manage_levels": (
            ["level_1", "level_2"]
            if admin.provider_level == ProviderLevel.SYSTEM_ADMIN
            else ["level_2"]
            if admin.provider_level == ProviderLevel.NATIONAL_ADMIN
            else ["level_2"]
        ),
    }


@router.get("/users", response_model=AdminUserListResponse)
async def list_users(
    q: Optional[str] = Query(None, description="search user_id or email"),
    only_frozen: Optional[bool] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    admin: User = Depends(get_admin_user),
    session: AsyncSession = Depends(get_async_session),
) -> AdminUserListResponse:
    base = visible_filter(admin)
    stmt = select(User).where(base)
    count_stmt = select(func.count(User.id)).where(base)

    if q:
        pattern = f"%{q.strip()}%"
        cond = or_(User.user_id.ilike(pattern), User.email.ilike(pattern))
        stmt = stmt.where(cond)
        count_stmt = count_stmt.where(cond)

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
        users=[AdminUserItem.model_validate(u) for u in rows],
    )


@router.post("/users", response_model=AdminUserItem, status_code=201)
async def create_admin_user(
    payload: AdminCreatePayload,
    admin: User = Depends(get_admin_user),
    session: AsyncSession = Depends(get_async_session),
    user_manager: UserManager = Depends(get_user_manager),
) -> AdminUserItem:
    allowed = can_create_level(admin)
    if payload.provider_level not in allowed:
        raise HTTPException(
            status_code=403,
            detail=f"You cannot create {payload.provider_level.value} accounts",
        )

    # ---- scope enforcement ----
    if payload.provider_level == ProviderLevel.NATIONAL_ADMIN:
        if not payload.admin_scope_country:
            raise HTTPException(400, "admin_scope_country is required")
        payload.admin_scope_region = None

    elif payload.provider_level == ProviderLevel.REGIONAL_ADMIN:
        if admin.provider_level == ProviderLevel.SYSTEM_ADMIN:
            if (
                not payload.admin_scope_country
                or not payload.admin_scope_region
            ):
                raise HTTPException(
                    400,
                    "admin_scope_country and admin_scope_region are required",
                )
        elif admin.provider_level == ProviderLevel.NATIONAL_ADMIN:
            payload.admin_scope_country = admin.admin_scope_country
            if not payload.admin_scope_region:
                raise HTTPException(400, "admin_scope_region is required")

    # ---- uniqueness ----
    if await session.scalar(select(User).where(User.user_id == payload.user_id)):
        raise HTTPException(400, "User ID is already taken")
    if await session.scalar(select(User).where(User.email == payload.email)):
        raise HTTPException(400, "Email is already registered")

    user_create = UserCreate(
        email=payload.email,
        password=payload.password,
        user_id=payload.user_id,
        first_name=payload.first_name,
        last_name=payload.last_name,
        role=UserRole.PROVIDER,
        provider_level=payload.provider_level,
        country=payload.admin_scope_country,
        region=payload.admin_scope_region,
    )

    new_user = await user_manager.create(user_create, safe=True)

    # these columns are not part of UserCreate
    new_user.admin_scope_country = payload.admin_scope_country
    new_user.admin_scope_region = payload.admin_scope_region
    new_user.managed_by_id = admin.id
    await session.commit()
    await session.refresh(new_user)

    print(
        f"[ADMIN] {admin.user_id} created "
        f"{new_user.provider_level.value} @{new_user.user_id}"
    )
    return AdminUserItem.model_validate(new_user)


@router.post("/users/{user_pk}/freeze", response_model=AdminActionResponse)
async def freeze_user(
    user_pk: uuid.UUID,
    admin: User = Depends(get_admin_user),
    session: AsyncSession = Depends(get_async_session),
) -> AdminActionResponse:
    target = await session.scalar(select(User).where(User.id == user_pk))
    if not target:
        raise HTTPException(404, "User not found")
    if not can_manage(admin, target):
        raise HTTPException(403, "Not authorised")
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
        raise HTTPException(404, "User not found")
    if not can_manage(admin, target):
        raise HTTPException(403, "Not authorised")
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
        raise HTTPException(404, "User not found")
    if not can_manage(admin, target):
        raise HTTPException(403, "Not authorised")
    uid = target.user_id
    await session.delete(target)
    await session.commit()
    print(f"[ADMIN] {admin.user_id} deleted {uid}")
    return AdminActionResponse(ok=True, detail="User deleted")