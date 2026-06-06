import json
import logging
import os
import re
import time
from pathlib import Path
from typing import Optional
from urllib.parse import urlparse

from bs4 import BeautifulSoup

from models import Product, Category

BASE_URL = "https://www.enterkomputer.com"
API_URL = f"{BASE_URL}/jeanne/v2/product-list"
COOKIE_FILE = Path(".ek_cookies.json")

KCODE_RE = re.compile(r"/category/(\d+)/")
TOKEN_RE = re.compile(r'data-api-token="([^"]+)"')
SIGNATURE_RE = re.compile(r'data-api-signature="([^"]+)"')

logger = logging.getLogger(__name__)


def _parse_api_item(item: dict, category: str = "") -> Product:
    price = 0
    try:
        price = int(item.get("PPRCZ", [0])[0])
    except (ValueError, IndexError, TypeError):
        price = 0

    stock = "ready" if item.get("PSTTS") == 0 else "unknown"
    brand = item.get("BNAME", "") or item.get("BRAND", "")

    return Product(
        code=str(item.get("PCODE", "")),
        name=item.get("PNAME", ""),
        price=price,
        category=category,
        brand=brand,
        stock_status=stock,
        slug=item.get("PLINK", ""),
        image_url=item.get("PIMGZ", [""])[0] if item.get("PIMGZ") else "",
    )


def parse_products_from_api(data: dict, category: str = "") -> list[Product]:
    results = []
    if not data or not data.get("status"):
        return results
    for pprnt in data.get("result", []):
        for pchld in pprnt.get("PPRNT", []):
            for pc in pchld.get("PCHLD", []):
                for p in pc.get("PLIST", []):
                    if isinstance(p, dict):
                        results.append(_parse_api_item(p, category))
    return results


class EnterkomputerScraper:
    def __init__(self):
        self.session: Optional["Session"] = None
        self.api_token: Optional[str] = None
        self.api_signature: Optional[str] = None
        self.cookies: dict[str, str] = {}

    def load_cookies_from_file(self) -> bool:
        if COOKIE_FILE.exists():
            try:
                data = json.loads(COOKIE_FILE.read_text())
                self.cookies = data.get("cookies", {})
                self.api_token = data.get("token")
                self.api_signature = data.get("signature")
                return bool(self.cookies.get("cf_clearance"))
            except (json.JSONDecodeError, KeyError):
                pass
        return False

    def save_cookies_to_file(self):
        COOKIE_FILE.write_text(json.dumps({
            "cookies": self.cookies,
            "token": self.api_token,
            "signature": self.api_signature,
        }, indent=2))

    def _init_session(self):
        if self.session is not None:
            return
        from curl_cffi import requests as cf_requests

        self.session = cf_requests.Session(impersonate="chrome120")
        self.session.headers.update({
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/120.0.0.0 Safari/537.36"
            ),
        })
        domain = "." + urlparse(BASE_URL).netloc.lstrip("www.")
        for k, v in self.cookies.items():
            self.session.cookies.set(k, v, domain=domain)

    def set_credentials(self, cf_clearance: str, token: str, signature: str,
                        user_agent: str = ""):
        self.cookies["cf_clearance"] = cf_clearance
        self.api_token = token
        self.api_signature = signature
        self.session = None
        if user_agent:
            pass
        self.save_cookies_to_file()

    def has_credentials(self) -> bool:
        return bool(self.cookies.get("cf_clearance") and self.api_token and self.api_signature)

    # ---- API Calls ----

    def fetch_sitemap(self) -> Optional[str]:
        self._init_session()
        try:
            r = self.session.get(f"{BASE_URL}/sitemap.xml", timeout=30)
            if r.status_code == 200:
                return r.text
        except Exception as e:
            logger.warning("Sitemap fetch failed: %s", e)
        return None

    def fetch_api_credentials(self, category_url: str) -> bool:
        self._init_session()
        try:
            r = self.session.get(category_url, timeout=30)
            if r.status_code != 200:
                return False
            token_m = TOKEN_RE.search(r.text)
            sig_m = SIGNATURE_RE.search(r.text)
            if token_m and sig_m:
                self.api_token = token_m.group(1)
                self.api_signature = sig_m.group(1)
                self.save_cookies_to_file()
                return True
        except Exception as e:
            logger.warning("Credential fetch failed: %s", e)
        return False

    def fetch_product_page(self, kcode: str, page: int = 1,
                           keyword: str = "", referer: str = "") -> Optional[dict]:
        self._init_session()
        payload = {
            "KCODE": kcode,
            "SCODE": "all",
            "BCODE": "all",
            "BNAME": "",
            "MORDR": "default",
            "MSTGE": "mapping",
            "MKYWD": keyword,
            "MTAGS": "",
            "MSGMN": "category",
            "MPAGE": str(page),
            "token": self.api_token or "",
            "signature": self.api_signature or "",
        }
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json, text/plain, */*",
            "Origin": BASE_URL,
            "Referer": referer or f"{BASE_URL}/",
            "X-Requested-With": "XMLHttpRequest",
        }
        try:
            r = self.session.post(API_URL, json=payload, headers=headers, timeout=30)
            if r.status_code == 200:
                return r.json()
        except Exception as e:
            logger.warning("API fetch failed: %s", e)
        return None

    def fetch_product_detail(self, pcode: str, slug: str = "") -> Optional[Product]:
        if not slug:
            slug = pcode
        url = f"{BASE_URL}/detail/{pcode}/{slug}"
        self._init_session()
        try:
            r = self.session.get(url, timeout=30)
            if r.status_code != 200:
                return None
            soup = BeautifulSoup(r.text, "lxml")
            ctx_node = soup.select_one("div.context-json")
            if not ctx_node:
                return None
            raw = ctx_node.get_text(strip=True)
            if not raw:
                return None
            data = json.loads(raw)
            price = 0
            try:
                price = int(data.get("PPRCZ", [0])[0])
            except (ValueError, IndexError, TypeError):
                price = 0
            stock = "ready" if data.get("PDISP") == 1 else "empty"
            specs = {}
            spec_table = soup.select_one("table.specs-table")
            if spec_table:
                for row in spec_table.select("tr"):
                    cells = row.select("td")
                    if len(cells) >= 2:
                        key = cells[0].get_text(strip=True)
                        val = cells[1].get_text(strip=True)
                        if key:
                            specs[key] = val

            desc = ""
            meta_desc = (
                soup.select_one('meta[property="og:description"]')
                or soup.select_one('meta[name="description"]')
            )
            if meta_desc:
                desc = meta_desc.get("content", "")

            cat_el = soup.select_one("p.product-category a")
            category = cat_el.get_text(strip=True) if cat_el else ""

            return Product(
                code=str(data.get("PCODE", pcode)),
                name=data.get("PNAME", ""),
                price=price,
                category=category,
                brand="",
                stock_status=stock,
                slug=data.get("PLINK", slug),
                image_url=data.get("PIMGZ", [""])[0] if data.get("PIMGZ") else "",
                specs=specs,
                description=desc,
            )
        except Exception as e:
            logger.warning("Detail fetch failed for %s: %s", pcode, e)
        return None

    # ---- Category helpers ----

    def get_categories_from_sitemap(self, sitemap_xml: str) -> list[Category]:
        categories: dict[int, Category] = {}
        for match in KCODE_RE.finditer(sitemap_xml):
            cid = int(match.group(1))
            if cid not in categories:
                slug = match.group(0).rstrip("/").split("/")[-1]
                name = slug.replace("-", " ").title()
                categories[cid] = Category(id=cid, name=name, slug=slug)
        if not categories:
            return self._fallback_categories()
        return list(categories.values())

    def _fallback_categories(self) -> list[Category]:
        known = [
            (17, "Processor"), (12, "Motherboard"), (24, "VGA"),
            (6, "Hard Drive"), (101, "SSD"), (11, "Memory RAM"),
            (19, "PSU"), (3, "Casing"), (9, "Monitor"), (8, "Keyboard"),
            (4, "Cooler"), (5, "Printer"), (20, "Software"),
            (14, "Notebook"), (1, "Accessories"), (21, "Gadget"),
            (13, "Networking"), (15, "Server"), (18, "Speaker"),
            (16, "Projector"), (22, "Gaming Chair"), (23, "Mouse"),
            (7, "Headset"),
        ]
        return [
            Category(id=cid, name=name, slug=name.lower().replace(" ", "-"))
            for cid, name in known
        ]

    def try_nodriver_bypass(self) -> bool:
        """Attempt Cloudflare bypass using nodriver (requires Chrome)."""
        try:
            import asyncio
            import nodriver as uc
            from nodriver.cdp import network
            from nodriver.cdp import storage

            original = network.Cookie.from_json
            def patched_cookie(json_dict):
                json_dict.setdefault("sameParty", False)
                return original(json_dict)
            network.Cookie.from_json = staticmethod(patched_cookie)

            chrome_candidates = [
                os.environ.get("CHROME_PATH", ""),
                "/tmp/chrome-linux64-extracted/chrome-linux64/chrome",
            ]
            chrome_path = next((p for p in chrome_candidates if p and Path(p).exists()), "")

            async def _bypass():
                kwargs = {"headless": False}
                if chrome_path:
                    kwargs["browser_executable_path"] = chrome_path
                    kwargs["browser_args"] = ["--window-position=-2400,-2400", "--window-size=1280,800"]

                browser = await uc.start(**kwargs)
                try:
                    page = browser.tabs[0] if browser.tabs else await browser.get("about:blank")
                    await page.get(BASE_URL)

                    cleared = False
                    for i in range(35):
                        await asyncio.sleep(1)
                        try:
                            title = await page.evaluate("document.title")
                            if title and "Just a moment" not in title:
                                cleared = True
                                break
                        except Exception:
                            pass

                    if not cleared:
                        return False

                    cookies_list = await page.send(storage.get_cookies())
                    self.cookies = {c.name: c.value for c in cookies_list}

                    await page.get(f"{BASE_URL}/category/17/processor")
                    await asyncio.sleep(3)

                    token = await page.evaluate(
                        'document.querySelector("[data-api-token]")?.getAttribute("data-api-token")'
                    )
                    sig = await page.evaluate(
                        'document.querySelector("[data-api-signature]")?.getAttribute("data-api-signature")'
                    )
                    self.api_token = token
                    self.api_signature = sig
                    return bool(self.cookies.get("cf_clearance") and self.api_token)
                finally:
                    browser.stop()

            return asyncio.run(_bypass())
        except Exception as e:
            logger.warning("nodriver bypass failed: %s", e)
            return False
