"""
Jitsi JWT 签发工具

依赖：pip install PyJWT
环境变量（与 Jitsi 容器 .env 里的 JWT_APP_ID / JWT_APP_SECRET 保持一致）：
  JITSI_JWT_APP_ID
  JITSI_JWT_APP_SECRET
  JITSI_JWT_SUB        (默认 meet.jitsi，对应 Jitsi 的 XMPP_DOMAIN)
"""
import os
import time
from typing import Optional

import jwt  # PyJWT


def _app_id() -> str:
    return os.getenv("JITSI_JWT_APP_ID", "fdq95live")


def _app_secret() -> str:
    secret = os.getenv("JITSI_JWT_APP_SECRET") or os.getenv("JWT_APP_SECRET")
    if not secret:
        raise RuntimeError(
            "JITSI_JWT_APP_SECRET 未配置，无法签发 Jitsi JWT"
        )
    return secret


def _sub() -> str:
    return os.getenv("JITSI_JWT_SUB", "meet.jitsi")


def create_jitsi_token(
    *,
    user_id: str,
    user_name: str,
    user_email: str,
    avatar_url: Optional[str],
    room: str,
    is_moderator: bool,
    ttl_seconds: int = 7200,
) -> str:
    """签发一个 Jitsi JWT，默认 2 小时有效。"""
    now = int(time.time())
    payload = {
        "aud": "jitsi",
        "iss": _app_id(),
        "sub": _sub(),
        "room": room,
        "iat": now,
        "nbf": now - 10,
        "exp": now + ttl_seconds,
        "context": {
            "user": {
                "id": str(user_id),
                "name": user_name or user_id,
                "email": user_email or "",
                "avatar": avatar_url or "",
                "moderator": bool(is_moderator),
            },
            "features": {
                "livestreaming": False,
                "recording": False,
                "outbound-call": False,
                "transcription": False,
            },
        },
    }
    return jwt.encode(payload, _app_secret(), algorithm="HS256")