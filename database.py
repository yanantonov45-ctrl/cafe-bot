import json

import aiosqlite

from config import DB_PATH, FINAL_STATUSES


async def init_db() -> None:
    async with aiosqlite.connect(DB_PATH) as db:
        await db.executescript(
            """
            CREATE TABLE IF NOT EXISTS cart (
                user_id INTEGER NOT NULL,
                item_id TEXT    NOT NULL,
                qty     INTEGER NOT NULL,
                PRIMARY KEY (user_id, item_id)
            );
            CREATE TABLE IF NOT EXISTS orders (
                id            INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id       INTEGER NOT NULL,
                items         TEXT    NOT NULL,   -- JSON: [{name, price, qty}]
                subtotal      INTEGER NOT NULL,
                delivery_fee  INTEGER NOT NULL,
                total         INTEGER NOT NULL,
                delivery_type TEXT    NOT NULL,   -- delivery / pickup
                address       TEXT,
                phone         TEXT    NOT NULL,
                comment       TEXT,
                status        TEXT    NOT NULL DEFAULT 'new',
                created_at    TEXT    NOT NULL DEFAULT CURRENT_TIMESTAMP
            );
            """
        )
        await db.commit()


async def _fetch(query: str, params: tuple = ()) -> list[dict]:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cur = await db.execute(query, params)
        return [dict(r) for r in await cur.fetchall()]


# ---------- Корзина ----------

async def get_cart(user_id: int) -> dict[str, int]:
    rows = await _fetch("SELECT item_id, qty FROM cart WHERE user_id = ?", (user_id,))
    return {r["item_id"]: r["qty"] for r in rows}


async def change_qty(user_id: int, item_id: str, delta: int) -> int:
    """Меняет количество позиции и возвращает новое (0 — удалена)."""
    qty = (await get_cart(user_id)).get(item_id, 0) + delta
    qty = max(0, min(qty, 99))
    async with aiosqlite.connect(DB_PATH) as db:
        if qty == 0:
            await db.execute("DELETE FROM cart WHERE user_id = ? AND item_id = ?",
                             (user_id, item_id))
        else:
            await db.execute(
                "INSERT INTO cart (user_id, item_id, qty) VALUES (?, ?, ?) "
                "ON CONFLICT(user_id, item_id) DO UPDATE SET qty = excluded.qty",
                (user_id, item_id, qty),
            )
        await db.commit()
    return qty


async def clear_cart(user_id: int) -> None:
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("DELETE FROM cart WHERE user_id = ?", (user_id,))
        await db.commit()


# ---------- Заказы ----------

async def create_order(user_id: int, items: list[dict], subtotal: int, fee: int,
                       delivery_type: str, address: str | None,
                       phone: str, comment: str | None) -> int:
    async with aiosqlite.connect(DB_PATH) as db:
        cur = await db.execute(
            "INSERT INTO orders (user_id, items, subtotal, delivery_fee, total, "
            "delivery_type, address, phone, comment) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (user_id, json.dumps(items, ensure_ascii=False), subtotal, fee,
             subtotal + fee, delivery_type, address, phone, comment),
        )
        await db.execute("DELETE FROM cart WHERE user_id = ?", (user_id,))
        await db.commit()
        return cur.lastrowid


def _parse(order: dict) -> dict:
    order["items"] = json.loads(order["items"])
    return order


async def get_order(order_id: int) -> dict | None:
    rows = await _fetch("SELECT * FROM orders WHERE id = ?", (order_id,))
    return _parse(rows[0]) if rows else None


async def set_status(order_id: int, status: str) -> None:
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("UPDATE orders SET status = ? WHERE id = ?", (status, order_id))
        await db.commit()


async def get_user_orders(user_id: int, limit: int = 5) -> list[dict]:
    rows = await _fetch(
        "SELECT * FROM orders WHERE user_id = ? ORDER BY id DESC LIMIT ?",
        (user_id, limit),
    )
    return [_parse(r) for r in rows]


async def get_active_orders() -> list[dict]:
    placeholders = ",".join("?" * len(FINAL_STATUSES))
    rows = await _fetch(
        f"SELECT * FROM orders WHERE status NOT IN ({placeholders}) ORDER BY id",
        tuple(FINAL_STATUSES),
    )
    return [_parse(r) for r in rows]
