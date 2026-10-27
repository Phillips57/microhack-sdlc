from __future__ import annotations

from fastapi import APIRouter, Query

from models.product import CreateProductRequest, Product, UpdateProductRequest
from repositories.products import ProductsRepository
from utils.errors import NotFoundException, ValidationException

router = APIRouter(prefix="/api/products", tags=["Products"])
repository = ProductsRepository()


@router.get("", response_model=list[Product])
async def get_all(
    q: str | None = Query(default=None, description="Case-insensitive search across product name and SKU"),
    min_price: float | None = Query(default=None, ge=0, description="Minimum product price, inclusive"),
    max_price: float | None = Query(default=None, ge=0, description="Maximum product price, inclusive"),
) -> list[Product]:
    if min_price is not None and max_price is not None and min_price > max_price:
        raise ValidationException("min_price must be less than or equal to max_price")
    return await repository.find_all(q=q, min_price=min_price, max_price=max_price)


@router.get("/{product_id}", response_model=Product)
async def get_by_id(product_id: int) -> Product:
    product = await repository.find_by_id(product_id)
    if product is None:
        raise NotFoundException("Product", product_id)
    return product


@router.post("", response_model=Product, status_code=201)
async def create(request: CreateProductRequest) -> Product:
    if not request.name.strip():
        raise ValidationException("name is required")
    return await repository.create(request)


@router.put("/{product_id}", response_model=Product)
async def update(product_id: int, request: UpdateProductRequest) -> Product:
    return await repository.update(product_id, request)


@router.delete("/{product_id}", status_code=204)
async def delete(product_id: int) -> None:
    await repository.delete(product_id)
