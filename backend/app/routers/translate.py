from typing import Dict

import httpx
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.config import settings

router = APIRouter()

LT_LANG_MAP: Dict[str, str] = {
    "en": "en",
    "zh-CN": "zh",
    "es": "es",
    "fr": "fr",
    "de": "de",
    "ja": "ja",
    "ko": "ko",
    "ar": "ar",
}

SEPARATOR = "\n\n<<<>>>\n\n"


class TranslateRequest(BaseModel):
    texts: Dict[str, str]
    target: str
    source: str = "en"


class TranslateResponse(BaseModel):
    translations: Dict[str, str]


def _payload(q: str, source: str, target: str) -> dict:
    p = {"q": q, "source": source, "target": target, "format": "text"}
    if settings.LIBRETRANSLATE_API_KEY:
        p["api_key"] = settings.LIBRETRANSLATE_API_KEY
    return p


async def _post(client: httpx.AsyncClient, payload: dict) -> str:
    resp = await client.post(
        f"{settings.LIBRETRANSLATE_URL.rstrip('/')}/translate",
        json=payload,
    )
    if resp.status_code != 200:
        raise HTTPException(
            status_code=502,
            detail=f"LibreTranslate HTTP {resp.status_code}: {resp.text[:200]}",
        )
    return resp.json().get("translatedText", "")


@router.post("", response_model=TranslateResponse)
async def translate(req: TranslateRequest) -> TranslateResponse:
    if not req.texts:
        return TranslateResponse(translations={})

    if req.target == req.source:
        return TranslateResponse(translations=req.texts)

    lt_target = LT_LANG_MAP.get(req.target, req.target)
    lt_source = LT_LANG_MAP.get(req.source, req.source)

    keys = list(req.texts.keys())
    values = [req.texts[k] for k in keys]
    joined = SEPARATOR.join(values)

    try:
        async with httpx.AsyncClient(timeout=60) as client:
            translated = await _post(
                client, _payload(joined, lt_source, lt_target)
            )
    except HTTPException:
        raise
    except Exception as e:  # noqa: BLE001
        raise HTTPException(status_code=502, detail=f"Translation error: {e}")

    parts = translated.split(SEPARATOR)
    if len(parts) == len(values):
        return TranslateResponse(
            translations={k: parts[i] for i, k in enumerate(keys)}
        )

    # Fallback: translate each value independently
    result: Dict[str, str] = {}
    async with httpx.AsyncClient(timeout=60) as client:
        for k, v in req.texts.items():
            try:
                result[k] = await _post(client, _payload(v, lt_source, lt_target))
            except Exception:  # noqa: BLE001
                result[k] = v
    return TranslateResponse(translations=result)
