import csv
import io
import json
import threading
from datetime import datetime

from flask import (
    Flask,
    jsonify,
    render_template,
    request,
    Response,
    send_file,
)

from models import db, Product
from scraper import scrape_all as run_scrape

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///agres.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
db.init_app(app)

scrape_status = {"running": False, "progress": None, "done": False}


with app.app_context():
    db.create_all()


def parse_list(val):
    if not val:
        return []
    if isinstance(val, str):
        return [v.strip() for v in val.split(",") if v.strip()]
    return val


def get_filtered_products(args):
    query = Product.query

    search = args.get("search", "").strip()
    if search:
        like = f"%{search}%"
        query = query.filter(
            db.or_(
                Product.title.ilike(like),
                Product.sku.ilike(like),
                Product.product_code.ilike(like),
                Product.brand.ilike(like),
            )
        )

    category = args.get("category", "").strip()
    if category:
        query = query.filter(Product.category_name == category)

    brand = args.get("brand", "").strip()
    if brand:
        query = query.filter(Product.brand == brand)

    in_stock = args.get("in_stock", "").strip()
    if in_stock == "1":
        query = query.filter(Product.in_stock == True)
    elif in_stock == "0":
        query = query.filter(Product.in_stock == False)

    min_price = args.get("min_price", "").strip()
    if min_price:
        query = query.filter(Product.price_effective >= float(min_price))

    max_price = args.get("max_price", "").strip()
    if max_price:
        query = query.filter(Product.price_effective <= float(max_price))

    sort = args.get("sort", "updated_at")
    order = args.get("order", "desc")
    sort_col = getattr(Product, sort, Product.updated_at)
    if order == "asc":
        query = query.order_by(sort_col.asc())
    else:
        query = query.order_by(sort_col.desc())

    return query


@app.route("/")
def index():
    page = request.args.get("page", 1, type=int)
    per_page = request.args.get("per_page", 30, type=int)
    per_page = min(per_page, 200)

    q = get_filtered_products(request.args)
    total = q.count()
    pagination = q.paginate(page=page, per_page=per_page, error_out=False)

    categories = [
        r[0]
        for r in db.session.query(Product.category_name)
        .distinct()
        .order_by(Product.category_name)
        .all()
        if r[0]
    ]
    brands = [
        r[0]
        for r in db.session.query(Product.brand)
        .distinct()
        .order_by(Product.brand)
        .all()
        if r[0]
    ]

    stats = {
        "total_products": Product.query.count(),
        "in_stock": Product.query.filter(Product.in_stock == True).count(),
        "categories": len(categories),
        "brands": len(brands),
    }

    return render_template(
        "index.html",
        products=pagination.items,
        page=page,
        per_page=per_page,
        total=total,
        pages=pagination.pages,
        categories=categories,
        brands=brands,
        stats=stats,
        request_args=request.args,
        url_for_with_args=lambda **kw: _url_for_with_args(request.args, kw),
    )


@app.route("/product/<slug>")
def product_detail(slug):
    product = Product.query.filter_by(slug=slug).first_or_404()
    attrs = []
    if product.attributes_kv:
        for line in product.attributes_kv.strip().split("\n"):
            if ":" in line:
                k, v = line.split(":", 1)
                attrs.append((k.strip(), v.strip()))

    related = (
        Product.query.filter(
            Product.category_name == product.category_name,
            Product.id != product.id,
        )
        .order_by(Product.updated_at.desc())
        .limit(6)
        .all()
    )

    return render_template("detail.html", product=product, attrs=attrs, related=related)


@app.route("/api/products")
def api_products():
    page = request.args.get("page", 1, type=int)
    per_page = request.args.get("per_page", 30, type=int)
    per_page = min(per_page, 200)

    q = get_filtered_products(request.args)
    total = q.count()
    pagination = q.paginate(page=page, per_page=per_page, error_out=False)

    return jsonify(
        {
            "success": True,
            "data": {
                "hits": [p.to_dict() for p in pagination.items],
                "total": total,
                "page": page,
                "per_page": per_page,
                "pages": pagination.pages,
            },
        }
    )


@app.route("/scrape", methods=["POST"])
def trigger_scrape():
    global scrape_status

    if scrape_status["running"]:
        return jsonify({"success": False, "error": "Scraping already in progress"}), 400

    def progress_callback(stats):
        global scrape_status
        scrape_status["progress"] = stats

    def run():
        global scrape_status
        scrape_status["running"] = True
        scrape_status["done"] = False
        scrape_status["progress"] = None
        try:
            result = run_scrape(callback=progress_callback)
            scrape_status["progress"] = result
        except Exception as e:
            scrape_status["progress"] = {"error": str(e)}
        finally:
            scrape_status["running"] = False
            scrape_status["done"] = True

    thread = threading.Thread(target=run, daemon=True)
    thread.start()

    return jsonify({"success": True, "message": "Scraping started"})


@app.route("/scrape/status")
def scrape_status_endpoint():
    return jsonify(
        {
            "running": scrape_status["running"],
            "done": scrape_status["done"],
            "progress": scrape_status["progress"],
        }
    )


@app.route("/export")
def export_csv():
    q = get_filtered_products(request.args)
    products = q.order_by(Product.updated_at.desc()).all()

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(
        [
            "Title",
            "Brand",
            "Category",
            "SKU",
            "Price",
            "Discounted Price",
            "Price Effective",
            "In Stock",
            "Quantity",
            "Slug",
            "Image URL",
        ]
    )
    for p in products:
        writer.writerow(
            [
                p.title,
                p.brand,
                p.category_name,
                p.sku,
                p.price,
                p.discounted_price,
                p.price_effective,
                "Yes" if p.in_stock else "No",
                p.quantity,
                p.slug,
                p.image_primary,
            ]
        )

    mem = io.BytesIO()
    mem.write(output.getvalue().encode("utf-8-sig"))
    mem.seek(0)

    return send_file(
        mem,
        mimetype="text/csv",
        as_attachment=True,
        download_name=f"agres_products_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
    )


@app.route("/stats")
def stats_json():
    total = Product.query.count()
    in_stock = Product.query.filter(Product.in_stock == True).count()
    out_of_stock = total - in_stock

    brand_counts = {}
    for r in db.session.query(Product.brand, db.func.count(Product.id)).group_by(
        Product.brand
    ).all():
        if r[0]:
            brand_counts[r[0]] = r[1]

    cat_counts = {}
    for r in db.session.query(
        Product.category_name, db.func.count(Product.id)
    ).group_by(Product.category_name).all():
        if r[0]:
            cat_counts[r[0]] = r[1]

    return jsonify(
        {
            "total_products": total,
            "in_stock": in_stock,
            "out_of_stock": out_of_stock,
            "brands": len(brand_counts),
            "categories": len(cat_counts),
            "brand_counts": dict(
                sorted(brand_counts.items(), key=lambda x: -x[1])[:30]
            ),
            "category_counts": dict(
                sorted(cat_counts.items(), key=lambda x: -x[1])
            ),
        }
    )


def _url_for_with_args(args, overrides):
    d = {k: v for k, v in args.items()}
    for k, v in overrides.items():
        d[k] = str(v) if v else ""
    qs = "&".join(f"{k}={v}" for k, v in d.items() if v)
    return f"/?{qs}" if qs else "/"


@app.template_filter("number_format")
def number_format_filter(n):
    if n is None:
        return "0"
    return f"{n:,}"


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
