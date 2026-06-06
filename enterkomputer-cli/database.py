import sqlite3
import json
from typing import Optional
from models import Product, Category, Brand


DB_PATH = "enterkomputer.db"


def get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_conn()
    cur = conn.cursor()
    cur.executescript("""
        CREATE TABLE IF NOT EXISTS categories (
            id INTEGER PRIMARY KEY,
            name TEXT NOT NULL,
            slug TEXT NOT NULL,
            product_count INTEGER DEFAULT 0
        );
        CREATE TABLE IF NOT EXISTS brands (
            name TEXT PRIMARY KEY,
            product_count INTEGER DEFAULT 0
        );
        CREATE TABLE IF NOT EXISTS products (
            code TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            price INTEGER DEFAULT 0,
            category TEXT DEFAULT '',
            brand TEXT DEFAULT '',
            stock_status TEXT DEFAULT 'unknown',
            slug TEXT DEFAULT '',
            image_url TEXT DEFAULT '',
            specs TEXT DEFAULT '{}',
            description TEXT DEFAULT '',
            weight TEXT DEFAULT '',
            updated_at TEXT DEFAULT ''
        );
        CREATE INDEX IF NOT EXISTS idx_products_name ON products(name);
        CREATE INDEX IF NOT EXISTS idx_products_category ON products(category);
        CREATE INDEX IF NOT EXISTS idx_products_brand ON products(brand);
        CREATE INDEX IF NOT EXISTS idx_products_price ON products(price);
    """)
    conn.commit()
    conn.close()


def save_categories(categories: list[Category]):
    conn = get_conn()
    cur = conn.cursor()
    cur.executemany(
        "INSERT OR REPLACE INTO categories (id, name, slug, product_count) VALUES (?, ?, ?, ?)",
        [(c.id, c.name, c.slug, c.product_count) for c in categories]
    )
    conn.commit()
    conn.close()


def get_categories() -> list[Category]:
    conn = get_conn()
    cur = conn.cursor()
    rows = cur.execute("SELECT * FROM categories ORDER BY name").fetchall()
    conn.close()
    return [Category(id=r["id"], name=r["name"], slug=r["slug"], product_count=r["product_count"]) for r in rows]


def save_brands(brands: list[Brand]):
    conn = get_conn()
    cur = conn.cursor()
    cur.executemany(
        "INSERT OR REPLACE INTO brands (name, product_count) VALUES (?, ?)",
        [(b.name, b.product_count) for b in brands]
    )
    conn.commit()
    conn.close()


def get_brands() -> list[Brand]:
    conn = get_conn()
    cur = conn.cursor()
    rows = cur.execute("SELECT * FROM brands ORDER BY name").fetchall()
    conn.close()
    return [Brand(name=r["name"], product_count=r["product_count"]) for r in rows]


def save_products(products: list[Product]):
    conn = get_conn()
    cur = conn.cursor()
    for p in products:
        cur.execute(
            """INSERT OR REPLACE INTO products
               (code, name, price, category, brand, stock_status, slug, image_url, specs, description, weight, updated_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (p.code, p.name, p.price, p.category, p.brand, p.stock_status,
             p.slug, p.image_url, json.dumps(p.specs), p.description, p.weight, p.updated_at)
        )
    conn.commit()
    conn.close()


def search_products(keyword: str, category: str = "", brand: str = "",
                    min_price: int = 0, max_price: int = 0,
                    in_stock: bool = False,
                    sort_by: str = "", limit: int = 50) -> list[Product]:
    conn = get_conn()
    cur = conn.cursor()

    conditions = ["name LIKE ?"]
    params = [f"%{keyword}%"]

    if category:
        conditions.append("category = ?")
        params.append(category)
    if brand:
        conditions.append("brand = ?")
        params.append(brand)
    if min_price > 0:
        conditions.append("price >= ?")
        params.append(min_price)
    if max_price > 0:
        conditions.append("price <= ?")
        params.append(max_price)
    if in_stock:
        conditions.append("stock_status = 'ready'")

    order_map = {
        "termurah": "price ASC",
        "termahal": "price DESC",
        "nama": "name ASC",
        "terbaru": "updated_at DESC",
    }
    order = order_map.get(sort_by, "name ASC")

    query = f"SELECT * FROM products WHERE {' AND '.join(conditions)} ORDER BY {order} LIMIT ?"
    params.append(limit)

    rows = cur.execute(query, params).fetchall()
    conn.close()
    return [_row_to_product(r) for r in rows]


def get_product(code: str) -> Optional[Product]:
    conn = get_conn()
    cur = conn.cursor()
    row = cur.execute("SELECT * FROM products WHERE code = ?", (code,)).fetchone()
    conn.close()
    return _row_to_product(row) if row else None


def _row_to_product(r) -> Product:
    return Product(
        code=r["code"],
        name=r["name"],
        price=r["price"],
        category=r["category"],
        brand=r["brand"],
        stock_status=r["stock_status"],
        slug=r["slug"],
        image_url=r["image_url"],
        specs=json.loads(r["specs"]) if r["specs"] else {},
        description=r["description"],
        weight=r["weight"],
        updated_at=r["updated_at"],
    )


def count_products() -> int:
    conn = get_conn()
    cur = conn.cursor()
    count = cur.execute("SELECT COUNT(*) FROM products").fetchone()[0]
    conn.close()
    return count


def get_distinct_categories() -> list[str]:
    conn = get_conn()
    cur = conn.cursor()
    rows = cur.execute("SELECT DISTINCT category FROM products WHERE category != '' ORDER BY category").fetchall()
    conn.close()
    return [r[0] for r in rows]


def get_distinct_brands() -> list[str]:
    conn = get_conn()
    cur = conn.cursor()
    rows = cur.execute("SELECT DISTINCT brand FROM products WHERE brand != '' ORDER BY brand").fetchall()
    conn.close()
    return [r[0] for r in rows]
