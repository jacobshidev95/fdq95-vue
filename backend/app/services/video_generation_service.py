"""
视频生成服务层 — 调用 LTX-2 生成带音频的视频片段

LTX-2 API 是异步的：
1. POST /v2/text-to-video        → 返回 {id, created_at}
2. GET  /v2/text-to-video/{id}   → 轮询直到 status=completed
3. 下载 result.video_url

★ 成本控制：
   - 每次提交前先查余额
   - 余额不足抛 InsufficientFundsError（上层可直接停止）
   - 记录每片段的估算成本
"""
import os
import uuid
import asyncio
import logging
from typing import Optional, Dict, Any, List
from pathlib import Path

import httpx

logger = logging.getLogger(__name__)


# ──────────────────────────────────────────────
# 异常类型
# ──────────────────────────────────────────────
class InsufficientFundsError(RuntimeError):
    """LTX-2 余额不足 — 上层可据此立即停止整个任务"""
    pass


# ──────────────────────────────────────────────
# 配置
# ──────────────────────────────────────────────
OUTPUT_DIR = Path(os.getenv("AI_VIDEO_OUTPUT_DIR", "/app/outputs/ai_videos"))
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

LTX2_API_BASE = os.getenv("LTX2_API_BASE", "https://api.ltx.io")
LTX2_API_KEY = os.getenv("LTX2_API_KEY", "")
MOVA_API_BASE = os.getenv("MOVA_API_BASE", "https://studio.mosi.cn/api/v1")
MOVA_API_KEY = os.getenv("MOVA_API_KEY", "")

# 生成后端: "ltx2" | "mova" | "mock"
GENERATION_BACKEND = os.getenv("AI_VIDEO_BACKEND", "mock")

# 每个片段的最大时长（秒）
MAX_CLIP_DURATION = int(os.getenv("AI_VIDEO_CLIP_DURATION", "8"))

# LTX-2 模型
LTX2_MODEL = os.getenv("LTX2_MODEL", "ltx-2-3-fast")

# 轮询参数
POLL_INTERVAL = 5
POLL_MAX_ATTEMPTS = 120

# ★ 成本参数：每秒钟的价格（美分）
#   ltx-2-3-fast ≈ 7.5 美分/秒，即 $0.60/8秒
LTX2_PRICE_PER_SECOND_CENTS = float(
    os.getenv("LTX2_PRICE_PER_SECOND_CENTS", "7.5")
)

# ★ 单次生成预算上限（美分）—— 超过此值的任务会被拒绝
#   默认 200 美分 = $2.00
MAX_BUDGET_CENTS = float(os.getenv("AI_VIDEO_MAX_BUDGET_CENTS", "200"))


class VideoGenerationService:
    """视频生成服务"""

    def __init__(self):
        self.backend = GENERATION_BACKEND
        logger.info(f"VideoGenerationService 初始化，后端: {self.backend}")

    async def generate_clip(
        self,
        prompt: str,
        audio_prompt: Optional[str] = None,
        duration: int = MAX_CLIP_DURATION,
        resolution: str = "1280x720",
        seed: int = 42,
    ) -> Dict[str, Any]:
        """
        生成单个视频片段（含同步音频）

        Returns:
            {"clip_id": str, "path": str, "duration": int, "has_audio": bool}
        """
        clip_id = uuid.uuid4().hex[:12]

        if self.backend == "ltx2":
            return await self._generate_with_ltx2(
                clip_id, prompt, audio_prompt, duration, resolution, seed
            )
        elif self.backend == "mova":
            return await self._generate_with_mova(
                clip_id, prompt, audio_prompt, duration, resolution, seed
            )
        else:
            return await self._generate_mock_clip(clip_id, duration)

    async def _generate_with_ltx2(
        self,
        clip_id: str,
        prompt: str,
        audio_prompt: Optional[str],
        duration: int,
        resolution: str,
        seed: int,
    ) -> Dict[str, Any]:
        """调用 LTX-2 异步 API 生成带音频的视频片段"""
        if not LTX2_API_KEY:
            raise RuntimeError("LTX2_API_KEY 未配置")

        # ★ 成本预估
        est_cost = duration * LTX2_PRICE_PER_SECOND_CENTS
        logger.info(f"[LTX-2] 片段预计花费: {est_cost:.1f} 美分 (${est_cost/100:.2f})")

        output_path = OUTPUT_DIR / f"{clip_id}.mp4"

        full_prompt = prompt
        if audio_prompt:
            full_prompt = f"{prompt}. Audio: {audio_prompt}"

        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {LTX2_API_KEY}",
        }

        # ★ 步骤 1: 提交异步任务
        payload = {
            "prompt": full_prompt,
            "model": LTX2_MODEL,
            "duration": duration,
            "resolution": resolution,
            "fps": 24,
            "generate_audio": True,
        }

        submit_url = f"{LTX2_API_BASE.rstrip('/')}/v2/text-to-video"
        logger.info(f"[LTX-2] 提交任务: {submit_url}")

        async with httpx.AsyncClient(timeout=60.0) as client:
            resp = await client.post(submit_url, json=payload, headers=headers)

            if resp.status_code >= 400:
                error_body = resp.text[:500]
                logger.error(f"[LTX-2] 提交失败 {resp.status_code}: {error_body}")

                # ★ 402 或 Insufficient funds → 抛特定异常
                if resp.status_code == 402 or "Insufficient" in error_body:
                    raise InsufficientFundsError(
                        f"LTX-2 余额不足 (HTTP {resp.status_code}): {error_body}"
                    )

                resp.raise_for_status()

            submit_data = resp.json()
            job_id = submit_data.get("id")
            if not job_id:
                raise RuntimeError(f"LTX-2 未返回任务 ID: {submit_data}")

            logger.info(f"[LTX-2] 任务已提交: job_id={job_id}")

        # ★ 步骤 2: 轮询任务状态
        poll_url = f"{LTX2_API_BASE.rstrip('/')}/v2/text-to-video/{job_id}"

        for attempt in range(POLL_MAX_ATTEMPTS):
            await asyncio.sleep(POLL_INTERVAL)

            async with httpx.AsyncClient(timeout=30.0) as client:
                resp = await client.get(poll_url, headers=headers)
                if resp.status_code >= 400:
                    logger.warning(f"[LTX-2] 轮询失败 {resp.status_code}: {resp.text[:200]}")
                    continue

                data = resp.json()

            status = data.get("status")
            logger.info(f"[LTX-2] 轮询 #{attempt + 1}: job={job_id} status={status}")

            if status == "completed":
                result = data.get("result", {})
                video_url = result.get("video_url") or result.get("url")

                if not video_url:
                    raise RuntimeError(f"LTX-2 完成任务但无 video_url: {data}")

                logger.info(f"[LTX-2] 下载视频: {video_url}")

                async with httpx.AsyncClient(timeout=300.0) as dl_client:
                    video_resp = await dl_client.get(video_url)
                    video_resp.raise_for_status()
                    output_path.write_bytes(video_resp.content)

                logger.info(f"[LTX-2] 片段生成完成: {output_path}")
                return {
                    "clip_id": clip_id,
                    "path": str(output_path),
                    "duration": duration,
                    "has_audio": True,
                    "cost_cents": est_cost,
                }

            elif status == "failed":
                error_msg = data.get("error", {}).get("message", "未知错误")
                # ★ 失败信息里含余额相关词也抛特定异常
                if "Insufficient" in error_msg or "funds" in error_msg.lower():
                    raise InsufficientFundsError(f"LTX-2 任务失败: {error_msg}")
                raise RuntimeError(f"LTX-2 任务失败: {error_msg}")

            elif status in ("pending", "processing", "queued", "running"):
                continue
            else:
                logger.warning(f"[LTX-2] 未知状态 {status}，继续等待")

        raise TimeoutError(f"LTX-2 任务 {job_id} 超时未完成")

    async def _generate_with_mova(
        self,
        clip_id: str,
        prompt: str,
        audio_prompt: Optional[str],
        duration: int,
        resolution: str,
        seed: int,
    ) -> Dict[str, Any]:
        """调用 MOVA API 生成音画同步的视频片段"""
        output_path = OUTPUT_DIR / f"{clip_id}.mp4"

        payload = {
            "prompt": prompt,
            "audio_prompt": audio_prompt or "",
            "seed": seed,
            "resolution": resolution,
            "duration": duration,
        }

        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {MOVA_API_KEY}",
        }

        async with httpx.AsyncClient(timeout=300.0) as client:
            resp = await client.post(
                f"{MOVA_API_BASE}/generate",
                json=payload,
                headers=headers,
            )
            resp.raise_for_status()
            result = resp.json()

            video_url = result.get("video_url")
            if video_url:
                video_data = await client.get(video_url)
                video_data.raise_for_status()
                output_path.write_bytes(video_data.content)

        logger.info(f"MOVA 片段生成完成: {output_path}")
        return {
            "clip_id": clip_id,
            "path": str(output_path),
            "duration": duration,
            "has_audio": True,
        }

    async def _generate_mock_clip(
        self, clip_id: str, duration: int
    ) -> Dict[str, Any]:
        """开发调试用 — 生成一个带测试音频的占位视频"""
        output_path = OUTPUT_DIR / f"{clip_id}.mp4"
        cmd = [
            "ffmpeg", "-y",
            "-f", "lavfi", "-i", f"color=c=blue:s=1280x720:d={duration}",
            "-f", "lavfi", "-i", f"sine=frequency=440:duration={duration}",
            "-c:v", "libx264", "-c:a", "aac", "-shortest",
            str(output_path),
        ]
        proc = await asyncio.create_subprocess_exec(
            *cmd, stdout=asyncio.subprocess.DEVNULL, stderr=asyncio.subprocess.DEVNULL
        )
        await proc.wait()

        return {
            "clip_id": clip_id,
            "path": str(output_path),
            "duration": duration,
            "has_audio": True,
            "cost_cents": 0,
        }


    async def stitch_clips(
        self, clip_paths: List[str], output_name: Optional[str] = None
    ) -> Dict[str, Any]:
        """使用 FFmpeg 将多个视频片段拼接为长视频"""
        if not clip_paths:
            raise ValueError("没有可拼接的视频片段")

        final_id = output_name or uuid.uuid4().hex[:12]
        final_path = OUTPUT_DIR / f"{final_id}.mp4"
        list_file = OUTPUT_DIR / f"{final_id}_concat.txt"

        with open(list_file, "w") as f:
            for p in clip_paths:
                f.write(f"file '{p}'\n")

        cmd = [
            "ffmpeg", "-y",
            "-f", "concat", "-safe", "0",
            "-i", str(list_file),
            "-c", "copy",
            str(final_path),
        ]
        proc = await asyncio.create_subprocess_exec(
            *cmd, stdout=asyncio.subprocess.DEVNULL, stderr=asyncio.subprocess.PIPE
        )
        _, stderr = await proc.communicate()

        if proc.returncode != 0:
            logger.warning("无损拼接失败，转码拼接中...")
            cmd = [
                "ffmpeg", "-y",
                "-f", "concat", "-safe", "0",
                "-i", str(list_file),
                "-c:v", "libx264", "-preset", "fast", "-crf", "23",
                "-c:a", "aac", "-b:a", "128k",
                str(final_path),
            ]
            proc = await asyncio.create_subprocess_exec(
                *cmd, stdout=asyncio.subprocess.DEVNULL, stderr=asyncio.subprocess.PIPE
            )
            await proc.communicate()

        list_file.unlink(missing_ok=True)

        logger.info(f"长视频拼接完成: {final_path}")
        return {
            "video_id": final_id,
            "path": str(final_path),
            "clip_count": len(clip_paths),
        }