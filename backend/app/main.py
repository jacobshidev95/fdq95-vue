from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from slowapi.errors import RateLimitExceeded
from sqlalchemy import text

from app.auth import auth_backend, fastapi_users
from app.config import settings
from app.database import Base, engine
from app.rate_limit import limiter, _rate_limit_exceeded_handler
from app.routers import (
    activities,
    applications,
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
)
from app.schemas import UserCreate, UserRead, UserUpdate


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
    yield


app = FastAPI(title="FDQ95 API", version="0.3.0", lifespan=lifespan)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# auth
app.include_router(
    fastapi_users.get_auth_router(auth_backend), prefix="/auth/jwt", tags=["auth"]
)
# NOTE: default register router is intentionally NOT mounted; register_guard
# provides a rate-limited, pre-validated replacement.
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

# guarded registration
app.include_router(register_guard.router, prefix="/auth", tags=["auth"])

# extra auth endpoints
app.include_router(
    auth_extra.router, prefix="/api/auth", tags=["auth-extra"]
)

# domain routers
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
app.include_router(products.router, prefix="/api/products", tags=["products"])
app.include_router(activities.router, prefix="/api/activities", tags=["activities"])


@app.get("/health")
async def health():
    return {"status": "ok"}