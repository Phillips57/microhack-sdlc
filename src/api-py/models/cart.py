from __future__ import annotations

from pydantic import BaseModel, Field


class CartItem(BaseModel):
    productId: int
    name: str
    imgName: str | None = None
    unitPrice: float
    quantity: int
    lineTotal: float


class Cart(BaseModel):
    cartId: str
    items: list[CartItem]
    itemCount: int
    total: float


class AddCartItemRequest(BaseModel):
    productId: int = Field(gt=0)
    quantity: int = Field(gt=0)


class UpdateCartItemRequest(BaseModel):
    quantity: int = Field(gt=0)
