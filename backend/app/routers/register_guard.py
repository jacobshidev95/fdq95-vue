from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import UserManager, get_user_manager
from app.database import get_async_session
from app.models import User
from app.rate_limit import limiter
from app.schemas import UserCreate, UserRead

router = APIRouter()


@router.post("/register", response_model=UserRead, status_code=201)
@limiter.limit("5/hour")
async def register_guarded(
    request: Request,
    payload: UserCreate,
    session: AsyncSession = Depends(get_async_session),
    user_manager: UserManager = Depends(get_user_manager),
) -> UserRead:
    """Rate-limited, pre-validated registration endpoint.

    - 5 registrations per hour per IP (slowapi)
    - Checks user_id uniqueness
    - Checks email uniqueness
    """
    # Pre-check user_id
    existing_id = await session.scalar(
        select(User).where(User.user_id == payload.user_id)
    )
    if existing_id:
        raise HTTPException(
            status_code=400, detail="User ID is already taken."
        )

    # Pre-check email
    existing_email = await session.scalar(
        select(User).where(User.email == payload.email)
    )
    if existing_email:
        raise HTTPException(
            status_code=400, detail="Email is already registered."
        )

    user = await user_manager.create(payload, safe=True)
    return UserRead.model_validate(user)