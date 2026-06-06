from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()


class Product(db.Model):
    __tablename__ = "products"

    id = db.Column(db.String(64), primary_key=True)
    title = db.Column(db.String(500), nullable=False)
    slug = db.Column(db.String(500), unique=True, nullable=False)
    sku = db.Column(db.String(100))
    product_code = db.Column(db.String(100))
    brand = db.Column(db.String(200))
    category_name = db.Column(db.String(200))
    category_id = db.Column(db.Integer)
    price = db.Column(db.Float)
    discounted_price = db.Column(db.Float, nullable=True)
    price_effective = db.Column(db.Float)
    has_discount = db.Column(db.Boolean, default=False)
    short_description = db.Column(db.Text)
    description = db.Column(db.Text)
    image_primary = db.Column(db.String(500))
    image_urls = db.Column(db.Text)
    in_stock = db.Column(db.Boolean, default=True)
    quantity = db.Column(db.Integer, default=0)
    colors = db.Column(db.String(500))
    sizes = db.Column(db.String(500))
    tags = db.Column(db.String(500))
    weight = db.Column(db.Float, nullable=True)
    attributes_kv = db.Column(db.Text)
    site = db.Column(db.String(50), default="agres")
    created_at = db.Column(db.DateTime)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow)
    scraped_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "title": self.title,
            "slug": self.slug,
            "sku": self.sku,
            "product_code": self.product_code,
            "brand": self.brand,
            "category_name": self.category_name,
            "price": self.price,
            "discounted_price": self.discounted_price,
            "price_effective": self.price_effective,
            "has_discount": self.has_discount,
            "short_description": self.short_description,
            "description": self.description,
            "image_primary": self.image_primary,
            "in_stock": self.in_stock,
            "quantity": self.quantity,
            "colors": self.colors.split(",") if self.colors else [],
            "sizes": self.sizes.split(",") if self.sizes else [],
            "tags": self.tags.split(",") if self.tags else [],
            "weight": self.weight,
            "attributes_kv": self.attributes_kv,
            "category_id": self.category_id,
            "site": self.site,
        }
