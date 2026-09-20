from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter()


class Activity(BaseModel):
    id: str
    host_string_id: str
    title: str
    description: str
    starts_at: str


@router.get("/user/{user_string_id}")
async def list_user_activities(user_string_id: str) -> dict:
    """Placeholder. Full activity page is defined separately."""
    return {"activities": []}


@router.post("")
async def create_activity(payload: dict) -> dict:
    return {"ok": True, "detail": "Activity endpoints are stubs."}