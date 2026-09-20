"""Whisper ASR service: transcribe video/audio to subtitles.

Uses faster-whisper (CTranslate2 backend) for fast CPU inference with int8.
Model is lazy-loaded on first use and cached in-process.
"""

import asyncio
import os
from pathlib import Path
from typing import Any

# 全局模型单例（lazy load）
_model: Any = None
_load_lock = asyncio.Lock()


def _get_model():
    """Lazy load the Whisper model. Size controlled by env var WHISPER_MODEL."""
    global _model
    if _model is not None:
        return _model

    from faster_whisper import WhisperModel

    size = os.getenv("WHISPER_MODEL", "base")  # tiny / base / small / medium
    print(f"[WHISPER] loading model '{size}' (this may take ~30s first time)")

    _model = WhisperModel(
        size,
        device="cpu",
        compute_type="int8",   # 8-bit 量化：CPU 上更快、更省内存
        download_root=os.getenv("WHISPER_CACHE", "/root/.cache/huggingface"),
    )
    print(f"[WHISPER] model '{size}' loaded")
    return _model


async def transcribe_video(
    video_path: Path,
    language: str | None = None,
) -> dict:
    """Transcribe a video file (extract audio via ffmpeg internally).

    Returns:
        {
          "language": "zh",
          "language_probability": 0.98,
          "segments": [{"start": 0.5, "end": 3.2, "text": "..."}, ...]
        }
    """
    def _run() -> dict:
        model = _get_model()
        segments, info = model.transcribe(
            str(video_path),
            language=language,     # None → 自动检测
            beam_size=5,
            vad_filter=True,       # 去除静音段
            vad_parameters={"min_silence_duration_ms": 500},
        )
        result_segments = [
            {
                "start": round(float(s.start), 2),
                "end": round(float(s.end), 2),
                "text": (s.text or "").strip(),
            }
            for s in segments
        ]
        return {
            "language": info.language,
            "language_probability": round(float(info.language_probability), 3),
            "segments": result_segments,
        }

    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, _run)