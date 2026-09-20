import uuid
from typing import Optional, Dict, Any
from fastapi import Depends, Request
from fastapi_users import BaseUserManager, UUIDIDMixin
from fastapi_users.db import SQLAlchemyUserDatabase
from fastapi_users.jwt import generate_jwt

from app.db import get_user_db  # 假设你的 get_user_db 在这里
from app.models import User
from app.config import settings  # 假设你的配置在此处

class UserManager(UUIDIDMixin, BaseUserManager[User, uuid.UUID]):
    reset_password_token_secret = settings.SECRET_KEY
    verification_token_secret = settings.SECRET_KEY
    # 验证令牌有效期 (秒)
    verification_token_lifetime_seconds = 3600

    async def on_after_register(self, user: User, request: Optional[Request] = None):
        print(f"User {user.id} has registered.")
        # 注册后立即发送验证邮件
        await self.send_verification_email(user)

    async def on_after_request_verify(self, user: User, token: str, request: Optional[Request] = None):
        print(f"Verification requested for user {user.id}. Token: {token}")
        # 这个钩子通常由 /auth/request-verify-token 触发，如果你需要提供“重新发送验证邮件”功能，可以在这里实现

    async def on_after_forgot_password(self, user: User, token: str, request: Optional[Request] = None):
        print(f"User {user.id} has forgot their password. Token: {token}")
        # 发送重置密码邮件
        await self.send_password_reset_email(user, token)

    async def send_verification_email(self, user: User):
        token = generate_jwt(
            {"sub": str(user.id), "email": user.email, "aud": "fastapi-users:verify"},
            self.verification_token_secret,
            self.verification_token_lifetime_seconds,
        )
        # 请根据你的前端路由调整这里的 URL
        verification_link = f"{settings.FRONTEND_URL}/verify-email?token={token}"
        # 调用你现有的邮件发送函数
        await send_email(
            to=user.email,
            subject="Please verify your email address",
            body=f"Click the link to verify: {verification_link}",
        )

    async def send_password_reset_email(self, user: User, token: str):
        reset_link = f"{settings.FRONTEND_URL}/reset-password?token={token}"
        await send_email(
            to=user.email,
            subject="Password Reset Request",
            body=f"Click the link to reset your password: {reset_link}",
        )


async def get_user_manager(user_db: SQLAlchemyUserDatabase = Depends(get_user_db)):
    yield UserManager(user_db)