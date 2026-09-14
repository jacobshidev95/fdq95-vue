import uuid

from fastapi_users import BaseUserManager, FastAPIUsers, UUIDIDMixin
from fastapi_users.authentication import (
    AuthenticationBackend,
    BearerTransport,
    JWTStrategy,
)
from fastapi_users_db_sqlalchemy import SQLAlchemyUserDatabase

from app.config import settings
from app.database import get_async_session
from app.models import User
from app.email_service import send_verification_email


class UserManager(UUIDIDMixin, BaseUserManager[User, uuid.UUID]):
    reset_password_token_secret = settings.SECRET_KEY
    verification_token_secret = settings.SECRET_KEY

    async def on_after_register(self, user: User, request=None) -> None:  # type: ignore[override]
        print(f"[AUTH] User {user.id} registered.")

    async def on_after_forgot_password(
        self, user: User, token: str, request=None  # type: ignore[override]
    ) -> None:
        print(f"[AUTH] Forgot password for {user.id}: token={token}")

    async def on_after_request_verify(
        self, user: User, token: str, request=None  # type: ignore[override]
    ) -> None:
        try:
            await send_verification_email(user.email, token)
        except Exception as e:  # noqa: BLE001
            print(f"[AUTH] Failed to send verification email: {e}")


async def get_user_db(session=Depends(get_async_session)):  # noqa: F821
    yield SQLAlchemyUserDatabase(session, User)


from fastapi import Depends  # noqa: E402


async def get_user_manager(user_db=Depends(get_user_db)):  # noqa: F821
    yield UserManager(user_db)


bearer_transport = BearerTransport(tokenUrl="/auth/jwt/login")


def get_jwt_strategy() -> JWTStrategy:
    return JWTStrategy(secret=settings.SECRET_KEY, lifetime_seconds=3600)


auth_backend = AuthenticationBackend(
    name="jwt",
    transport=bearer_transport,
    get_strategy=get_jwt_strategy,
)


fastapi_users = FastAPIUsers[User, uuid.UUID](get_user_manager, [auth_backend])
current_active_user = fastapi_users.current_user(active=True)
