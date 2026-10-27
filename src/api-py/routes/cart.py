from __future__ import annotations

import uuid

from fastapi import APIRouter, Path, Response

from models.cart import AddCartItemRequest, Cart, UpdateCartItemRequest
from repositories.cart import CartRepository

router = APIRouter(prefix="/api/cart", tags=["Cart"])
repository = CartRepository()


@router.get("/{cart_id}", response_model=Cart, summary="Get a cart and its totals")
async def get_cart(cart_id: uuid.UUID) -> Cart:
    return await repository.get_cart(cart_id)


@router.post("/{cart_id}/items", response_model=Cart, summary="Add a product to a cart")
async def add_item(cart_id: uuid.UUID, request: AddCartItemRequest) -> Cart:
    return await repository.add_item(cart_id, request.productId, request.quantity)


@router.put(
    "/{cart_id}/items/{product_id}",
    response_model=Cart,
    summary="Set a cart item's quantity",
)
async def update_item(
    cart_id: uuid.UUID,
    request: UpdateCartItemRequest,
    product_id: int = Path(gt=0),
) -> Cart:
    return await repository.update_item(cart_id, product_id, request.quantity)


@router.delete(
    "/{cart_id}/items/{product_id}",
    status_code=204,
    response_class=Response,
    summary="Remove a product from a cart",
)
async def remove_item(cart_id: uuid.UUID, product_id: int = Path(gt=0)) -> Response:
    await repository.remove_item(cart_id, product_id)
    return Response(status_code=204)
