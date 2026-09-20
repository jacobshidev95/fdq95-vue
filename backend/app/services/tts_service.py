"""
配音服务层 — 集成 VoiceStudio / Edge-TTS 生成旁白音频
"""
import os
import uuid
import asyncio
import logging
from pathlib import Path
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)

OUTPUT_DIR = Path(os.getenv("AI_VIDEO_OUTPUT_DIR", "/app/outputs/ai_videos"))
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# VoiceStudio 本地 API 地址（默认 Docker 内网）
VOICESTUDIO_API_BASE = os.getenv("VOICESTUDIO_API_BASE", "http://voicestudio:8000")
VOICESTUDIO_API_KEY = os.getenv("VOICESTUDIO_API_KEY", "")

# TTS 后端: "voicestudio" | "edge_tts" | "none"
TTS_BACKEND = os.getenv("AI_VIDEO_TTS_BACKEND", "edge_tts")


class TTSService:
    """TTS 配音服务"""

    def __init__(self):
        self.backend = TTS_BACKEND
        logger.info(f"TTSService 初始化，后端: {self.backend}")

    async def generate_speech(
        self,
        text: str,
        voice: str = "zh-CN-XiaoxiaoNeural",
        output_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        生成语音音频

        Returns:
            {"audio_id": str, "path": str, "duration_estimate": float}
        """
        audio_id = output_id or uuid.uuid4().hex[:12]
        output_path = OUTPUT_DIR / f"{audio_id}.mp3"

        if self.backend == "voicestudio":
            return await self._generate_with_voicestudio(text, voice, audio_id, output_path)
        elif self.backend == "edge_tts":
            return await self._generate_with_edge_tts(text, voice, audio_id, output_path)
        else:
            return {"audio_id": audio_id, "path": "", "duration_estimate": 0.0}

    async def _generate_with_voicestudio(
        self, text: str, voice: str, audio_id: str, output_path: Path
    ) -> Dict[str, Any]:
        """调用 VoiceStudio 本地 API 生成语音"""
        import httpx

        headers = {"Content-Type": "application/json"}
        if VOICESTUDIO_API_KEY:
            headers["Authorization"] = f"Bearer {VOICESTUDIO_API_KEY}"

        payload = {
            "text": text,
            "voice": voice,
            "format": "mp3",
        }

        async with httpx.AsyncClient(timeout=120.0) as client:
            resp = await client.post(
                f"{VOICESTUDIO_API_BASE}/api/v1/tts",
                json=payload,
                headers=headers,
            )
            resp.raise_for_status()
            output_path.write_bytes(resp.content)

        logger.info(f"VoiceStudio 语音生成完成: {output_path}")
        return {
            "audio_id": audio_id,
            "path": str(output_path),
            "duration_estimate": len(text) / 15.0,
        }

    async def _generate_with_edge_tts(
        self, text: str, voice: str, audio_id: str, output_path: Path
    ) -> Dict[str, Any]:
        """使用 Edge-TTS 生成语音（免费，无需 API Key）"""
        cmd = [
            "edge-tts",
            "--voice", voice,
            "--text", text,
            "--write-media", str(output_path),
        ]
        proc = await asyncio.create_subprocess_exec(
            *cmd, stdout=asyncio.subprocess.DEVNULL, stderr=asyncio.subprocess.PIPE
        )
        _, stderr = await proc.communicate()

        if proc.returncode != 0:
            logger.error(f"Edge-TTS 失败: {stderr.decode()}")
            raise RuntimeError(f"Edge-TTS 生成失败: {stderr.decode()}")

        logger.info(f"Edge-TTS 语音生成完成: {output_path}")
        return {
            "audio_id": audio_id,
            "path": str(output_path),
            "duration_estimate": len(text) / 15.0,
        }