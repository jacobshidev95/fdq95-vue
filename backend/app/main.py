from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text

from app.auth import auth_backend, fastapi_users
from app.config import settings
from app.database import Base, engine
from app.routers import (
    activities,
    applications,
    friends,
    follows,
    jobs,
    messages,
    products,
    profile,
    translate,
    videos,
)
from app.schemas import UserCreate, UserRead, UserUpdate


async def _run_migrations() -> None:
    statements = [
        "ALTER TYPE service_category ADD VALUE IF NOT EXISTS 'health'",
        "ALTER TYPE service_category ADD VALUE IF NOT EXISTS 'tech'",
        "ALTER TYPE service_category ADD VALUE IF NOT EXISTS 'iot'",
        (
            "DO $$ BEGIN "
            "  CREATE TYPE provider_level AS ENUM "
            "    ('level_0','level_1','level_2','level_3','level_4'); "
            "EXCEPTION WHEN duplicate_object THEN null; END $$;"
        ),
        "ALTER TABLE users ADD COLUMN IF NOT EXISTS provider_level provider_level",
        "ALTER TABLE users ADD COLUMN IF NOT EXISTS managed_by_id UUID",
        "ALTER TABLE users ADD COLUMN IF NOT EXISTS created_at TIMESTAMPTZ DEFAULT now()",
    ]
    async with engine.connect() as conn:
        await conn.execution_options(isolation_level="AUTOCOMMIT")
        for stmt in statements:
            try:
                await conn.execute(text(stmt))
            except Exception as e:  # noqa: BLE001
                print(f"[startup] migration skipped: {e}")


@asynccontextmanager
async def lifespan(app: FastAPI):
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    await _run_migrations()
    yield


app = FastAPI(title="FDQ95 API", version="0.2.0", lifespan=lifespan)

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
app.include_router(
    fastapi_users.get_register_router(UserRead, UserCreate),
    prefix="/auth",
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