"""
配音服务层

语言 → 音色的映射只在这里维护（VOICE_MAP）。
加新语言只需在 VOICE_MAP 加一行；未列出的语言回落到英语音色。
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

VOICESTUDIO_API_BASE = os.getenv("VOICESTUDIO_API_BASE", "http://voicestudio:8000")
VOICESTUDIO_API_KEY = os.getenv("VOICESTUDIO_API_KEY", "")

TTS_BACKEND = os.getenv("AI_VIDEO_TTS_BACKEND", "edge_tts")


# ══════════════════════════════════════════════════════════════
# ★ 语言代码 → edge-tts 音色（唯一需要维护的映射）
#   edge-tts 支持 100+ 语言：edge-tts --list-voices
#   加新语言：加一行即可；不加则回落到英语音色
# ══════════════════════════════════════════════════════════════
VOICE_MAP: Dict[str, str] = {
    "en":      "en-US-AriaNeural",
    "en-US":   "en-US-AriaNeural",
    "en-GB":   "en-GB-SoniaNeural",
    "zh":      "zh-CN-XiaoxiaoNeural",
    "zh-CN":   "zh-CN-XiaoxiaoNeural",
    "zh-TW":   "zh-TW-HsiaoChenNeural",
    "es":      "es-ES-ElviraNeural",
    "es-ES":   "es-ES-ElviraNeural",
    "es-MX":   "es-MX-DaliaNeural",
    "fr":      "fr-FR-DeniseNeural",
    "de":      "de-DE-KatjaNeural",
    "ja":      "ja-JP-NanamiNeural",
    "ko":      "ko-KR-SunHiNeural",
    "ar":      "ar-SA-ZariyahNeural",
    # ★ 加语言：在此追加一行
    # "it":    "it-IT-ElsaNeural",
    # "pt":    "pt-BR-FranciscaNeural",
    # "ru":    "ru-RU-SvetlanaNeural",
}

# 兜底音色
FALLBACK_VOICE = "en-US-AriaNeural"


def get_voice(language: str) -> str:
    """语言代码 → edge-tts 音色（未知则回落到英语）"""
    return VOICE_MAP.get(language, FALLBACK_VOICE)


class TTSService:
    """TTS 配音服务（语言无关，音色由 VOICE_MAP 决定）"""

    def __init__(self):
        self.backend = TTS_BACKEND
        logger.info(f"TTSService 初始化，后端: {self.backend}")

    async def generate_speech(
        self,
        text: str,
        language: str = "en",                    # ★ 只传语言代码
        output_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        audio_id = output_id or uuid.uuid4().hex[:12]
        output_path = OUTPUT_DIR / f"{audio_id}.mp3"

        # ★ 唯一一行：语言 → 音色
        voice = get_voice(language)

        if self.backend == "voicestudio":
            return await self._generate_with_voicestudio(
                text, voice, audio_id, output_path
            )
        elif self.backend == "edge_tts":
            return await self._generate_with_edge_tts(
                text, voice, audio_id, output_path
            )
        else:
            return {"audio_id": audio_id, "path": "", "duration_estimate": 0.0}

    async def _generate_with_edge_tts(
        self, text: str, voice: str, audio_id: str, output_path: Path
    ) -> Dict[str, Any]:
        cmd = [
            "edge-tts",
            "--voice", voice,
            "--text", text,
            "--write-media", str(output_path),
        ]
        proc = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.DEVNULL,
            stderr=asyncio.subprocess.PIPE,
        )
        _, stderr = await proc.communicate()
        if proc.returncode != 0:
            raise RuntimeError(f"Edge-TTS 失败: {stderr.decode()}")

        logger.info(f"Edge-TTS 完成: {output_path} (voice={voice})")
        return {
            "audio_id": audio_id,
            "path": str(output_path),
            "duration_estimate": len(text) / 15.0,
        }

    async def _generate_with_voicestudio(
        self, text: str, voice: str, audio_id: str, output_path: Path
    ) -> Dict[str, Any]:
        import httpx

        headers = {"Content-Type": "application/json"}
        if VOICESTUDIO_API_KEY:
            headers["Authorization"] = f"Bearer {VOICESTUDIO_API_KEY}"

        payload = {"text": text, "voice": voice, "format": "mp3"}

        async with httpx.AsyncClient(timeout=120.0) as client:
            resp = await client.post(
                f"{VOICESTUDIO_API_BASE}/api/v1/tts",
                json=payload,
                headers=headers,
            )
            resp.raise_for_status()
            output_path.write_bytes(resp.content)

        logger.info(f"VoiceStudio 完成: {output_path}")
        return {
            "audio_id": audio_id,
            "path": str(output_path),
            "duration_estimate": len(text) / 15.0,
        }