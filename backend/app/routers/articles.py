"""Articles API."""

import os
import uuid
from pathlib import Path

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import current_active_user
from app.database import get_async_session
from app.models import Article, Profile, ServiceCategory, User
from app.schemas import ArticleCreate, ArticleRead

router = APIRouter()

# ── 上传目录与限制 ──
UPLOAD_DIR = Path("/app/uploads")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

MAX_IMAGE_SIZE = 5 * 1024 * 1024
MAX_VIDEO_SIZE = 50 * 1024 * 1024
MAX_DOC_SIZE = 10 * 1024 * 1024

ALLOWED_IMAGE_EXT = {".jpg", ".jpeg", ".png", ".gif", ".webp"}
ALLOWED_VIDEO_EXT = {".mp4", ".webm", ".mov"}
ALLOWED_DOC_EXT = {".pdf", ".doc", ".docx", ".txt"}


# ══════════════════════════════════════════════════════════════
# ★ /feed 必须定义在 /{article_id} 之前（如果以后加详情端点）
# ══════════════════════════════════════════════════════════════
@router.get("/feed")
async def feed(
    tab: str = "recommend",
    limit: int = 20,
    me: User = Depends(current_active_user),
    session: AsyncSession = Depends(get_async_session),
) -> dict:
    """文章流。

    当前实现：按创建时间倒序返回所有用户的文章。
    后续可扩展 following / friends / activity 过滤。
    """
    limit = max(1, min(limit, 50))

    stmt = select(Article).order_by(desc(Article.created_at)).limit(limit)
    rows = (await session.execute(stmt)).scalars().all()

    # 批量取作者 + profile
    owner_ids = list({a.user_id for a in rows})
    owners: dict = {}
    profiles: dict = {}
    if owner_ids:
        owner_rows = (
            await session.execute(select(User).where(User.id.in_(owner_ids)))
        ).scalars().all()
        owners = {u.id: u for u in owner_rows}

        profile_rows = (
            await session.execute(
                select(Profile).where(Profile.user_id.in_(owner_ids))
            )
        ).scalars().all()
        profiles = {p.user_id: p for p in profile_rows}

    result = []
    for a in rows:
        owner = owners.get(a.user_id)
        prof = profiles.get(a.user_id)

        # 转换 content 为前端的 blocks 格式
        blocks: list[dict] = []
        if a.content_type == "rich" and a.rich_blocks:
            blocks = list(a.rich_blocks)
        elif a.content_type == "file" and a.file_url:
            blocks = [
                {
                    "type": "text",
                    "content": f"📄 {a.file_name or 'attachment'}\n{a.file_url}",
                }
            ]
        elif a.content_type == "link" and a.link_url:
            blocks = [{"type": "text", "content": a.link_url}]

        result.append(
            {
                "id": str(a.id),
                "owner_user_id": str(a.user_id),
                "owner_string_id": owner.user_id if owner else "",
                "owner_display_name": (
                    prof.display_name
                    if prof and prof.display_name
                    else (owner.user_id if owner else "")
                ),
                "owner_avatar_url": prof.avatar_url if prof else None,
                "title": a.title,
                "category": a.category.value if a.category else None,
                "content_type": a.content_type,
                "blocks": blocks,
                "like_count": 0,
                "love_count": 0,
                "comment_count": 0,
                "is_liked": False,
                "is_loved": False,
                "is_following_owner": False,
                "created_at": a.created_at.isoformat() if a.created_at else None,
            }
        )

    return {"articles": result}


# ══════════════════════════════════════════════════════════════
# 上传
# ══════════════════════════════════════════════════════════════
@router.post("/upload")
async def upload_file(
    kind: str = Form(...),
    file: UploadFile = File(...),
    me: User = Depends(current_active_user),
) -> dict:
    """上传文章资源文件，返回永久 URL。"""
    ext = os.path.splitext(file.filename or "")[1].lower()

    if kind == "image":
        allowed, max_size = ALLOWED_IMAGE_EXT, MAX_IMAGE_SIZE
    elif kind == "video":
        allowed, max_size = ALLOWED_VIDEO_EXT, MAX_VIDEO_SIZE
    elif kind == "document":
        allowed, max_size = ALLOWED_DOC_EXT, MAX_DOC_SIZE
    else:
        raise HTTPException(400, "Invalid kind")

    if ext not in allowed:
        raise HTTPException(400, f"File type {ext} not allowed")

    content = await file.read()
    if len(content) > max_size:
        raise HTTPException(
            413, f"File too large. Max {max_size // (1024 * 1024)} MB"
        )

    user_dir = UPLOAD_DIR / str(me.id)
    user_dir.mkdir(parents=True, exist_ok=True)
    fname = f"{uuid.uuid4().hex}{ext}"
    dest = user_dir / fname
    dest.write_bytes(content)

    print(f"[ARTICLE] {me.user_id} uploaded {kind} {len(content)}B → {dest}")

    return {
        "url": f"/uploads/{me.id}/{fname}",
        "name": file.filename,
        "size": len(content),
    }


# ══════════════════════════════════════════════════════════════
# 发表文章
# ══════════════════════════════════════════════════════════════
@router.post("", response_model=ArticleRead, status_code=201)
async def create_article(
    payload: ArticleCreate,
    me: User = Depends(current_active_user),
    session: AsyncSession = Depends(get_async_session),
) -> ArticleRead:
    """发表文章。"""
    try:
        category_enum = ServiceCategory(payload.category)
    except ValueError:
        raise HTTPException(400, f"Invalid category: {payload.category}")

    if payload.content_type == "file" and not payload.file_url:
        raise HTTPException(400, "file_url required for file articles")
    if payload.content_type == "link" and not payload.link_url:
        raise HTTPException(400, "link_url required for link articles")
    if payload.content_type == "rich":
        if not payload.rich_blocks:
            raise HTTPException(400, "rich_blocks required for rich articles")
        has_content = any(
            (b.get("content") or "").strip() for b in payload.rich_blocks
        )
        if not has_content:
            raise HTTPException(400, "rich_blocks is empty")

    article = Article(
        user_id=me.id,
        title=payload.title.strip(),
        category=category_enum,
        content_type=payload.content_type,
        file_url=payload.file_url,
        file_name=payload.file_name,
        file_size=payload.file_size,
        rich_blocks=payload.rich_blocks,
        link_url=payload.link_url,
    )
    session.add(article)
    await session.commit()
    await session.refresh(article)

    print(f"[ARTICLE] {me.user_id} published '{article.title}'")
    return ArticleRead.model_validate(article, from_attributes=True)