"""定期清理未验证的注册账号。

每 30 分钟扫一次，删除 `is_verified=False 且 created_at < now() - 24h` 的用户。
"""
import asyncio
from datetime import datetime, timedelta, timezone

from sqlalchemy import delete, select

from app.database import async_session_maker
from app.models import User

UNVERIFIED_TTL_HOURS = 24
SCAN_INTERVAL_SECONDS = 30 * 60  # 30 分钟


async def _cleanup_once() -> int:
    cutoff = datetime.now(timezone.utc) - timedelta(hours=UNVERIFIED_TTL_HOURS)
    async with async_session_maker() as session:
        # 找出待删除的 user_id（用于日志）
        stmt = select(User.user_id, User.email, User.created_at).where(
            User.is_verified.is_(False),
            User.created_at < cutoff,
        )
        rows = (await session.execute(stmt)).all()
        if not rows:
            return 0

        # 删除
        await session.execute(
            delete(User).where(
                User.is_verified.is_(False),
                User.created_at < cutoff,
            )
        )
        await session.commit()

        for uid, email, created in rows:
            print(
                f"[cleanup] removed unverified user "
                f"@{uid} <{email}> created={created}"
            )
        print(f"[cleanup] deleted {len(rows)} unverified users")
        return len(rows)


async def cleanup_unverified_loop() -> None:
    """后台常驻任务：每 30 分钟执行一次。"""
    # 启动后先等 60 秒，避免和启动流程抢资源
    await asyncio.sleep(60)
    while True:
        try:
            await _cleanup_once()
        except Exception as e:
            print(f"[cleanup] loop error: {type(e).__name__}: {e}")
        await asyncio.sleep(SCAN_INTERVAL_SECONDS)