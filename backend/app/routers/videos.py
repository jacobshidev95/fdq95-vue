import os
import uuid
import asyncio
from pathlib import Path

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import current_active_user
from app.database import async_session_maker, get_async_session
from app.models import ActivityVideo, Follow, Friend, ServiceCategory, User, Video
from app.schemas import ActivityVideoRead, VideoCreate, VideoCreateResponse, VideoRead
from app.services.whisper_service import transcribe_video

router = APIRouter()


async def _user_by_string(session: AsyncSession, sid: str) -> User:
    u = await session.scalar(select(User).where(User.user_id == sid))
    if not u:
        raise HTTPException(status_code=404, detail="User not found")
    return u


# ══════════════════════════════════════════════════════════════
# /feed 必须在 /{video_id} 之前
# ══════════════════════════════════════════════════════════════
@router.get("/feed")
async def feed(
    tab: str = "recommend",
    limit: int = 20,
    me: User = Depends(current_active_user),
    session: AsyncSession = Depends(get_async_session),
) -> dict:
    limit = max(1, min(limit, 50))

    following_ids = set(
        (await session.execute(
            select(Follow.following_id).where(Follow.follower_id == me.id)
        )).scalars().all()
    )
    friend_ids = set(
        (await session.execute(
            select(Friend.friend_id).where(Friend.user_id == me.id)
        )).scalars().all()
    )

    stmt = select(Video)
    if tab == "following":
        if not following_ids:
            return {"videos": []}
        stmt = stmt.where(Video.user_id.in_(following_ids))
    elif tab == "friends":
        if not friend_ids:
            return {"videos": []}
        stmt = stmt.where(Video.user_id.in_(friend_ids))
    elif tab == "live":
        # ★ 只显示录制的 Live 视频
        stmt = stmt.where(Video.category == ServiceCategory.LIVE)
    elif tab == "activity":
        # ★ 只显示录制的 Activity 视频
        stmt = stmt.where(Video.category == ServiceCategory.ACTIVITY)
    elif tab == "recommend":
        # 推荐：排除 live / activity（只显示普通视频）
        stmt = stmt.where(
            Video.category.notin_([ServiceCategory.LIVE, ServiceCategory.ACTIVITY])
        )
    # 其它未知 tab：不过滤，返回全部

    stmt = stmt.order_by(desc(Video.created_at)).limit(limit)
    videos = (await session.execute(stmt)).scalars().all()

    owner_ids = list({v.user_id for v in videos})
    owners: dict = {}
    if owner_ids:
        owners = {
            u.id: u for u in (await session.execute(
                select(User).where(User.id.in_(owner_ids))
            )).scalars().all()
        }

    result = []
    for v in videos:
        owner = owners.get(v.user_id)
        result.append({
            "id": str(v.id),
            "owner_user_id": str(v.user_id),
            "owner_string_id": owner.user_id if owner else "",
            "owner_display_name": (
                (owner.first_name or owner.user_id) if owner else ""
            ),
            "owner_avatar_url": None,
            "video_url": v.url or "",
            "thumbnail_url": v.thumbnail_url,
            "caption": v.title,
            "like_count": v.likes or 0,
            "love_count": getattr(v, "hearts", 0) or 0,
            "comment_count": 0,
            "is_liked": False,
            "is_loved": False,
            "is_following_owner": v.user_id in following_ids,
            "created_at": v.created_at.isoformat() if v.created_at else None,
        })
    return {"videos": result}


# ══════════════════════════════════════════════════════════════
# 视频上传 + 转码
# ══════════════════════════════════════════════════════════════
VIDEO_UPLOAD_DIR = Path("/app/uploads/videos")
VIDEO_UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

MAX_VIDEO_SIZE = 50 * 1024 * 1024
ALLOWED_VIDEO_EXT = {".mp4"}


async def _transcode_to_h264(src: Path, dst: Path) -> bool:
    cmd = [
        "ffmpeg", "-y",
        "-i", str(src),
        "-c:v", "libx264", "-preset", "fast", "-crf", "23",
        "-c:a", "aac", "-b:a", "128k",
        "-movflags", "+faststart",
        str(dst),
    ]
    try:
        proc = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.DEVNULL,
            stderr=asyncio.subprocess.PIPE,
        )
        _, stderr = await proc.communicate()
        if proc.returncode != 0:
            print(f"[TRANSCODE] failed: {stderr.decode(errors='replace')[-500:]}")
            return False
        return True
    except FileNotFoundError:
        print("[TRANSCODE] ffmpeg not found")
        return False
    except Exception as e:
        print(f"[TRANSCODE] error: {type(e).__name__}: {e}")
        return False


@router.post("/upload-video")
async def upload_video_file(
    file: UploadFile = File(...),
    me: User = Depends(current_active_user),
) -> dict:
    ext = os.path.splitext(file.filename or "")[1].lower()
    if ext not in ALLOWED_VIDEO_EXT:
        raise HTTPException(400, "Only MP4 files are allowed")

    content = await file.read()
    if len(content) > MAX_VIDEO_SIZE:
        raise HTTPException(
            413, f"File too large. Max {MAX_VIDEO_SIZE // (1024 * 1024)} MB"
        )

    user_dir = VIDEO_UPLOAD_DIR / str(me.id)
    user_dir.mkdir(parents=True, exist_ok=True)
    base = uuid.uuid4().hex
    fname = f"{base}.mp4"
    dest = user_dir / fname
    dest.write_bytes(content)

    print(f"[VIDEO] {me.user_id} uploaded {len(content)}B → {dest}")

    tmp_out = user_dir / f"{base}.transcoded.mp4"
    ok = await _transcode_to_h264(dest, tmp_out)

    if ok and tmp_out.exists() and tmp_out.stat().st_size > 0:
        final_size = tmp_out.stat().st_size
        dest.unlink()
        tmp_out.rename(dest)
        print(f"[VIDEO] transcoded → {dest} ({final_size}B)")
        return {
            "url": f"/uploads/videos/{me.id}/{fname}",
            "name": file.filename,
            "size": final_size,
        }
    else:
        if tmp_out.exists():
            tmp_out.unlink(missing_ok=True)
        return {
            "url": f"/uploads/videos/{me.id}/{fname}",
            "name": file.filename,
            "size": len(content),
        }


# ══════════════════════════════════════════════════════════════
# 后台任务：ASR 转写
# ══════════════════════════════════════════════════════════════
async def _transcribe_video_task(video_id: uuid.UUID, video_url: str) -> None:
    """后台转写视频字幕（不阻塞请求）。"""
    if not video_url.startswith("/uploads/"):
        return
    rel = video_url.replace("/uploads/", "", 1)
    file_path = Path("/app/uploads") / rel

    if not file_path.exists():
        print(f"[WHISPER] file not found: {file_path}")
        return

    async with async_session_maker() as session:
        v = await session.get(Video, video_id)
        if not v:
            return
        v.subtitle_status = "processing"
        await session.commit()

        try:
            result = await transcribe_video(file_path)
            v = await session.get(Video, video_id)
            if v:
                v.subtitle_status = "done"
                v.subtitle_lang = result["language"]
                v.subtitle_json = {"segments": result["segments"]}
                await session.commit()
                print(
                    f"[WHISPER] {video_id} done: "
                    f"{len(result['segments'])} segments, "
                    f"lang={result['language']}"
                )
        except Exception as e:
            v = await session.get(Video, video_id)
            if v:
                v.subtitle_status = "failed"
                await session.commit()
            print(f"[WHISPER] {video_id} failed: {type(e).__name__}: {e}")


@router.post("", response_model=VideoCreateResponse, status_code=201)
async def create_video(
    payload: VideoCreate,
    me: User = Depends(current_active_user),
    session: AsyncSession = Depends(get_async_session),
) -> VideoCreateResponse:
    try:
        category_enum = ServiceCategory(payload.category)
    except ValueError:
        raise HTTPException(400, f"Invalid category: {payload.category}")

    if payload.content_type not in ("file", "record", "link"):
        raise HTTPException(400, "Invalid content_type")
    if not payload.url.strip():
        raise HTTPException(400, "url is required")

    video = Video(
        user_id=me.id,
        title=payload.title.strip(),
        url=payload.url.strip(),
        duration_sec=payload.duration_sec or 0,
        category=category_enum,
        content_type=payload.content_type,
        file_size=payload.file_size,
        hearts=0, likes=0, views=0,
        subtitle_status="pending",
    )
    session.add(video)
    await session.commit()
    await session.refresh(video)

    print(f"[VIDEO] {me.user_id} published '{video.title}'")

    # ★ 启动后台转写（仅对本地文件）
    if payload.content_type in ("file", "record"):
        asyncio.create_task(_transcribe_video_task(video.id, video.url))

    return VideoCreateResponse.model_validate(video, from_attributes=True)


# ══════════════════════════════════════════════════════════════
# 字幕获取
# ══════════════════════════════════════════════════════════════
@router.get("/{video_id}/subtitles")
async def get_subtitles(
    video_id: uuid.UUID,
    session: AsyncSession = Depends(get_async_session),
) -> dict:
    v = await session.get(Video, video_id)
    if not v:
        raise HTTPException(404, "Video not found")
    return {
        "status": v.subtitle_status or "pending",
        "language": v.subtitle_lang,
        "segments": (v.subtitle_json or {}).get("segments", []),
    }


# ══════════════════════════════════════════════════════════════
# 保留原有端点
# ══════════════════════════════════════════════════════════════
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
            .order_by(desc(Video.created_at))
        )
    ).scalars().all()
    return [VideoRead.model_validate(v) for v in rows]


@router.get("/activity/user/{user_string_id}", response_model=list[ActivityVideoRead])
async def list_activity_videos(
    user_string_id: str,
    session: AsyncSession = Depends(get_async_session),
) -> list[ActivityVideoRead]:
    user = await _user_by_string(session, user_string_id)
    rows = (
        await session.execute(
            select(ActivityVideo)
            .where(ActivityVideo.user_id == user.id)
            .order_by(desc(ActivityVideo.created_at))
        )
    ).scalars().all()
    return [ActivityVideoRead.model_validate(v) for v in rows]


@router.get("/{video_id}", response_model=VideoRead)
async def get_video(
    video_id: uuid.UUID,
    session: AsyncSession = Depends(get_async_session),
) -> VideoRead:
    v = await session.get(Video, video_id)
    if not v:
        raise HTTPException(status_code=404, detail="Video not found")
    v.views = (v.views or 0) + 1
    await session.commit()
    await session.refresh(v)
    return VideoRead.model_validate(v)