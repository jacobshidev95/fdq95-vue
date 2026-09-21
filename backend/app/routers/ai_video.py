"""
AI 视频生成 API 路由

★ 成本控制：
   - target_duration 最小 8 秒（最便宜）
   - 每日消费上限（内存计数器，默认 $5/天）
   - 幂等键防重复提交
"""
import os
import uuid
import json
import time
import asyncio
import logging
import shutil
from datetime import date
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
_event_queues: Dict[str, asyncio.Queue] = {}
_video_temp_files: Dict[str, List[str]] = {}

# ★ 幂等缓存: {idempotency_key: task_id}
_idempotency_cache: Dict[str, str] = {}

# ★ 每日消费（美分）: {"2026-09-21": 180.0}
_daily_spend: Dict[str, float] = {}

# ★ 每日消费上限（美分）—— 默认 $5/天
DAILY_LIMIT_CENTS = float(os.getenv("AI_VIDEO_DAILY_LIMIT_CENTS", "500"))

# ★ 每片段秒数
CLIP_DURATION = int(os.getenv("AI_VIDEO_CLIP_DURATION", "8"))

# ★ 每秒钟价格（美分）—— LTX-2.3-fast $0.075/秒
PRICE_PER_SECOND_CENTS = float(
    os.getenv("LTX2_PRICE_PER_SECOND_CENTS", "7.5")
)

# ★ 单次任务上限（美分）—— $2/次
PER_TASK_LIMIT_CENTS = float(
    os.getenv("AI_VIDEO_MAX_BUDGET_CENTS", "200")
)

# AI 视频输出目录
OUTPUT_DIR = Path(os.getenv("AI_VIDEO_OUTPUT_DIR", "/app/outputs/ai_videos"))
UPLOAD_VIDEO_DIR = Path("/app/uploads/videos")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
UPLOAD_VIDEO_DIR.mkdir(parents=True, exist_ok=True)


def _today_spent() -> float:
    today = date.today().isoformat()
    return _daily_spend.get(today, 0.0)


def _add_today_spend(cents: float):
    today = date.today().isoformat()
    _daily_spend[today] = _daily_spend.get(today, 0.0) + cents


# ──────────────────────────────────────────────
# 请求 / 响应模型
# ──────────────────────────────────────────────
class GenerateRequest(BaseModel):
    idea: str = Field(..., description="视频创意描述", min_length=10)
    # ★ 最小值改为 8，上限改为 60（避免一次任务太贵）
    target_duration: int = Field(
        24, description="目标时长（秒）", ge=8, le=60
    )
    language: str = Field("en", description="BCP-47 语言代码")
    # ★ 幂等键（可选）
    idempotency_key: Optional[str] = Field(
        None, description="幂等键（防止重复提交）"
    )


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
    cost_cents: float = 0.0


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
async def _execute_pipeline(task_id: str, idea: str, target_duration: int, language: str):
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
        "cost_cents": 0.0,
    }

    try:
        await emit("progress", {"progress": 0.0, "step": "initialized"})

        result = await run_video_pipeline(
            user_idea=idea,
            target_duration=target_duration,
            task_id=task_id,
            language=language,
        )

        final_video_id = result.get("final_video_id")
        final_video_path = result.get("final_video_path")
        actual_cost = result.get("total_cost_cents", 0.0)

        # ★ 记录今日消费
        _add_today_spend(actual_cost)
        logger.info(
            f"[task {task_id}] 实际花费 {actual_cost:.1f} 美分，"
            f"今日累计 {_today_spent():.1f} 美分"
        )

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
            "cost_cents": actual_cost,
        }

        # 记录临时文件
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

        await emit("completed", _task_store[task_id])
    except Exception as e:
        logger.error(f"任务 {task_id} 失败: {e}")
        _task_store[task_id] = {
            "status": "failed",
            "progress": 0.0,
            "current_step": "error",
            "final_video_url": None,
            "errors": [str(e)],
            "cost_cents": 0.0,
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
    """启动 AI 视频生成任务（带成本检查和幂等）"""

    # ★ 幂等检查
    if req.idempotency_key:
        cached_task_id = _idempotency_cache.get(req.idempotency_key)
        if cached_task_id and cached_task_id in _task_store:
            logger.info(f"[idempotency] 命中: {req.idempotency_key} → {cached_task_id}")
            return GenerateResponse(
                task_id=cached_task_id,
                status="accepted",
                message="任务已存在（幂等命中）",
            )

    # ★ 场景数预算检查
    from app.services.agent_orchestrator import MAX_SCENES, CLIP_DURATION as CLIP_DUR
    num_scenes = max(1, min(req.target_duration // CLIP_DUR, MAX_SCENES))
    est_cost = num_scenes * CLIP_DUR * PRICE_PER_SECOND_CENTS

    # 单次上限
    if est_cost > PER_TASK_LIMIT_CENTS:
        raise HTTPException(
            status_code=429,
            detail=(
                f"预估成本 ${est_cost/100:.2f} 超过单次上限 "
                f"${PER_TASK_LIMIT_CENTS/100:.2f}，请缩短时长。"
            ),
        )

    # 每日上限
    today = _today_spent()
    if today + est_cost > DAILY_LIMIT_CENTS:
        raise HTTPException(
            status_code=429,
            detail=(
                f"今日已消费 ${today/100:.2f}，本次需要 ${est_cost/100:.2f}，"
                f"超过每日上限 ${DAILY_LIMIT_CENTS/100:.2f}。请明天再试。"
            ),
        )

    logger.info(
        f"[cost] 接受任务: {num_scenes} 场景 × {CLIP_DUR}s × "
        f"${PRICE_PER_SECOND_CENTS/100:.4f}/s = ${est_cost/100:.2f} "
        f"(今日已用 ${today/100:.2f})"
    )

    task_id = uuid.uuid4().hex[:12]
    _event_queues[task_id] = asyncio.Queue()

    # ★ 记录幂等键
    if req.idempotency_key:
        _idempotency_cache[req.idempotency_key] = task_id

    background_tasks.add_task(
        _execute_pipeline, task_id, req.idea, req.target_duration, req.language,
    )
    return GenerateResponse(
        task_id=task_id,
        status="accepted",
        message="视频生成任务已启动",
    )


@router.get("/status/{task_id}", response_model=TaskStatus)
async def get_task_status(task_id: str):
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
    connected_at = time.time()

    async def event_generator() -> AsyncGenerator[str, None]:
        try:
            while True:
                event = await queue.get()
                if event is None:
                    logger.info(f"[SSE] 任务结束: task={task_id}")
                    break
                yield f"event: {event['event']}\ndata: {json.dumps(event['data'], ensure_ascii=False)}\n\n"
        except asyncio.CancelledError:
            elapsed = time.time() - connected_at
            logger.warning(f"[SSE] 连接被取消: task={task_id}, 已连接 {elapsed:.1f}s")
            raise
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


@router.post("/publish", response_model=PublishResponse)
async def publish_ai_video(req: PublishRequest):
    src = OUTPUT_DIR / f"{req.video_id}.mp4"
    if not src.exists():
        raise HTTPException(status_code=404, detail="AI 视频文件不存在")

    dst = UPLOAD_VIDEO_DIR / f"{req.video_id}.mp4"
    shutil.copyfile(src, dst)

    dub_src = OUTPUT_DIR / f"{req.video_id}_dub.mp3"
    if dub_src.exists():
        shutil.copyfile(dub_src, UPLOAD_VIDEO_DIR / f"{req.video_id}_dub.mp3")

    public_url = f"/uploads/videos/{req.video_id}.mp4"
    file_size = dst.stat().st_size
    logger.info(f"[publish_ai_video] {src} → {dst} ({file_size} bytes)")

    temp_files = _video_temp_files.pop(req.video_id, [])
    for f in temp_files:
        try:
            Path(f).unlink(missing_ok=True)
        except Exception as e:
            logger.warning(f"[publish] 清理临时文件失败 {f}: {e}")

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

@router.get("/budget")
async def get_budget():
    """查询预算使用情况"""
    return {
        "today_spent_cents": _today_spent(),
        "daily_limit_cents": DAILY_LIMIT_CENTS,
        "per_task_limit_cents": PER_TASK_LIMIT_CENTS,
        "price_per_second_cents": PRICE_PER_SECOND_CENTS,
        "clip_duration_seconds": CLIP_DURATION,
    }


async def cleanup_stale_temp_files():
    """每 30 分钟清理超过 1 小时的临时文件"""
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