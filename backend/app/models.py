import enum

from sqlalchemy import Boolean, Enum as SAEnum, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from fastapi_users_db_sqlalchemy import SQLAlchemyBaseUserTableUUID

from app.database import Base


class UserRole(str, enum.Enum):
    PROVIDER = "provider"
    CONSUMER = "consumer"


class ServiceCategory(str, enum.Enum):
    MEDICAL = "medical"
    EDUCATION = "education"
    ENTERTAINMENT = "entertainment"
    TRAVEL = "travel"
    FOOD = "food"
    CLOTHING = "clothing"
    INDUSTRY = "industry"


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

    phone: Mapped[str | None] = mapped_column(String(32), nullable=True)
    real_name: Mapped[str | None] = mapped_column(String(128), nullable=True)
    phone_verified: Mapped[bool] = mapped_column(Boolean, default=False)
