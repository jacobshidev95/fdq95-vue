import uuid

from fastapi_users import schemas

from app.models import ProviderLevel, ServiceCategory, UserRole


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