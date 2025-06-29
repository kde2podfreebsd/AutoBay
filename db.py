import sqlite3, json
from datetime import datetime
from config import DB_PATH

_conn = sqlite3.connect(DB_PATH, check_same_thread=False, detect_types=sqlite3.PARSE_DECLTYPES)
_conn.row_factory = sqlite3.Row
_cur = _conn.cursor()

def init_db():
    _cur.execute("""
    CREATE TABLE IF NOT EXISTS orders (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        username TEXT,
        type TEXT NOT NULL,
        data TEXT NOT NULL,
        status TEXT NOT NULL,
        created_at TIMESTAMP NOT NULL,
        admin_id INTEGER,
        reply_text TEXT,
        reply_media TEXT
    )""")
    _conn.commit()

def create_order(user_id, username, otype, data):
    now = datetime.utcnow()
    j = json.dumps(data, ensure_ascii=False)
    _cur.execute("INSERT INTO orders (user_id,username,type,data,status,created_at) VALUES (?,?,?,?,?,?)",
                (user_id, username, otype, j, 'new', now))
    _conn.commit()
    return _cur.lastrowid

def update_order_status(order_id, status):
    _cur.execute("UPDATE orders SET status=? WHERE id=?", (status, order_id))
    _conn.commit()

def assign_order(order_id, admin_id):
    _cur.execute("UPDATE orders SET admin_id=?, status='in_work' WHERE id=?", (admin_id, order_id))
    _conn.commit()

def save_admin_reply(order_id, text, media):
    j = json.dumps(media) if media else None
    _cur.execute("UPDATE orders SET reply_text=?, reply_media=? WHERE id=?", (text, j, order_id))
    _conn.commit()

def get_user_orders(user_id):
    _cur.execute("SELECT * FROM orders WHERE user_id=? ORDER BY created_at DESC", (user_id,))
    return _cur.fetchall()

def get_orders_by_status(status):
    _cur.execute("SELECT * FROM orders WHERE status=? ORDER BY created_at", (status,))
    return _cur.fetchall()

def get_order(order_id):
    _cur.execute("SELECT * FROM orders WHERE id=?", (order_id,))
    return _cur.fetchone()

def update_order_data_and_status(order_id, data, status):
    j = json.dumps(data, ensure_ascii=False)
    _cur.execute("UPDATE orders SET data=?, status=? WHERE id=?", (j, status, order_id))
    _conn.commit()
