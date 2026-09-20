import enum
import uuid

from datetime import datetime
from sqlalchemy import (
    Boolean,
    DateTime,
    Enum as SAEnum,
    ForeignKey,
    Integer,
    String,
    Text,
    Uuid,
    func,
    UniqueConstraint,
    JSON,
    Index,
)

from sqlalchemy.dialects.postgresql import ENUM as PGEnum

from sqlalchemy.orm import Mapped, mapped_column

from fastapi_users_db_sqlalchemy import SQLAlchemyBaseUserTableUUID

from app.database import Base


class UserRole(str, enum.Enum):
    PROVIDER = "provider"
    CONSUMER = "consumer"


class ServiceCategory(str, enum.Enum):
    MEDICAL = "medical"
    HEALTH = "health"
    EDUCATION = "education"
    ENTERTAINMENT = "entertainment"
    TRAVEL = "travel"
    FOOD = "food"
    CLOTHING = "clothing"
    INDUSTRY = "industry"
    TECH = "tech"
    IOT = "iot"
    LIFE = "life"
    AI = "ai"


class ProviderLevel(str, enum.Enum):
    SYSTEM_ADMIN = "level_0"
    NATIONAL_ADMIN = "level_1"
    REGIONAL_ADMIN = "level_2"
    SALES_ADMIN = "level_3"
    PROVIDER = "level_4"


class MessageType(str, enum.Enum):
    TEXT = "text"
    IMAGE = "image"
    VIDEO = "video"
    VOICE = "voice"


class RequestStatus(str, enum.Enum):
    PENDING = "pending"
    ACCEPTED = "accepted"
    REJECTED = "rejected"


class User(Base, SQLAlchemyBaseUserTableUUID):
    __tablename__ = "users"

    user_id: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    gender: Mapped[str | None] = mapped_column(String(16), nullable=True)
    age: Mapped[int | None] = mapped_column(Integer, nullable=True)
    country: Mapped[str | None] = mapped_column(String(64), nullable=True)
    region: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)

    first_name: Mapped[str | None] = mapped_column(String(64), nullable=True)
    last_name: Mapped[str | None] = mapped_column(String(64), nullable=True)
    real_name: Mapped[str | None] = mapped_column(String(128), nullable=True)
    real_verified: Mapped[bool] = mapped_column(Boolean, default=False)

    face_enrolled: Mapped[bool] = mapped_column(Boolean, default=False)
    face_credential_id: Mapped[str | None] = mapped_column(
        String(256), nullable=True
    )

    role: Mapped[UserRole] = mapped_column(
        SAEnum(UserRole, name="user_role"),
        default=UserRole.CONSUMER,
    )
    service_category: Mapped[ServiceCategory | None] = mapped_column(
        SAEnum(ServiceCategory, name="service_category"),
        nullable=True,
    )

    provider_level: Mapped[ProviderLevel | None] = mapped_column(
        SAEnum(ProviderLevel, name="provider_level"),
        nullable=True,
        default=None,
    )
    managed_by_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )

    admin_scope_country: Mapped[str | None] = mapped_column(
        String(8), nullable=True, index=True
    )
    admin_scope_region: Mapped[str | None] = mapped_column(
        String(64), nullable=True, index=True
    )

    is_frozen: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    customer_level: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    phone: Mapped[str | None] = mapped_column(String(32), nullable=True)
    phone_verified: Mapped[bool] = mapped_column(Boolean, default=False)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )


class Profile(Base):
    __tablename__ = "profiles"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        unique=True,
        index=True,
    )
    display_name: Mapped[str] = mapped_column(String(64), default="")
    avatar_url: Mapped[str | None] = mapped_column(String(512), nullable=True)
    bio_line_1: Mapped[str] = mapped_column(String(160), default="")
    bio_line_2: Mapped[str] = mapped_column(String(160), default="")
    real_verified: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )


# ─────────────────────────────────────────────────────────────
# Video 表
# ★ 修复：hearts / likes / views 都加 server_default="0"
#    解决 "null value in column hearts violates not-null constraint"
# ─────────────────────────────────────────────────────────────
class Video(Base):
    __tablename__ = "videos"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), index=True
    )
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    url: Mapped[str] = mapped_column(String(512), nullable=False)
    thumbnail_url: Mapped[str | None] = mapped_column(String(512), nullable=True)
    duration_sec: Mapped[int] = mapped_column(
        Integer, default=0, server_default="0", nullable=False
    )

    category: Mapped[ServiceCategory | None] = mapped_column(
        PGEnum(ServiceCategory, name="service_category", create_type=False),
        nullable=True,
    )
    content_type: Mapped[str | None] = mapped_column(String(16), nullable=True)
    file_size: Mapped[int | None] = mapped_column(Integer, nullable=True)

    # ★ 计数 3 列：加 server_default，避免 NOT NULL 报错
    views: Mapped[int] = mapped_column(
        Integer, default=0, server_default="0", nullable=False
    )
    likes: Mapped[int] = mapped_column(
        Integer, default=0, server_default="0", nullable=False
    )
    hearts: Mapped[int] = mapped_column(
        Integer, default=0, server_default="0", nullable=False
    )

    # ★ 新增：字幕相关字段
    subtitle_status: Mapped[str | None] = mapped_column(String(16), nullable=True)
    subtitle_lang: Mapped[str | None] = mapped_column(String(8), nullable=True)
    subtitle_json: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )


class ActivityVideo(Base):
    __tablename__ = "activity_videos"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), index=True
    )
    activity_id: Mapped[str] = mapped_column(String(64), index=True)
    title: Mapped[str] = mapped_column(String(200), default="")
    url: Mapped[str] = mapped_column(String(512))
    thumbnail_url: Mapped[str | None] = mapped_column(String(512), nullable=True)
    duration_sec: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), index=True
    )


class Follow(Base):
    __tablename__ = "follows"
    __table_args__ = (
        UniqueConstraint("follower_id", "following_id", name="uq_follow"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    follower_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE")
    )
    following_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE")
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )


class Follower(Base):
    __tablename__ = "followers"
    __table_args__ = (
        UniqueConstraint("user_id", "follower_id", name="uq_follower"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE")
    )
    follower_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE")
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )


class MessageInbox(Base):
    __tablename__ = "messages_inbox"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    recipient_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), index=True
    )
    sender_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), index=True
    )
    content: Mapped[str] = mapped_column(Text, default="")
    content_type: Mapped[MessageType] = mapped_column(
        SAEnum(MessageType, name="message_type"), default=MessageType.TEXT
    )
    media_url: Mapped[str | None] = mapped_column(String(512), nullable=True)
    read: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), index=True
    )


class MessageOutbox(Base):
    __tablename__ = "messages_outbox"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    sender_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), index=True
    )
    recipient_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), index=True
    )
    content: Mapped[str] = mapped_column(Text, default="")
    content_type: Mapped[MessageType] = mapped_column(
        SAEnum(MessageType, name="message_type_out"), default=MessageType.TEXT
    )
    media_url: Mapped[str | None] = mapped_column(String(512), nullable=True)
    delivered: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), index=True
    )


class FriendRequestInbox(Base):
    __tablename__ = "friend_requests_inbox"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    recipient_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), index=True
    )
    sender_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), index=True
    )
    status: Mapped[RequestStatus] = mapped_column(
        SAEnum(RequestStatus, name="request_status_in"),
        default=RequestStatus.PENDING,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )


class FriendRequestOutbox(Base):
    __tablename__ = "friend_requests_outbox"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    sender_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), index=True
    )
    recipient_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), index=True
    )
    status: Mapped[RequestStatus] = mapped_column(
        SAEnum(RequestStatus, name="request_status_out"),
        default=RequestStatus.PENDING,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )


class Friend(Base):
    __tablename__ = "friends"
    __table_args__ = (
        UniqueConstraint("user_id", "friend_id", name="uq_friend"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE")
    )
    friend_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE")
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )


# ─────────────────────────────────────────────────────────────
# Article 表
# ─────────────────────────────────────────────────────────────
class Article(Base):
    __tablename__ = "articles"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        index=True,
    )
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    category: Mapped[ServiceCategory] = mapped_column(
        PGEnum(ServiceCategory, name="service_category", create_type=False),
        nullable=False,
    )
    content_type: Mapped[str] = mapped_column(String(16), nullable=False)
    file_url: Mapped[str | None] = mapped_column(String(512), nullable=True)
    file_name: Mapped[str | None] = mapped_column(String(256), nullable=True)
    file_size: Mapped[int | None] = mapped_column(Integer, nullable=True)
    rich_blocks: Mapped[list | None] = mapped_column(JSON, nullable=True)
    link_url: Mapped[str | None] = mapped_column(String(1024), nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )