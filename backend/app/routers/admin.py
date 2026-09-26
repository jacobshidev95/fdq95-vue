"""Admin user management API."""

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
import os
from pathlib import Path
from fastapi import HTTPException
from sqlalchemy import select, desc, or_

import uuid
from datetime import datetime, timezone
from pathlib import Path
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select, desc
from sqlalchemy.ext.asyncio import AsyncSession
from app.auth import current_active_user
from app.database import get_async_session
from app.models import User, Video, Article, ServiceCategory

router = APIRouter()

ADMIN_LEVELS = {
    ProviderLevel.SYSTEM_ADMIN,
    ProviderLevel.NATIONAL_ADMIN,
    ProviderLevel.REGIONAL_ADMIN,
}


# ★ 客户等级映射（与 auth.py 保持一致）
_CUSTOMER_LEVEL_MAP = {
    None: 0,
    ProviderLevel.SYSTEM_ADMIN: 9,
    ProviderLevel.NATIONAL_ADMIN: 2,
    ProviderLevel.REGIONAL_ADMIN: 1,
    ProviderLevel.SALES_ADMIN: 3,
    ProviderLevel.PROVIDER: 0,
}


def _level_to_customer_level(level) -> int:
    return _CUSTOMER_LEVEL_MAP.get(level, 0)


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
        return or_(
            User.provider_level.in_(
                [ProviderLevel.NATIONAL_ADMIN, ProviderLevel.REGIONAL_ADMIN]
            ),
            User.role == UserRole.CONSUMER,
        )
    if admin.provider_level == ProviderLevel.NATIONAL_ADMIN:
        return or_(
            (
                (User.provider_level == ProviderLevel.REGIONAL_ADMIN)
                & (User.admin_scope_country == admin.admin_scope_country)
            ),
            (
                (User.role == UserRole.CONSUMER)
                & (User.country == admin.admin_scope_country)
            ),
        )
    if admin.provider_level == ProviderLevel.REGIONAL_ADMIN:
        return or_(
            (
                (User.provider_level == ProviderLevel.REGIONAL_ADMIN)
                & (User.admin_scope_country == admin.admin_scope_country)
                & (User.admin_scope_region == admin.admin_scope_region)
                & (User.id != admin.id)
            ),
            (
                (User.role == UserRole.CONSUMER)
                & (User.country == admin.admin_scope_country)
                & (User.region == admin.admin_scope_region)
            ),
        )
    return User.id == uuid.UUID(int=0)


def can_create_level(admin: User) -> list[ProviderLevel]:
    if admin.provider_level == ProviderLevel.SYSTEM_ADMIN:
        return [ProviderLevel.NATIONAL_ADMIN, ProviderLevel.REGIONAL_ADMIN]
    if admin.provider_level == ProviderLevel.NATIONAL_ADMIN:
        return [ProviderLevel.REGIONAL_ADMIN]
    return []


def _is_consumer(target: User) -> bool:
    if target.role == UserRole.CONSUMER:
        return True
    return target.provider_level is None and target.role is None


def can_manage(admin: User, target: User) -> bool:
    if admin.id == target.id:
        return False

    if admin.provider_level == ProviderLevel.SYSTEM_ADMIN:
        if target.provider_level in (
            ProviderLevel.NATIONAL_ADMIN,
            ProviderLevel.REGIONAL_ADMIN,
        ):
            return True
        return _is_consumer(target)

    if admin.provider_level == ProviderLevel.NATIONAL_ADMIN:
        if target.provider_level == ProviderLevel.REGIONAL_ADMIN:
            return target.admin_scope_country == admin.admin_scope_country
        if _is_consumer(target):
            return target.country == admin.admin_scope_country
        return False

    if admin.provider_level == ProviderLevel.REGIONAL_ADMIN:
        if target.provider_level == ProviderLevel.REGIONAL_ADMIN:
            return (
                target.admin_scope_country == admin.admin_scope_country
                and target.admin_scope_region == admin.admin_scope_region
            )
        if _is_consumer(target):
            return (
                target.country == admin.admin_scope_country
                and target.region == admin.admin_scope_region
            )
        return False

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
    # ★ 新增：客户等级（可选，由后端根据 provider_level 自动决定）
    customer_level: Optional[int] = None


class AdminUserItem(BaseModel):
    id: uuid.UUID
    email: str
    user_id: str
    role: Optional[UserRole] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    provider_level: Optional[ProviderLevel] = None
    admin_scope_country: Optional[str] = None
    admin_scope_region: Optional[str] = None
    country: Optional[str] = None
    region: Optional[str] = None
    is_frozen: bool = False
    is_active: bool = True
    created_at: Optional[datetime] = None
    # ★ 新增：客户等级
    customer_level: int = 0

    class Config:
        from_attributes = True

    @classmethod
    def from_user(cls, u: User) -> "AdminUserItem":
        user_country = getattr(u, "country", None)
        user_region = getattr(u, "region", None)
        return cls(
            id=u.id,
            email=u.email,
            user_id=u.user_id,
            role=u.role,
            first_name=u.first_name,
            last_name=u.last_name,
            provider_level=u.provider_level,
            admin_scope_country=u.admin_scope_country,
            admin_scope_region=u.admin_scope_region,
            country=user_country if user_country is not None
            else u.admin_scope_country,
            region=user_region if user_region is not None
            else u.admin_scope_region,
            is_frozen=u.is_frozen,
            is_active=getattr(u, "is_active", True),
            created_at=u.created_at,
            customer_level=getattr(u, "customer_level", 0) or 0,
        )


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
    return {
        "id": str(admin.id),
        "user_id": admin.user_id,
        "email": admin.email,
        "provider_level": admin.provider_level.value
        if admin.provider_level
        else None,
        "admin_scope_country": admin.admin_scope_country,
        "admin_scope_region": admin.admin_scope_region,
        "customer_level": getattr(admin, "customer_level", 0) or 0,
        "can_create": [lvl.value for lvl in can_create_level(admin)],
        "can_manage_levels": (
            ["level_1", "level_2", "consumer"]
            if admin.provider_level == ProviderLevel.SYSTEM_ADMIN
            else ["level_2", "consumer"]
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
        users=[AdminUserItem.from_user(u) for u in rows],
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

    if await session.scalar(select(User).where(User.user_id == payload.user_id)):
        raise HTTPException(400, "User ID is already taken")
    if await session.scalar(select(User).where(User.email == payload.email)):
        raise HTTPException(400, "Email is already registered")

    # ★ 计算 customer_level（后端权威，忽略前端传值）
    computed_customer_level = _level_to_customer_level(payload.provider_level)

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
        customer_level=computed_customer_level,   # ★ 传入
    )

    new_user = await user_manager.create(user_create, safe=True)

    new_user.admin_scope_country = payload.admin_scope_country
    new_user.admin_scope_region = payload.admin_scope_region
    new_user.managed_by_id = admin.id
    await session.commit()
    await session.refresh(new_user)

    print(
        f"[ADMIN] {admin.user_id} created "
        f"{new_user.provider_level.value} @{new_user.user_id} "
        f"(customer_level={new_user.customer_level})"
    )
    return AdminUserItem.from_user(new_user)


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

# ══════════════════════════════════════════════════════════════
# 用户内容管理
# ══════════════════════════════════════════════════════════════

UPLOADS_ROOT = Path("/app/uploads")


def _safe_delete_upload(url: str) -> bool:
    """删除 /uploads/... 对应的物理文件。返回是否删除成功。"""
    if not url or not url.startswith("/uploads/"):
        return False
    rel = url.replace("/uploads/", "", 1)
    path = UPLOADS_ROOT / rel
    try:
        # 防目录穿越
        path = path.resolve()
        if not str(path).startswith(str(UPLOADS_ROOT.resolve())):
            return False
        if path.exists() and path.is_file():
            path.unlink()
            return True
    except Exception as e:
        print(f"[admin] delete file failed: {url} → {e}")
    return False


UPLOADS_ROOT = Path("/app/uploads")


@router.get("/users/{user_id}/content")
async def list_user_content(
    user_id: uuid.UUID,
    me: User = Depends(current_active_user),
    session: AsyncSession = Depends(get_async_session),
):
    """列出某用户的全部内容：文本、普通视频、Live、Activity + 磁盘孤儿文件。"""
    target = await session.scalar(select(User).where(User.id == user_id))
    if not target:
        raise HTTPException(status_code=404, detail="User not found")

    # ---- 文章 ----
    articles = (
        await session.execute(
            select(Article)
            .where(Article.user_id == user_id)
            .order_by(desc(Article.created_at))
        )
    ).scalars().all()

    # ---- 视频 ----
    videos = (
        await session.execute(
            select(Video)
            .where(Video.user_id == user_id)
            .order_by(desc(Video.created_at))
        )
    ).scalars().all()

    def video_dict(v: Video) -> dict:
        cat = v.category.value if v.category else None
        return {
            "id": str(v.id),
            "title": v.title,
            "url": v.url,
            "thumbnail_url": v.thumbnail_url,
            "category": cat,
            "duration_sec": v.duration_sec or 0,
            "file_size": v.file_size or 0,
            "views": v.views or 0,
            "likes": v.likes or 0,
            "created_at": v.created_at.isoformat() if v.created_at else None,
            "is_orphan": False,
        }

    # ★ 扫描磁盘：找该用户目录下所有未被数据库记录的孤儿文件
    existing_urls = {v.url for v in videos}
    orphan_files: list[dict] = []
    user_dir = UPLOADS_ROOT / "videos" / str(user_id)
    if user_dir.exists() and user_dir.is_dir():
        for f in sorted(user_dir.rglob("*")):
            if not f.is_file():
                continue
            if f.suffix.lower() not in {".mp4", ".webm"}:
                continue
            url = f"/uploads/videos/{user_id}/{f.name}"
            if url in existing_urls:
                continue
            try:
                st = f.stat()
                orphan_files.append({
                    "id": None,
                    "title": f"Orphan: {f.stem[:40]}",
                    "url": url,
                    "thumbnail_url": None,
                    "category": None,
                    "duration_sec": 0,
                    "file_size": st.st_size,
                    "views": 0,
                    "likes": 0,
                    "created_at": datetime.fromtimestamp(
                        st.st_mtime, tz=timezone.utc
                    ).isoformat(),
                    "is_orphan": True,
                })
            except Exception as e:
                print(f"[admin] scan orphan failed: {f} → {e}")

    return {
        "user": {
            "id": str(target.id),
            "user_id": target.user_id,
            "email": target.email,
            "first_name": target.first_name,
            "last_name": target.last_name,
        },
        "articles": [
            {
                "id": str(a.id),
                "title": a.title,
                "category": a.category.value if a.category else None,
                "content_type": a.content_type,
                "file_url": a.file_url,
                "link_url": a.link_url,
                "rich_blocks": a.rich_blocks,
                "created_at": a.created_at.isoformat() if a.created_at else None,
            }
            for a in articles
        ],
        "videos": [video_dict(v) for v in videos if v.category is None],
        "live_videos": [video_dict(v) for v in videos if v.category == ServiceCategory.LIVE],
        "activity_videos": [video_dict(v) for v in videos if v.category == ServiceCategory.ACTIVITY],
        "orphan_files": orphan_files,
    }


@router.delete("/orphans/{user_id}/{filename}")
async def delete_orphan_file(
    user_id: uuid.UUID,
    filename: str,
    me: User = Depends(current_active_user),
):
    """管理员删除磁盘孤儿文件（无 DB 记录）。"""
    if "/" in filename or "\\" in filename or ".." in filename:
        raise HTTPException(status_code=400, detail="Invalid filename")
    path = (UPLOADS_ROOT / "videos" / str(user_id) / filename).resolve()
    try:
        if not str(path).startswith(str(UPLOADS_ROOT.resolve())):
            raise HTTPException(status_code=400, detail="Invalid path")
        if not path.exists() or not path.is_file():
            raise HTTPException(status_code=404, detail="File not found")
        path.unlink()
        return {"ok": True, "deleted": filename}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Delete failed: {e}")


@router.delete("/videos/{video_id}")
async def admin_delete_video(
    video_id: uuid.UUID,
    me: User = Depends(current_active_user),
    session: AsyncSession = Depends(get_async_session),
):
    """管理员删除单个视频记录 + 物理文件。"""
    v = await session.scalar(select(Video).where(Video.id == video_id))
    if not v:
        raise HTTPException(status_code=404, detail="Video not found")

    url = v.url
    await session.delete(v)
    await session.commit()

    _safe_delete_upload(url)

    return {"ok": True, "deleted_id": str(video_id)}


@router.delete("/articles/{article_id}")
async def admin_delete_article(
    article_id: uuid.UUID,
    me: User = Depends(current_active_user),
    session: AsyncSession = Depends(get_async_session),
):
    """管理员删除单篇文章 + 物理文件。"""
    a = await session.scalar(select(Article).where(Article.id == article_id))
    if not a:
        raise HTTPException(status_code=404, detail="Article not found")

    file_url = a.file_url
    await session.delete(a)
    await session.commit()

    if file_url:
        _safe_delete_upload(file_url)

    return {"ok": True, "deleted_id": str(article_id)}