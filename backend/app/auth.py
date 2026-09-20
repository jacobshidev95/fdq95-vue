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
from app.email_service import send_verification_email, send_password_reset_email
from app.models import ProviderLevel, User, UserRole
from app.services.user_template import create_profile_for_user


# 管理员级别：这些账号由上级分配，不需要邮箱验证
ADMIN_LEVELS = (
    ProviderLevel.SYSTEM_ADMIN,
    ProviderLevel.NATIONAL_ADMIN,
    ProviderLevel.REGIONAL_ADMIN,
    ProviderLevel.SALES_ADMIN,
)


# ★ 客户等级映射（0-9）：provider_level → customer_level
_CUSTOMER_LEVEL_MAP = {
    None: 0,
    ProviderLevel.SYSTEM_ADMIN: 9,
    ProviderLevel.NATIONAL_ADMIN: 2,
    ProviderLevel.REGIONAL_ADMIN: 1,
    ProviderLevel.SALES_ADMIN: 3,
    ProviderLevel.PROVIDER: 0,
}


def _level_to_customer_level(level) -> int:
    """根据 provider_level 计算 customer_level。普通用户默认为 0。"""
    return _CUSTOMER_LEVEL_MAP.get(level, 0)


class UserManager(UUIDIDMixin, BaseUserManager[User, uuid.UUID]):
    reset_password_token_secret = settings.SECRET_KEY
    verification_token_secret = settings.SECRET_KEY

    # ----------------------------------------------------------------
    # 登录检查：
    #   - 冻结账号 → 拒绝
    #   - 管理员（level_0/1/2/3）→ 放行，不检查邮箱验证
    #   - 普通客户 → 必须 is_verified=True 才放行
    # ----------------------------------------------------------------
    async def authenticate(self, credentials):
        user = await super().authenticate(credentials)
        if user is None:
            return None

        if getattr(user, "is_frozen", False):
            print(f"[AUTH] login blocked — frozen account {user.user_id}")
            return None

        # 管理员无需邮箱验证
        if user.provider_level in ADMIN_LEVELS:
            return user

        # 普通客户必须已验证邮箱
        if not user.is_verified:
            print(f"[AUTH] login blocked — unverified consumer {user.user_id}")
            return None

        return user

    # ----------------------------------------------------------------
    # 创建用户：
    #   - 管理员自动标记已验证
    #   - 根据 provider_level 自动设置 customer_level
    # ----------------------------------------------------------------
    async def create(self, user_create, safe: bool = False, request=None) -> User:
        role = getattr(user_create, "role", UserRole.CONSUMER)
        level = getattr(user_create, "provider_level", None)

        if role == UserRole.PROVIDER:
            if level is None:
                user_create.provider_level = ProviderLevel.PROVIDER
        else:
            user_create.provider_level = None

        # ★ 强制根据 provider_level 计算 customer_level（忽略前端传入）
        user_create.customer_level = _level_to_customer_level(
            user_create.provider_level
        )

        user = await super().create(user_create, safe=safe, request=request)

        # 管理员账号（level_0/1/2/3）不需要邮箱验证 → 立即标记
        if user.provider_level in ADMIN_LEVELS and not user.is_verified:
            user.is_verified = True
            await self.user_db.update(user, {"is_verified": True})
            print(f"[AUTH] admin {user.user_id} auto-verified on create")

        return user

    # ----------------------------------------------------------------
    # 注册后：仅普通客户需要发送验证邮件
    # ----------------------------------------------------------------
    async def on_after_register(self, user: User, request=None) -> None:
        print(
            f"[AUTH] registered user={user.id} email={user.email} "
            f"verified={user.is_verified} level={user.customer_level}"
        )

        if user.is_verified:
            print(f"[AUTH] skip verification email (already verified) for {user.email}")
            return

        try:
            await self.request_verify(user, request)
            print(f"[AUTH] verification email dispatched to {user.email}")
        except Exception as e:
            print(f"[AUTH] request_verify failed: {type(e).__name__}: {e}")

    async def on_after_request_verify(
        self, user: User, token: str, request=None
    ) -> None:
        try:
            ok = await send_verification_email(user.email, token)
            print(f"[AUTH] send_verification_email -> {ok}")
        except Exception as e:
            print(f"[AUTH] verification email failed: {type(e).__name__}: {e}")

    async def on_after_verify(self, user: User, request=None) -> None:
        async with async_session_maker() as session:
            try:
                profile = await create_profile_for_user(session, user)
                print(f"[AUTH] profile created for user={user.id} profile={profile.id}")
            except Exception as e:
                print(f"[AUTH] profile creation failed: {e}")

    async def on_after_forgot_password(
        self, user: User, token: str, request=None
    ) -> None:
        try:
            ok = await send_password_reset_email(user.email, token)
            print(f"[AUTH] send_password_reset_email -> {ok}")
        except Exception as e:
            print(f"[AUTH] password reset email failed: {type(e).__name__}: {e}")


async def get_user_db(session=Depends(get_async_session)):
    yield SQLAlchemyUserDatabase(session, User)


async def get_user_manager(user_db=Depends(get_user_db)):
    yield UserManager(user_db)


bearer_transport = BearerTransport(tokenUrl="/auth/jwt/login")


def get_jwt_strategy() -> JWTStrategy:
    return JWTStrategy(
        secret=settings.SECRET_KEY,
        lifetime_seconds=60 * 60 * 24 * 7,   # 7 天
    )


auth_backend = AuthenticationBackend(
    name="jwt",
    transport=bearer_transport,
    get_strategy=get_jwt_strategy,
)

fastapi_users = FastAPIUsers[User, uuid.UUID](get_user_manager, [auth_backend])
current_active_user = fastapi_users.current_user(active=True)