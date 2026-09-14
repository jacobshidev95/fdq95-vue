import enum
import uuid

from sqlalchemy import Boolean, Enum as SAEnum, ForeignKey, Integer, String, Uuid
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


class ProviderLevel(str, enum.Enum):
    """Hierarchy for service providers (lower number = higher rank).

    level_0  System Administrator
    level_1  National Administrator   (managed by level_0)
    level_2  Regional Administrator   (managed by level_1)
    level_3  Sales Administrator      (managed by level_2)
    level_4  Service Provider         (managed by level_3)  <- default on register
    """

    SYSTEM_ADMIN = "level_0"
    NATIONAL_ADMIN = "level_1"
    REGIONAL_ADMIN = "level_2"
    SALES_ADMIN = "level_3"
    PROVIDER = "level_4"


class User(Base, SQLAlchemyBaseUserTableUUID):
    __tablename__ = "users"

    user_id: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    gender: Mapped[str | None] = mapped_column(String(16), nullable=True)
    age: Mapped[int | None] = mapped_column(Integer, nullable=True)
    country: Mapped[str | None] = mapped_column(String(64), nullable=True)

    role: Mapped[UserRole] = mapped_column(
        SAEnum(UserRole, name="user_role"),
        default=UserRole.CONSUMER,
    )
    service_category: Mapped[ServiceCategory | None] = mapped_column(
        SAEnum(ServiceCategory, name="service_category"),
        nullable=True,
    )

    # ---- provider hierarchy ----
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

    # ---- provider-only contact fields ----
    phone: Mapped[str | None] = mapped_column(String(32), nullable=True)
    real_name: Mapped[str | None] = mapped_column(String(128), nullable=True)
    phone_verified: Mapped[bool] = mapped_column(Boolean, default=False)