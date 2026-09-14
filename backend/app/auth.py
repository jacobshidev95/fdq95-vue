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
from app.database import async_session_maker, get_async_session
from app.email_service import send_verification_email
from app.models import ProviderLevel, User, UserRole
from app.services.user_template import create_profile_for_user


class UserManager(UUIDIDMixin, BaseUserManager[User, uuid.UUID]):
    reset_password_token_secret = settings.SECRET_KEY
    verification_token_secret = settings.SECRET_KEY

    async def create(self, user_create, safe: bool = False, request=None) -> User:
        role = getattr(user_create, "role", UserRole.CONSUMER)
        level = getattr(user_create, "provider_level", None)
        if role == UserRole.PROVIDER:
            if level is None:
                user_create.provider_level = ProviderLevel.PROVIDER
        else:
            user_create.provider_level = None
        return await super().create(user_create, safe=safe, request=request)

    async def on_after_register(self, user: User, request=None) -> None:
        print(f"[AUTH] registered user={user.id}")

    async def on_after_request_verify(
        self, user: User, token: str, request=None
    ) -> None:
        try:
            await send_verification_email(user.email, token)
        except Exception as e:  # noqa: BLE001
            print(f"[AUTH] verification email failed: {e}")

    async def on_after_verify(self, user: User, request=None) -> None:
        """Called after email verification succeeds — build the user template."""
        async with async_session_maker() as session:
            try:
                profile = await create_profile_for_user(session, user)
                print(
                    f"[AUTH] profile created for user={user.id} "
                    f"profile={profile.id}"
                )
            except Exception as e:  # noqa: BLE001
                print(f"[AUTH] profile creation failed: {e}")

    async def on_after_forgot_password(
        self, user: User, token: str, request=None
    ) -> None:
        print(f"[AUTH] forgot password user={user.id}")


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