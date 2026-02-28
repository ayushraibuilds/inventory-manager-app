import sqlite3
import json
import threading
from datetime import datetime
from contextlib import contextmanager

_db_lock = threading.Lock()

@contextmanager
def get_db_connection():
    conn = sqlite3.connect('sellers_memory.db', check_same_thread=False)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.close()

def init_db():
    """Run this once on startup to create the tables."""
    with _db_lock:
        with get_db_connection() as conn:
            conn.execute('''
                CREATE TABLE IF NOT EXISTS catalogs (
                    seller_id TEXT PRIMARY KEY,
                    catalog_data TEXT
                )
            ''')
            conn.execute('''
                CREATE TABLE IF NOT EXISTS activity_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    seller_id TEXT NOT NULL,
                    action TEXT NOT NULL,
                    item_name TEXT,
                    details TEXT
                )
            ''')
            conn.execute('''
                CREATE TABLE IF NOT EXISTS seller_profiles (
                    seller_id TEXT PRIMARY KEY,
                    store_name TEXT DEFAULT '',
                    address TEXT DEFAULT '',
                    gst_number TEXT DEFAULT '',
                    logo_url TEXT DEFAULT '',
                    phone TEXT DEFAULT '',
                    low_stock_alerts INTEGER DEFAULT 0,
                    updated_at TEXT
                )
            ''')
            conn.execute('''
                CREATE TABLE IF NOT EXISTS orders (
                    id TEXT PRIMARY KEY,
                    seller_id TEXT NOT NULL,
                    buyer_name TEXT DEFAULT '',
                    buyer_phone TEXT DEFAULT '',
                    items_json TEXT DEFAULT '[]',
                    total_amount REAL DEFAULT 0,
                    status TEXT DEFAULT 'PLACED',
                    created_at TEXT,
                    updated_at TEXT
                )
            ''')
            conn.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    id TEXT PRIMARY KEY,
                    email TEXT UNIQUE NOT NULL,
                    password_hash TEXT NOT NULL,
                    seller_id TEXT UNIQUE NOT NULL,
                    created_at TEXT
                )
            ''')
            conn.commit()

# --- Auth ---
def create_user(user_id: str, email: str, password_hash: str, seller_id: str):
    with _db_lock:
        with get_db_connection() as conn:
            conn.execute(
                'INSERT INTO users (id, email, password_hash, seller_id, created_at) VALUES (?, ?, ?, ?, ?)',
                (user_id, email, password_hash, seller_id, datetime.utcnow().isoformat() + "Z")
            )
            conn.commit()

def get_user_by_email(email: str) -> dict | None:
    with _db_lock:
        with get_db_connection() as conn:
            row = conn.execute('SELECT * FROM users WHERE email = ?', (email,)).fetchone()
            if row:
                return dict(row)
            return None

def save_catalog(seller_id: str, catalog_json: dict):
    """Inserts or overwrites a shopkeeper's specific ONDC catalog."""
    with _db_lock:
        with get_db_connection() as conn:
            conn.execute(
                'INSERT OR REPLACE INTO catalogs (seller_id, catalog_data) VALUES (?, ?)',
                (seller_id, json.dumps(catalog_json))
            )
            conn.commit()

def get_catalog(seller_id: str) -> dict:
    """Retrieves a specific shopkeeper's catalog if it exists."""
    with _db_lock:
        with get_db_connection() as conn:
            row = conn.execute('SELECT catalog_data FROM catalogs WHERE seller_id = ?', (seller_id,)).fetchone()
    if row:
        return json.loads(row['catalog_data'])
    return {"bpp/catalog": {"bpp/providers": [{"items": []}]}}

def get_all_catalogs() -> list:
    """Helper for the dashboard to quickly render everyone."""
    with _db_lock:
        with get_db_connection() as conn:
            rows = conn.execute('SELECT catalog_data FROM catalogs').fetchall()
    return [json.loads(row['catalog_data']) for row in rows]

def get_all_seller_ids() -> list:
    """Returns a list of all seller IDs in the database."""
    with _db_lock:
        with get_db_connection() as conn:
            rows = conn.execute('SELECT seller_id FROM catalogs').fetchall()
    return [row['seller_id'] for row in rows]

# --- Activity Log ---
def log_activity(seller_id: str, action: str, item_name: str = "", details: str = ""):
    """Log an activity event to the audit trail."""
    with _db_lock:
        with get_db_connection() as conn:
            conn.execute(
                'INSERT INTO activity_logs (timestamp, seller_id, action, item_name, details) VALUES (?, ?, ?, ?, ?)',
                (datetime.utcnow().isoformat(), seller_id, action, item_name, details)
            )
            conn.commit()

def get_activity_logs(limit: int = 50, seller_id: str = "") -> list:
    """Retrieve recent activity logs, optionally filtered by seller."""
    with _db_lock:
        with get_db_connection() as conn:
            if seller_id:
                rows = conn.execute(
                    'SELECT * FROM activity_logs WHERE seller_id = ? ORDER BY id DESC LIMIT ?',
                    (seller_id, limit)
                ).fetchall()
            else:
                rows = conn.execute(
                    'SELECT * FROM activity_logs ORDER BY id DESC LIMIT ?',
                    (limit,)
                ).fetchall()
    return [dict(row) for row in rows]

# --- Seller Profiles ---
def save_seller_profile(seller_id: str, profile: dict):
    """Create or update a seller's profile."""
    with _db_lock:
        with get_db_connection() as conn:
            conn.execute(
                '''INSERT OR REPLACE INTO seller_profiles
                   (seller_id, store_name, address, gst_number, logo_url, phone, low_stock_alerts, updated_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?)''',
                (
                    seller_id,
                    profile.get("store_name", ""),
                    profile.get("address", ""),
                    profile.get("gst_number", ""),
                    profile.get("logo_url", ""),
                    profile.get("phone", ""),
                    1 if profile.get("low_stock_alerts") else 0,
                    datetime.utcnow().isoformat()
                )
            )
            conn.commit()

def get_seller_profile(seller_id: str) -> dict:
    """Retrieve a seller's profile, or empty defaults."""
    with _db_lock:
        with get_db_connection() as conn:
            row = conn.execute('SELECT * FROM seller_profiles WHERE seller_id = ?', (seller_id,)).fetchone()
    if row:
        d = dict(row)
        d["low_stock_alerts"] = bool(d.get("low_stock_alerts", 0))
        return d
    return {
        "seller_id": seller_id,
        "store_name": "",
        "address": "",
        "gst_number": "",
        "logo_url": "",
        "phone": "",
        "low_stock_alerts": False,
        "updated_at": None
    }

# --- Orders ---
def create_order(order: dict):
    """Create a new order."""
    with _db_lock:
        with get_db_connection() as conn:
            conn.execute(
                '''INSERT INTO orders (id, seller_id, buyer_name, buyer_phone, items_json, total_amount, status, created_at, updated_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)''',
                (
                    order["id"],
                    order["seller_id"],
                    order.get("buyer_name", ""),
                    order.get("buyer_phone", ""),
                    json.dumps(order.get("items", [])),
                    order.get("total_amount", 0),
                    order.get("status", "PLACED"),
                    datetime.utcnow().isoformat(),
                    datetime.utcnow().isoformat()
                )
            )
            conn.commit()

def get_orders(seller_id: str = "", status: str = "", limit: int = 50, date_from: str = "", date_to: str = "", search: str = "") -> list:
    """Retrieve orders, optionally filtered by seller, status, date range, and search."""
    with _db_lock:
        with get_db_connection() as conn:
            query = 'SELECT * FROM orders WHERE 1=1'
            params: list = []
            if seller_id:
                query += ' AND seller_id = ?'
                params.append(seller_id)
            if status:
                query += ' AND status = ?'
                params.append(status)
            if date_from:
                query += ' AND created_at >= ?'
                params.append(date_from)
            if date_to:
                query += ' AND created_at <= ?'
                params.append(date_to + "T23:59:59")
            if search:
                query += ' AND (buyer_name LIKE ? OR id LIKE ?)'
                params.extend([f"%{search}%", f"%{search}%"])
            query += ' ORDER BY created_at DESC LIMIT ?'
            params.append(limit)
            rows = conn.execute(query, params).fetchall()
    results = []
    for row in rows:
        d = dict(row)
        d["items"] = json.loads(d.get("items_json", "[]"))
        d.pop("items_json", None)
        results.append(d)
    return results

def update_order_status(order_id: str, new_status: str) -> bool:
    """Update an order's status. Returns True if found."""
    success = False
    with _db_lock:
        with get_db_connection() as conn:
            cursor = conn.execute(
                'UPDATE orders SET status = ?, updated_at = ? WHERE id = ?',
                (new_status, datetime.utcnow().isoformat(), order_id)
            )
            conn.commit()
            success = cursor.rowcount > 0
    return success

