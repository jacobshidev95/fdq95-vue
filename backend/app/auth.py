import uuid

from fastapi import Depends
from fastapi_users import BaseUserManager, FastAPIUsers, UUIDIDMixin
from fastapi_users.authentication import (
    AuthenticationBackend,
    BearerTransport,
    JWTStrategy,
)
from fastapi_users_db_sqlalchemy import SQLAlchemyUserDatabase

from app.config import settings
from app.database import get_async_session
from app.email_service import send_verification_email
from app.models import ProviderLevel, User, UserRole


class UserManager(UUIDIDMixin, BaseUserManager[User, uuid.UUID]):
    reset_password_token_secret = settings.SECRET_KEY
    verification_token_secret = settings.SECRET_KEY

    async def create(
        self,
        user_create,
        safe: bool = False,
        request=None,
    ) -> User:
        """Enforce hierarchy rules on user creation.

        - Providers always start at level_4 (Service Provider).
        - Consumers have no provider_level.
        """
        role = getattr(user_create, "role", UserRole.CONSUMER)
        level = getattr(user_create, "provider_level", None)

        if role == UserRole.PROVIDER:
            # force default to level_4 on registration
            if level is None:
                user_create.provider_level = ProviderLevel.PROVIDER
        else:
            # consumers do not participate in the provider hierarchy
            user_create.provider_level = None

        return await super().create(user_create, safe=safe, request=request)

    async def on_after_register(self, user: User, request=None) -> None:  # type: ignore[override]
        print(
            f"[AUTH] User {user.id} registered. "
            f"role={user.role.value} level={user.provider_level}"
        )

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


async def get_user_db(session=Depends(get_async_session)):
    yield SQLAlchemyUserDatabase(session, User)


async def get_user_manager(user_db=Depends(get_user_db)):
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