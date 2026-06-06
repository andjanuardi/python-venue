import requests
import json
import time
from datetime import datetime
from models import db, Product


API_BASE = "https://www.agres.id/api/search"
PER_PAGE = 50
REQUEST_DELAY = 0.3


def fetch_products_page(query="*", page=1, per_page=PER_PAGE):
    params = {
        "q": query,
        "page": page,
        "per_page": per_page,
        "filter_by": "price:>0",
    }
    try:
        resp = requests.get(API_BASE, params=params, timeout=30)
        resp.raise_for_status()
        return resp.json()
    except Exception as e:
        print(f"[ERROR] Page {page}: {e}")
        return None


def parse_and_save(data, stats):
    if not data or not data.get("success"):
        return stats

    payload = data["data"]
    hits = payload.get("hits", [])
    found = payload.get("found", 0)
    out_of = payload.get("out_of", 0)

    stats["total_available"] = out_of

    for hit in hits:
        try:
            product_id = hit.get("id")
            if not product_id:
                continue

            existing = Product.query.get(product_id)

            colors = hit.get("colors") or []
            sizes = hit.get("sizes") or []
            tags = hit.get("tags") or []
            image_urls = hit.get("image_urls") or []

            attrs = hit.get("attributes_kv") or []
            attrs_str = "\n".join(attrs) if attrs else None

            created_ts = hit.get("created_at")
            updated_ts = hit.get("updated_at")

            created_dt = (
                datetime.fromtimestamp(created_ts) if created_ts else datetime.utcnow()
            )
            updated_dt = (
                datetime.fromtimestamp(updated_ts) if updated_ts else datetime.utcnow()
            )

            data_dict = {
                "id": product_id,
                "title": hit.get("title", ""),
                "slug": hit.get("slug", ""),
                "sku": hit.get("sku"),
                "product_code": hit.get("product_code"),
                "brand": hit.get("brand"),
                "category_name": hit.get("category_name"),
                "category_id": hit.get("category_id"),
                "price": hit.get("price", 0),
                "discounted_price": hit.get("discounted_price"),
                "price_effective": hit.get("price_effective", 0),
                "has_discount": hit.get("has_discount", False),
                "short_description": hit.get("short_description"),
                "description": hit.get("description"),
                "image_primary": hit.get("image_primary"),
                "image_urls": "\n".join(image_urls) if image_urls else None,
                "in_stock": hit.get("in_stock", False),
                "quantity": hit.get("quantity", 0),
                "colors": ",".join(colors) if colors else None,
                "sizes": ",".join(sizes) if sizes else None,
                "tags": ",".join(tags) if tags else None,
                "weight": hit.get("weight"),
                "attributes_kv": attrs_str,
                "site": hit.get("site", "agres"),
                "created_at": created_dt,
                "updated_at": updated_dt,
                "scraped_at": datetime.utcnow(),
            }

            if existing:
                for key, val in data_dict.items():
                    if key != "scraped_at":
                        setattr(existing, key, val)
                existing.scraped_at = datetime.utcnow()
                stats["updated"] += 1
            else:
                product = Product(**data_dict)
                db.session.add(product)
                stats["created"] += 1

        except Exception as e:
            print(f"[ERROR] Processing product {hit.get('id', '?')}: {e}")
            stats["errors"] += 1

    db.session.commit()
    return stats


def scrape_all(callback=None):
    stats = {"created": 0, "updated": 0, "errors": 0, "total_available": 0, "scraped": 0}

    first_page = fetch_products_page(page=1)
    if not first_page:
        return stats

    stats = parse_and_save(first_page, stats)
    stats["scraped"] += len(first_page["data"].get("hits", []))
    if callback:
        callback(stats)

    total_out_of = first_page["data"].get("out_of", 0)
    total_pages = (total_out_of // PER_PAGE) + 1

    for page in range(2, total_pages + 1):
        time.sleep(REQUEST_DELAY)
        data = fetch_products_page(page=page)
        if data:
            stats = parse_and_save(data, stats)
            stats["scraped"] += len(data["data"].get("hits", []))
            if callback:
                callback(stats)

    return stats
