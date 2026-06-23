import hashlib
import logging
import re
from typing import List, Optional

from bs4 import BeautifulSoup

from scrapers.base_scraper import BaseScraper
from models.news import NewsArticle

logger = logging.getLogger(__name__)


class NewsScraper(BaseScraper):
    async def scrape(self) -> List[NewsArticle]:
        html = await self.fetch(self.domain)
        if not html:
            return []

        soup = BeautifulSoup(html, "lxml")
        articles = self._parse_articles(soup)
        logger.info(f"Found {len(articles)} news articles on {self.domain}")
        return articles

    def _parse_articles(self, soup: BeautifulSoup) -> List[NewsArticle]:
        articles = []

        # Cari semua link yang mengarah ke artikel
        for a in soup.find_all("a", href=True):
            href = a["href"].strip()
            text = a.get_text(strip=True)

            if not text or len(text) < 15:
                continue

            # Filter: harus mirip judul artikel (bukan navigasi)
            if not self._looks_like_article(a, text):
                continue

            full_url = href if href.startswith("http") else f"{self.domain}{href}"
            news_id = hashlib.md5(full_url.encode()).hexdigest()[:12]

            # Cari thumbnail dari parent/child
            thumbnail = None
            img = a.find("img")
            if img:
                thumbnail = img.get("src") or img.get("data-src")

            # Coba cari tanggal
            date = None
            parent = a.parent
            for _ in range(3):
                if parent:
                    time_tag = parent.find("time")
                    if time_tag:
                        date = time_tag.get("datetime") or time_tag.get_text(strip=True)
                        break
                    # Cari elemen dengan class date
                    date_el = parent.find(class_=lambda c: c and any(
                        kw in c.lower() for kw in ["date", "tanggal", "time", "posted"]
                    ) if c else False)
                    if date_el:
                        date = date_el.get_text(strip=True)
                        break
                    parent = parent.parent
                else:
                    break

            articles.append(NewsArticle(
                news_id=news_id,
                title=text,
                url=full_url,
                date=date,
                excerpt=text[:200],
                thumbnail=thumbnail,
                source=self.domain,
            ))

        # Dedup by URL
        seen = set()
        unique = []
        for a in articles:
            if a.url not in seen:
                seen.add(a.url)
                unique.append(a)

        return unique

    def _looks_like_article(self, tag, text: str) -> bool:
        # Navigasi / menu → skip
        nav_keywords = ["home", "beranda", "about", "tentang", "contact", "kontak",
                        "faq", "privacy", "disclaimer", "login", "register", "download"]
        if text.lower().strip() in nav_keywords:
            return False

        # Terlalu pendek → skip (bukan judul artikel)
        if len(text) < 15:
            return False

        # Terlalu panjang → kemungkinan bukan judul
        if len(text) > 300:
            return False

        # Tag <a> di dalam <h1-6> / <strong> → kemungkinan besar judul
        parent_heading = tag.find_parent(["h1", "h2", "h3", "h4", "h5", "h6"])
        if parent_heading:
            return True

        # Tag di dalam <article> → kemungkinan artikel
        if tag.find_parent("article"):
            return True

        # Punya class indikatif
        cls = " ".join(tag.get("class", []))
        article_cls = ["title", "judul", "post", "article", "headline", "berita", "entry"]
        if any(kw in cls.lower() for kw in article_cls):
            return True

        # Anchor text mengandung keyword bola → hitung sebagai artikel
        bola_keywords = ["liga", "vs", "fc", "world cup", "champions", "premier",
                         "bundesliga", "serie a", "la liga", "timnas", "pemain",
                         "transfer", "skor", "pertandingan", "jadwal"]
        if any(kw in text.lower() for kw in bola_keywords):
            return True

        return False
