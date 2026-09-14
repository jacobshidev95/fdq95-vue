import uuid
from datetime import datetime

from fastapi_users import schemas
from pydantic import BaseModel, Field

from app.models import (
    MessageType,
    ProviderLevel,
    RequestStatus,
    ServiceCategory,
    UserRole,
)


# ---------------------------------------------------------------- users
class UserRead(schemas.BaseUser[uuid.UUID]):
    user_id: str
    gender: str | None = None
    age: int | None = None
    country: str | None = None
    role: UserRole = UserRole.CONSUMER
    service_category: ServiceCategory | None = None
    provider_level: ProviderLevel | None = None
    managed_by_id: uuid.UUID | None = None
    phone: str | None = None
    real_name: str | None = None
    phone_verified: bool = False
    created_at: datetime | None = None


class UserCreate(schemas.BaseUserCreate):
    user_id: str
    gender: str | None = None
    age: int | None = None
    country: str | None = None
    role: UserRole = UserRole.CONSUMER
    service_category: ServiceCategory | None = None
    provider_level: ProviderLevel | None = None
    phone: str | None = None
    real_name: str | None = None


class UserUpdate(schemas.BaseUserUpdate):
    gender: str | None = None
    age: int | None = None
    country: str | None = None
    phone: str | None = None
    real_name: str | None = None


# ---------------------------------------------------------------- profile
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


# ---------------------------------------------------------------- videos
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


# ---------------------------------------------------------------- messages
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


# ---------------------------------------------------------------- friend requests
class FriendRequestRead(BaseModel):
    id: uuid.UUID
    other_id: uuid.UUID
    other_string_id: str
    other_display_name: str
    status: RequestStatus
    created_at: datetime


# ---------------------------------------------------------------- friend
class FriendRead(BaseModel):
    user_id: uuid.UUID
    user_string_id: str
    display_name: str
    avatar_url: str | None