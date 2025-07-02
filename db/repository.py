import sqlite3
from sqlite3 import Connection
import json
from datetime import datetime
import config
from db.models import Order

def get_connection() -> Connection:
    return sqlite3.connect(config.DB_PATH)

def init_db():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            username TEXT,
            type TEXT NOT NULL,
            data TEXT NOT NULL,
            status TEXT NOT NULL,
            payment_status TEXT NOT NULL,
            created_at TEXT NOT NULL
        )
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS service_prices (
            type TEXT PRIMARY KEY,
            price INTEGER NOT NULL
        )
    """)
    for svc, default in (
        ("auto", config.AUTO_SERVICE_PRICE),
        ("details_to", config.DETAILS_TO_SERVICE_PRICE),
        ("details_order", config.DETAILS_ORDER_SERVICE_PRICE),
    ):
        cur.execute(
            "INSERT OR IGNORE INTO service_prices(type, price) VALUES(?, ?)",
            (svc, default)
        )
    conn.commit()
    conn.close()

def create_order(user_id: int, username: str, type: str, data: dict) -> int:
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO orders (user_id, username, type, data, status, payment_status, created_at) VALUES (?, ?, ?, ?, ?, ?, ?)",
        (user_id, username, type, json.dumps(data), "new", "pending", datetime.utcnow().isoformat())
    )
    order_id = cur.lastrowid
    conn.commit()
    conn.close()
    return order_id

def get_orders_count(user_id: int) -> int:
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM orders WHERE user_id = ?", (user_id,))
    count = cur.fetchone()[0]
    conn.close()
    return count

def get_orders(user_id: int, offset: int, limit: int) -> list[Order]:
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        "SELECT id, user_id, username, type, data, status, payment_status, created_at FROM orders WHERE user_id = ? ORDER BY created_at DESC LIMIT ? OFFSET ?",
        (user_id, limit, offset)
    )
    rows = cur.fetchall()
    conn.close()
    orders = []
    for row in rows:
        data = json.loads(row[4])
        orders.append(Order(
            id=row[0],
            user_id=row[1],
            username=row[2],
            type=row[3],
            data=data,
            status=row[5],
            payment_status=row[6],
            created_at=datetime.fromisoformat(row[7])
        ))
    return orders

def get_order(order_id: int) -> Order or None:
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        "SELECT id, user_id, username, type, data, status, payment_status, created_at FROM orders WHERE id = ?",
        (order_id,)
    )
    row = cur.fetchone()
    conn.close()
    if row:
        data = json.loads(row[4])
        return Order(
            id=row[0],
            user_id=row[1],
            username=row[2],
            type=row[3],
            data=data,
            status=row[5],
            payment_status=row[6],
            created_at=datetime.fromisoformat(row[7])
        )
    return None

def update_order_status(order_id: int, status: str):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("UPDATE orders SET status = ? WHERE id = ?", (status, order_id))
    conn.commit()
    conn.close()

def update_order_payment_status(order_id: int, payment_status: str):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("UPDATE orders SET payment_status = ? WHERE id = ?", (payment_status, order_id))
    conn.commit()
    conn.close()

def update_order_data(order_id: int, data: dict):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("UPDATE orders SET data = ? WHERE id = ?", (json.dumps(data), order_id))
    conn.commit()
    conn.close()

def get_orders_count_by_status(status: str) -> int:
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM orders WHERE status = ?", (status,))
    count = cur.fetchone()[0]
    conn.close()
    return count

def get_orders_by_status(status: str, offset: int, limit: int) -> list[Order]:
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        "SELECT id, user_id, username, type, data, status, payment_status, created_at "
        "FROM orders WHERE status = ? ORDER BY created_at DESC LIMIT ? OFFSET ?",
        (status, limit, offset)
    )
    rows = cur.fetchall()
    conn.close()
    orders = []
    for row in rows:
        data = json.loads(row[4])
        orders.append(Order(
            id=row[0], user_id=row[1], username=row[2],
            type=row[3], data=data, status=row[5],
            payment_status=row[6], created_at=datetime.fromisoformat(row[7])
        ))
    return orders

def get_service_price(service_type: str) -> int:
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT price FROM service_prices WHERE type = ?", (service_type,))
    row = cur.fetchone()
    conn.close()
    if row:
        return row[0]
    return {
        "auto": config.AUTO_SERVICE_PRICE,
        "details_to": config.DETAILS_TO_SERVICE_PRICE,
        "details_order": config.DETAILS_ORDER_SERVICE_PRICE
    }.get(service_type, 0)

def set_service_price(service_type: str, price: int):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        "INSERT OR REPLACE INTO service_prices(type, price) VALUES(?, ?)",
        (service_type, price)
    )
    conn.commit()
    conn.close()
