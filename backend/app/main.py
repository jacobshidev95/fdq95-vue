from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text

from app.auth import auth_backend, fastapi_users
from app.config import settings
from app.database import Base, engine
from app.routers import translate
from app.schemas import UserCreate, UserRead, UserUpdate


@asynccontextmanager
async def lifespan(app: FastAPI):
    # 1) create tables if missing
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    # 2) ensure new enum values exist (idempotent, PostgreSQL 12+)
    #    SQLAlchemy may store the enum member's name OR value depending on
    #    configuration; try both to be safe.
    for candidate in ("health", "HEALTH"):
        try:
            async with engine.connect() as conn:
                await conn.execution_options(isolation_level="AUTOCOMMIT")
                await conn.execute(
                    text(
                        f"ALTER TYPE service_category "
                        f"ADD VALUE IF NOT EXISTS '{candidate}'"
                    )
                )
        except Exception as e:  # noqa: BLE001
            print(f"[startup] enum migration for '{candidate}': {e}")

    yield


app = FastAPI(title="FDQ95 API", version="0.1.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# fastapi-users
app.include_router(
    fastapi_users.get_auth_router(auth_backend),
    prefix="/auth/jwt",
    tags=["auth"],
)
app.include_router(
    fastapi_users.get_register_router(UserRead, UserCreate),
    prefix="/auth",
    tags=["auth"],
)
app.include_router(
    fastapi_users.get_verify_router(UserRead),
    prefix="/auth",
    tags=["auth"],
)
app.include_router(
    fastapi_users.get_reset_password_router(),
    prefix="/auth",
    tags=["auth"],
)
app.include_router(
    fastapi_users.get_users_router(UserRead, UserUpdate),
    prefix="/users",
    tags=["users"],
)

# translation proxy
app.include_router(translate.router, prefix="/api/translate", tags=["translate"])


@app.get("/health")
async def health():
    return {"status": "ok"}