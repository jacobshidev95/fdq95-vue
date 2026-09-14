import uuid

from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter()


class Product(BaseModel):
    id: str
    seller_string_id: str
    name: str
    description: str
    price: float
    currency: str = "USD"
    image_url: str | None = None


# Placeholder catalogue. Wire to a `products` table later.
def _demo_products(seller: str) -> list[Product]:
    return [
        Product(
            id=f"p_{i}",
            seller_string_id=seller,
            name=f"Product #{i} from {seller}",
            description="Sample product listing.",
            price=9.99 * i,
        )
        for i in range(1, 6)
    ]


@router.get("/user/{user_string_id}")
async def list_user_products(user_string_id: str) -> dict:
    return {"products": [p.model_dump() for p in _demo_products(user_string_id)]}