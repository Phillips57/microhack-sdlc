from __future__ import annotations

import uuid

import aiosqlite

from database.sqlite import get_connection
from models.cart import Cart, CartItem
from utils.errors import NotFoundException


class CartRepository:
    async def get_cart(self, cart_id: uuid.UUID) -> Cart:
        cart_key = str(cart_id)
        async with get_connection() as connection:
            await connection.execute(
                "INSERT OR IGNORE INTO carts (cart_id) VALUES (?);",
                (cart_key,),
            )
            await connection.commit()
            return await self._read_cart(connection, cart_key)

    async def add_item(self, cart_id: uuid.UUID, product_id: int, quantity: int) -> Cart:
        cart_key = str(cart_id)
        async with get_connection() as connection:
            await connection.execute("BEGIN IMMEDIATE;")
            cursor = await connection.execute(
                "SELECT 1 FROM products WHERE product_id = ?;",
                (product_id,),
            )
            if await cursor.fetchone() is None:
                raise NotFoundException("Product", product_id)

            await connection.execute(
                "INSERT OR IGNORE INTO carts (cart_id) VALUES (?);",
                (cart_key,),
            )
            await connection.execute(
                """
                INSERT INTO cart_items (cart_id, product_id, quantity)
                VALUES (?, ?, ?)
                ON CONFLICT (cart_id, product_id)
                DO UPDATE SET quantity = cart_items.quantity + excluded.quantity;
                """,
                (cart_key, product_id, quantity),
            )
            await connection.execute(
                "UPDATE carts SET updated_at = CURRENT_TIMESTAMP WHERE cart_id = ?;",
                (cart_key,),
            )
            await connection.commit()
            return await self._read_cart(connection, cart_key)

    async def update_item(self, cart_id: uuid.UUID, product_id: int, quantity: int) -> Cart:
        cart_key = str(cart_id)
        async with get_connection() as connection:
            cursor = await connection.execute(
                """
                UPDATE cart_items
                SET quantity = ?
                WHERE cart_id = ? AND product_id = ?;
                """,
                (quantity, cart_key, product_id),
            )
            if cursor.rowcount == 0:
                raise NotFoundException("Cart item", product_id)
            await connection.execute(
                "UPDATE carts SET updated_at = CURRENT_TIMESTAMP WHERE cart_id = ?;",
                (cart_key,),
            )
            await connection.commit()
            return await self._read_cart(connection, cart_key)

    async def remove_item(self, cart_id: uuid.UUID, product_id: int) -> None:
        cart_key = str(cart_id)
        async with get_connection() as connection:
            cursor = await connection.execute(
                "DELETE FROM cart_items WHERE cart_id = ? AND product_id = ?;",
                (cart_key, product_id),
            )
            if cursor.rowcount == 0:
                raise NotFoundException("Cart item", product_id)
            await connection.execute(
                "UPDATE carts SET updated_at = CURRENT_TIMESTAMP WHERE cart_id = ?;",
                (cart_key,),
            )
            await connection.commit()

    async def _read_cart(self, connection: aiosqlite.Connection, cart_id: str) -> Cart:
        cursor = await connection.execute(
            """
            SELECT
                p.product_id,
                p.name,
                p.img_name,
                ROUND(p.price * (1 - COALESCE(p.discount, 0)), 2) AS unit_price,
                ci.quantity,
                ROUND(
                    ROUND(p.price * (1 - COALESCE(p.discount, 0)), 2) * ci.quantity,
                    2
                ) AS line_total
            FROM cart_items AS ci
            JOIN products AS p ON p.product_id = ci.product_id
            WHERE ci.cart_id = ?
            ORDER BY p.product_id;
            """,
            (cart_id,),
        )
        rows = await cursor.fetchall()
        items = [
            CartItem(
                productId=row["product_id"],
                name=row["name"],
                imgName=row["img_name"],
                unitPrice=row["unit_price"],
                quantity=row["quantity"],
                lineTotal=row["line_total"],
            )
            for row in rows
        ]
        return Cart(
            cartId=cart_id,
            items=items,
            itemCount=sum(item.quantity for item in items),
            total=round(sum(item.lineTotal for item in items), 2),
        )
