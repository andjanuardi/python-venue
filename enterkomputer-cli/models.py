from dataclasses import dataclass, field
from typing import Optional


@dataclass
class Category:
    id: int
    name: str
    slug: str
    product_count: int = 0


@dataclass
class Brand:
    name: str
    product_count: int = 0


@dataclass
class Product:
    code: str
    name: str
    price: int
    category: str
    brand: str
    stock_status: str
    slug: str
    image_url: str = ""
    specs: dict = field(default_factory=dict)
    description: str = ""
    weight: str = ""
    updated_at: str = ""
