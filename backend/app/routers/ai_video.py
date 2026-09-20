"""
AI 视频生成 API 路由
"""
import os
import uuid
import json
import time
import asyncio
import logging
import shutil
from pathlib import Path
from typing import Optional, Dict, Any, AsyncGenerator, List

from fastapi import APIRouter, HTTPException, BackgroundTasks
from fastapi.responses import StreamingResponse, FileResponse
from pydantic import BaseModel, Field

from app.services.agent_orchestrator import run_video_pipeline

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/ai-video", tags=["ai-video"])

# 内存中的任务状态存储（生产环境应使用 Redis）
_task_store: Dict[str, Dict[str, Any]] = {}
# 用于 SSE 的事件队列
_event_queues: Dict[str, asyncio.Queue] = {}
# ★ video_id → 该视频的所有临时文件路径（用于 publish 后清理）
_video_temp_files: Dict[str, List[str]] = {}

# AI 视频输出目录（临时工作区，容器重启自动清空）
OUTPUT_DIR = Path(os.getenv("AI_VIDEO_OUTPUT_DIR", "/app/outputs/ai_videos"))
# 正式视频库（named volume 持久化）
UPLOAD_VIDEO_DIR = Path("/app/uploads/videos")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
UPLOAD_VIDEO_DIR.mkdir(parents=True, exist_ok=True)


# ──────────────────────────────────────────────
# 请求 / 响应模型
# ──────────────────────────────────────────────
class GenerateRequest(BaseModel):
    idea: str = Field(..., description="视频创意描述", min_length=10)
    target_duration: int = Field(60, description="目标时长（秒）", ge=10, le=600)
    language: str = Field("zh", description="语言代码")


class GenerateResponse(BaseModel):
    task_id: str
    status: str
    message: str


class TaskStatus(BaseModel):
    task_id: str
    status: str
    progress: float
    current_step: str
    final_video_url: Optional[str] = None
    errors: list = []


class PublishRequest(BaseModel):
    video_id: str
    title: str = "AI Generated Video"


class PublishResponse(BaseModel):
    ok: bool
    video_id: str
    public_url: str
    file_size: int


# ──────────────────────────────────────────────
# 后台任务执行
# ──────────────────────────────────────────────
async def _execute_pipeline(task_id: str, idea: str, target_duration: int):
    """在后台运行视频生成流水线"""
    queue = _event_queues.get(task_id)

    async def emit(event_type: str, data: dict):
        if queue:
            await queue.put({"event": event_type, "data": data})

    _task_store[task_id] = {
        "status": "running",
        "progress": 0.0,
        "current_step": "initialized",
        "final_video_url": None,
        "errors": [],
    }

    try:
        await emit("progress", {"progress": 0.0, "step": "initialized"})

        result = await run_video_pipeline(
            user_idea=idea,
            target_duration=target_duration,
            task_id=task_id,
        )

        final_video_id = result.get("final_video_id")
        final_video_path = result.get("final_video_path")

        _task_store[task_id] = {
            "status": "completed" if final_video_path else "failed",
            "progress": 1.0,
            "current_step": result.get("current_step", "completed"),
            "final_video_url": (
                f"/api/ai-video/video/{final_video_id}"
                if final_video_id
                else None
            ),
            "errors": result.get("errors", []),
        }

        # ★ 记录该视频所有临时文件路径，供 /publish 成功后清理
        if final_video_id:
            temp_files: List[str] = []
            if final_video_path:
                temp_files.append(str(final_video_path))
            for c in result.get("clips", []) or []:
                if c.get("path"):
                    temp_files.append(str(c["path"]))
            dub = OUTPUT_DIR / f"{final_video_id}_dub.mp3"
            if dub.exists():
                temp_files.append(str(dub))
            _video_temp_files[final_video_id] = temp_files
            logger.info(f"[task {task_id}] 记录 {len(temp_files)} 个临时文件")

        await emit("completed", _task_store[task_id])
    except Exception as e:
        logger.error(f"任务 {task_id} 失败: {e}")
        _task_store[task_id] = {
            "status": "failed",
            "progress": 0.0,
            "current_step": "error",
            "final_video_url": None,
            "errors": [str(e)],
        }
        await emit("error", {"message": str(e)})
    finally:
        if queue:
            await queue.put(None)


# ──────────────────────────────────────────────
# API 端点
# ──────────────────────────────────────────────
@router.post("/generate", response_model=GenerateResponse)
async def generate_video(req: GenerateRequest, background_tasks: BackgroundTasks):
    """启动 AI 视频生成任务"""
    task_id = uuid.uuid4().hex[:12]
    _event_queues[task_id] = asyncio.Queue()
    background_tasks.add_task(
        _execute_pipeline, task_id, req.idea, req.target_duration
    )
    return GenerateResponse(
        task_id=task_id,
        status="accepted",
        message="视频生成任务已启动",
    )


@router.get("/status/{task_id}", response_model=TaskStatus)
async def get_task_status(task_id: str):
    """查询任务状态"""
    if task_id not in _task_store:
        raise HTTPException(status_code=404, detail="任务不存在")
    task = _task_store[task_id]
    return TaskStatus(task_id=task_id, **task)


@router.get("/stream/{task_id}")
async def stream_task_progress(task_id: str):
    """SSE 实时推送任务进度"""
    if task_id not in _event_queues:
        raise HTTPException(status_code=404, detail="任务不存在")

    queue = _event_queues[task_id]

    async def event_generator() -> AsyncGenerator[str, None]:
        try:
            while True:
                event = await queue.get()
                if event is None:
                    break
                yield f"event: {event['event']}\ndata: {json.dumps(event['data'], ensure_ascii=False)}\n\n"
        except asyncio.CancelledError:
            pass
        finally:
            _event_queues.pop(task_id, None)

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@router.get("/video/{video_id}")
async def get_generated_video(video_id: str):
    """下载/预览生成的视频（先在临时目录找，再在正式目录找）"""
    video_path = OUTPUT_DIR / f"{video_id}.mp4"
    if not video_path.exists():
        video_path = UPLOAD_VIDEO_DIR / f"{video_id}.mp4"
    if not video_path.exists():
        raise HTTPException(status_code=404, detail="视频不存在")

    return FileResponse(
        str(video_path),
        media_type="video/mp4",
        filename=f"{video_id}.mp4",
    )


# ──────────────────────────────────────────────
# 发布 AI 视频：把临时文件转正到 uploads/videos/，并清理临时文件
# ──────────────────────────────────────────────
@router.post("/publish", response_model=PublishResponse)
async def publish_ai_video(req: PublishRequest):
    """
    把 AI 生成的 mp4 从 outputs/ai_videos/ 复制到 uploads/videos/，
    返回可公开访问的 URL。

    ★ 复制成功后立即清理 outputs/ai_videos/ 中该视频的所有临时文件。
    """
    src = OUTPUT_DIR / f"{req.video_id}.mp4"
    if not src.exists():
        raise HTTPException(status_code=404, detail="AI 视频文件不存在")

    dst = UPLOAD_VIDEO_DIR / f"{req.video_id}.mp4"
    shutil.copyfile(src, dst)

    # 把 TTS 配音 mp3 也复制过去（如果存在）
    dub_src = OUTPUT_DIR / f"{req.video_id}_dub.mp3"
    if dub_src.exists():
        shutil.copyfile(dub_src, UPLOAD_VIDEO_DIR / f"{req.video_id}_dub.mp3")

    public_url = f"/uploads/videos/{req.video_id}.mp4"
    file_size = dst.stat().st_size
    logger.info(f"[publish_ai_video] {src} → {dst} ({file_size} bytes)")

    # ★ 清理临时文件：先删通过映射记录的所有片段和最终产物
    temp_files = _video_temp_files.pop(req.video_id, [])
    for f in temp_files:
        try:
            Path(f).unlink(missing_ok=True)
        except Exception as e:
            logger.warning(f"[publish] 清理临时文件失败 {f}: {e}")

    # ★ 兜底：删除 outputs 里所有以该 video_id 开头的残留文件
    for f in OUTPUT_DIR.glob(f"{req.video_id}*"):
        try:
            f.unlink(missing_ok=True)
        except Exception as e:
            logger.warning(f"[publish] 兜底清理失败 {f}: {e}")

    logger.info(f"[publish] 已清理 video_id={req.video_id} 的所有临时文件")

    return PublishResponse(
        ok=True,
        video_id=req.video_id,
        public_url=public_url,
        file_size=file_size,
    )


# ──────────────────────────────────────────────
# 兜底清理任务：定期清理 outputs/ai_videos 里超过 1 小时的残留文件
# 由 main.py 的 lifespan 启动
# ──────────────────────────────────────────────
async def cleanup_stale_temp_files():
    """
    每 30 分钟扫描一次 outputs/ai_videos，
    删除最后修改时间超过 1 小时的文件（即未被 publish 的残留）。
    """
    MAX_AGE_SECONDS = 3600
    INTERVAL_SECONDS = 1800
    while True:
        try:
            if OUTPUT_DIR.exists():
                now = time.time()
                cleaned = 0
                for f in OUTPUT_DIR.glob("*"):
                    if not f.is_file():
                        continue
                    try:
                        age = now - f.stat().st_mtime
                        if age > MAX_AGE_SECONDS:
                            f.unlink(missing_ok=True)
                            cleaned += 1
                    except Exception as e:
                        logger.warning(f"[cleanup] 无法处理 {f}: {e}")
                if cleaned:
                    logger.info(f"[cleanup] 已删除 {cleaned} 个超过 1 小时的临时文件")
        except Exception as e:
            logger.warning(f"[cleanup] 扫描失败: {e}")
        await asyncio.sleep(INTERVAL_SECONDS)