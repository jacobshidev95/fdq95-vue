from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from slowapi.errors import RateLimitExceeded
from sqlalchemy import text
from starlette.exceptions import HTTPException as StarletteHTTPException
import traceback
import asyncio
# 在文件顶部的 import 区域添加
from app.routers import ai_video

from app.auth import auth_backend, fastapi_users
from app.config import settings
from app.database import Base, engine
from app.rate_limit import limiter, _rate_limit_exceeded_handler
from app.routers import (
    activities,
    admin,
    applications,
    articles,
    auth_extra,
    friends,
    follows,
    jobs,
    messages,
    products,
    profile,
    register_guard,
    translate,
    videos,
    ai_video,   # ★ 新增
)
from app.schemas import UserCreate, UserRead, UserUpdate
from pathlib import Path
from fastapi.staticfiles import StaticFiles
import logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)

async def _run_migrations() -> None:
    statements = [
        "ALTER TYPE service_category ADD VALUE IF NOT EXISTS 'health'",
        "ALTER TYPE service_category ADD VALUE IF NOT EXISTS 'tech'",
        "ALTER TYPE service_category ADD VALUE IF NOT EXISTS 'iot'",
        "ALTER TYPE service_category ADD VALUE IF NOT EXISTS 'life'",
        "ALTER TYPE service_category ADD VALUE IF NOT EXISTS 'ai'",
        (
            "DO $$ BEGIN "
            "  CREATE TYPE provider_level AS ENUM "
            "    ('level_0','level_1','level_2','level_3','level_4'); "
            "EXCEPTION WHEN duplicate_object THEN null; END $$;"
        ),
        "ALTER TABLE users ADD COLUMN IF NOT EXISTS provider_level provider_level",
        "ALTER TABLE users ADD COLUMN IF NOT EXISTS managed_by_id UUID",
        "ALTER TABLE users ADD COLUMN IF NOT EXISTS created_at TIMESTAMPTZ DEFAULT now()",
        "ALTER TABLE users ADD COLUMN IF NOT EXISTS first_name VARCHAR(64)",
        "ALTER TABLE users ADD COLUMN IF NOT EXISTS last_name VARCHAR(64)",
        "ALTER TABLE users ADD COLUMN IF NOT EXISTS real_verified BOOLEAN DEFAULT false",
        "ALTER TABLE users ADD COLUMN IF NOT EXISTS face_enrolled BOOLEAN DEFAULT false",
        "ALTER TABLE users ADD COLUMN IF NOT EXISTS face_credential_id VARCHAR(256)",
        "ALTER TABLE users ADD COLUMN IF NOT EXISTS region VARCHAR(64)",
        "ALTER TABLE users ADD COLUMN IF NOT EXISTS is_frozen BOOLEAN DEFAULT false",
        "ALTER TABLE users ADD COLUMN IF NOT EXISTS admin_scope_country VARCHAR(8)",
        "ALTER TABLE users ADD COLUMN IF NOT EXISTS admin_scope_region VARCHAR(64)",
        "ALTER TABLE users ADD COLUMN IF NOT EXISTS customer_level INTEGER DEFAULT 0 NOT NULL",

        # Video 表扩展字段
        "ALTER TABLE videos ADD COLUMN IF NOT EXISTS category service_category",
        "ALTER TABLE videos ADD COLUMN IF NOT EXISTS content_type VARCHAR(16)",
        "ALTER TABLE videos ADD COLUMN IF NOT EXISTS file_size INTEGER",

        # ★★★ 关键修复：确保 videos 的计数列有 NOT NULL + DEFAULT 0
        #     解决 "null value in column hearts violates not-null constraint"
        "ALTER TABLE videos ADD COLUMN IF NOT EXISTS views INTEGER NOT NULL DEFAULT 0",
        "ALTER TABLE videos ADD COLUMN IF NOT EXISTS likes INTEGER NOT NULL DEFAULT 0",
        "ALTER TABLE videos ADD COLUMN IF NOT EXISTS hearts INTEGER NOT NULL DEFAULT 0",
        "ALTER TABLE videos ALTER COLUMN views SET DEFAULT 0",
        "ALTER TABLE videos ALTER COLUMN likes SET DEFAULT 0",
        "ALTER TABLE videos ALTER COLUMN hearts SET DEFAULT 0",
        "UPDATE videos SET views = 0 WHERE views IS NULL",
        "UPDATE videos SET likes = 0 WHERE likes IS NULL",
        "UPDATE videos SET hearts = 0 WHERE hearts IS NULL",
        # ★ 新增：video 字幕字段
        "ALTER TABLE videos ADD COLUMN IF NOT EXISTS subtitle_status VARCHAR(16)",
        "ALTER TABLE videos ADD COLUMN IF NOT EXISTS subtitle_lang VARCHAR(8)",
        "ALTER TABLE videos ADD COLUMN IF NOT EXISTS subtitle_json JSON",

        "CREATE INDEX IF NOT EXISTS ix_users_is_frozen ON users (is_frozen)",
        "CREATE INDEX IF NOT EXISTS ix_users_region ON users (region)",
        "CREATE INDEX IF NOT EXISTS ix_users_admin_scope_country ON users (admin_scope_country)",
        "CREATE INDEX IF NOT EXISTS ix_users_admin_scope_region ON users (admin_scope_region)",
        "UPDATE users SET is_verified = true WHERE provider_level IS NOT NULL",
    ]
    async with engine.connect() as conn:
        await conn.execution_options(isolation_level="AUTOCOMMIT")
        for stmt in statements:
            try:
                await conn.execute(text(stmt))
            except Exception as e:
                print(f"[startup] migration skipped: {e}")

@asynccontextmanager
async def lifespan(app: FastAPI):
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    await _run_migrations()

    # ★ 启动 AI 视频临时文件清理任务
    from app.routers.ai_video import cleanup_stale_temp_files
    cleanup_task = asyncio.create_task(cleanup_stale_temp_files())

    yield

    # ★ 关闭时取消清理任务
    cleanup_task.cancel()
    try:
        await cleanup_task
    except asyncio.CancelledError:
        pass

app = FastAPI(title="FDQ95 API", version="0.4.0", lifespan=lifespan)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
# ★ AI 视频工作室
# app.include_router(ai_video.router, prefix="/api/ai-video", tags=["ai-video"])
# 在 app = FastAPI(...) 之后，添加路由注册
app.include_router(ai_video.router)

@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request, exc):
    print(f"[HTTP {exc.status_code}] {request.method} {request.url} → {exc.detail}")
    return JSONResponse(status_code=exc.status_code, content={"detail": exc.detail})


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request, exc):
    print(f"[VALIDATION] {request.method} {request.url}\n{exc.errors()}")
    return JSONResponse(status_code=422, content={"detail": exc.errors()})


@app.exception_handler(Exception)
async def generic_exception_handler(request, exc):
    print(f"[UNHANDLED] {request.method} {request.url}")
    traceback.print_exc()
    return JSONResponse(status_code=500, content={"detail": str(exc)})


app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ★ 挂载 /uploads 静态目录
UPLOAD_DIR = Path("/app/uploads")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
app.mount("/uploads", StaticFiles(directory=str(UPLOAD_DIR)), name="uploads")

# ---- auth routers ----
app.include_router(
    fastapi_users.get_auth_router(auth_backend),
    prefix="/auth/jwt",
    tags=["auth"],
)
app.include_router(
    fastapi_users.get_verify_router(UserRead), prefix="/auth", tags=["auth"]
)
app.include_router(
    fastapi_users.get_reset_password_router(), prefix="/auth", tags=["auth"]
)
app.include_router(
    fastapi_users.get_users_router(UserRead, UserUpdate),
    prefix="/users",
    tags=["users"],
)
app.include_router(register_guard.router, prefix="/auth", tags=["auth"])
app.include_router(auth_extra.router, prefix="/api/auth", tags=["auth-extra"])

# ---- domain routers ----
app.include_router(translate.router, prefix="/api/translate", tags=["translate"])
app.include_router(jobs.router, prefix="/api/jobs", tags=["jobs"])
app.include_router(
    applications.router, prefix="/api/applications", tags=["applications"]
)
app.include_router(profile.router, prefix="/api/profile", tags=["profile"])
app.include_router(follows.router, prefix="/api/social", tags=["social"])
app.include_router(friends.router, prefix="/api/friends", tags=["friends"])
app.include_router(messages.router, prefix="/api/messages", tags=["messages"])
app.include_router(videos.router, prefix="/api/videos", tags=["videos"])
app.include_router(articles.router, prefix="/api/articles", tags=["articles"])
app.include_router(products.router, prefix="/api/products", tags=["products"])
app.include_router(activities.router, prefix="/api/activities", tags=["activities"])
app.include_router(admin.router, prefix="/api/admin", tags=["admin"])


@app.get("/health")
async def health():
    return {"status": "ok"}