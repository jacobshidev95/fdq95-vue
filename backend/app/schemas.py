import uuid
from datetime import datetime

from fastapi_users import schemas
from pydantic import BaseModel, EmailStr, Field, computed_field, field_validator

from app.models import (
    MessageType,
    ProviderLevel,
    RequestStatus,
    ServiceCategory,
    UserRole,
)
import uuid
from datetime import datetime
from pydantic import BaseModel, Field
from app.models import ServiceCategory

class UserRead(schemas.BaseUser[uuid.UUID]):
    user_id: str
    gender: str | None = None
    age: int | None = None
    country: str | None = None
    region: str | None = None
    first_name: str | None = None
    last_name: str | None = None
    real_name: str | None = None
    real_verified: bool = False
    face_enrolled: bool = False
    role: UserRole = UserRole.CONSUMER
    service_category: ServiceCategory | None = None
    provider_level: ProviderLevel | None = None
    managed_by_id: uuid.UUID | None = None
    admin_scope_country: str | None = None
    admin_scope_region: str | None = None
    is_frozen: bool = False
    phone: str | None = None
    phone_verified: bool = False
    created_at: datetime | None = None
    customer_level: int = 0        # ★ 新增

    # ----------------------------------------------------------------
    # Derived fields (not stored in DB; computed on serialization)
    # ----------------------------------------------------------------
    @computed_field  # type: ignore[misc]
    @property
    def admin_level(self) -> int | None:
        """Return 0..4 for provider_level, or None for non-providers.

        level_0 → 0 (System Administrator)
        level_1 → 1 (National Administrator)
        level_2 → 2 (Regional Administrator)
        level_3 → 3 (Sales Administrator)
        level_4 → 4 (Service Provider)
        """
        if self.provider_level is None:
            return None
        try:
            return int(self.provider_level.value.split("_")[1])
        except (IndexError, ValueError):
            return None

    @computed_field  # type: ignore[misc]
    @property
    def is_admin(self) -> bool:
        """True for level_0, level_1, level_2."""
        return self.provider_level in (
            ProviderLevel.SYSTEM_ADMIN,
            ProviderLevel.NATIONAL_ADMIN,
            ProviderLevel.REGIONAL_ADMIN,
        )


class UserCreate(schemas.BaseUserCreate):
    user_id: str = Field(..., min_length=3, max_length=64)
    gender: str | None = None
    age: int | None = None
    country: str | None = None
    region: str | None = None
    first_name: str | None = None
    last_name: str | None = None
    role: UserRole = UserRole.CONSUMER
    service_category: ServiceCategory | None = None
    provider_level: ProviderLevel | None = None
    phone: str | None = None
    customer_level: int = 0        # ★ 新增

    @field_validator("user_id")
    @classmethod
    def validate_user_id(cls, v: str) -> str:
        v = v.strip()
        if not all(c.isalnum() or c in "_-" for c in v):
            raise ValueError(
                "User ID must be alphanumeric (underscore/hyphen allowed)"
            )
        return v


class UserUpdate(schemas.BaseUserUpdate):
    gender: str | None = None
    age: int | None = None
    country: str | None = None
    region: str | None = None
    first_name: str | None = None
    last_name: str | None = None
    phone: str | None = None


class ProfileRead(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    user_string_id: str
    display_name: str
    avatar_url: str | None
    bio_line_1: str
    bio_line_2: str
    real_verified: bool
    created_at: datetime

    class Config:
        from_attributes = True


class ProfileUpdate(BaseModel):
    display_name: str | None = None
    avatar_url: str | None = None
    bio_line_1: str | None = None
    bio_line_2: str | None = None


class VideoRead(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    title: str
    url: str
    thumbnail_url: str | None
    duration_sec: int
    views: int
    likes: int
    hearts: int
    created_at: datetime

    class Config:
        from_attributes = True


class ActivityVideoRead(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    activity_id: str
    title: str
    url: str
    thumbnail_url: str | None
    duration_sec: int
    created_at: datetime

    class Config:
        from_attributes = True


class MessageSend(BaseModel):
    content: str = ""
    content_type: MessageType = MessageType.TEXT
    media_url: str | None = None


class MessageRead(BaseModel):
    id: uuid.UUID
    sender_id: uuid.UUID
    sender_string_id: str
    sender_display_name: str
    content: str
    content_type: MessageType
    media_url: str | None
    read: bool
    created_at: datetime


class FriendRequestRead(BaseModel):
    id: uuid.UUID
    other_id: uuid.UUID
    other_string_id: str
    other_display_name: str
    status: RequestStatus
    created_at: datetime


class FriendRead(BaseModel):
    user_id: uuid.UUID
    user_string_id: str
    display_name: str
    avatar_url: str | None


class AvailabilityCheck(BaseModel):
    user_id: str | None = None
    email: str | None = None


class AvailabilityResult(BaseModel):
    user_id_taken: bool = False
    email_taken: bool = False
    available: bool = True


class FaceEnrollRequest(BaseModel):
    face_credential_id: str = Field(..., min_length=8, max_length=256)


class FaceLoginRequest(BaseModel):
    face_credential_id: str = Field(..., min_length=8, max_length=256)


class ForgotPasswordRequest(BaseModel):
    email: EmailStr


class ResetPasswordRequest(BaseModel):
    token: str
    password: str = Field(..., min_length=8)

# ★ 新增：Article schemas
class ArticleCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=200)
    category: str
    content_type: str = Field(..., pattern="^(file|rich|link)$")
    file_url: str | None = None
    file_name: str | None = None
    file_size: int | None = None
    rich_blocks: list[dict] | None = None
    link_url: str | None = None


class ArticleRead(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    title: str
    category: ServiceCategory
    content_type: str
    file_url: str | None = None
    file_name: str | None = None
    file_size: int | None = None
    rich_blocks: list[dict] | None = None
    link_url: str | None = None
    created_at: datetime

    class Config:
        from_attributes = True

# ★ 新增：Video schemas
class VideoCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=200)
    category: str
    content_type: str = Field(..., pattern="^(file|record|link)$")
    url: str
    duration_sec: int = 0
    file_size: int | None = None


class VideoCreateResponse(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    title: str
    category: ServiceCategory | None = None
    content_type: str | None = None
    url: str
    thumbnail_url: str | None = None
    duration_sec: int
    file_size: int | None = None
    views: int
    likes: int
    created_at: datetime

    class Config:
        from_attributes = True