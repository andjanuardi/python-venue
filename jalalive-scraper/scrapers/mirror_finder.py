import asyncio
import logging
import re
from typing import List, Optional

import httpx
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)


class MirrorFinder:
    SEARCH_URLS = [
        "https://www.google.com/search?q={query}",
        "https://www.bing.com/search?q={query}",
    ]

    SEARCH_QUERIES = [
        "jalas30 link alternatif",
        "jalalive domain baru",
        "jalalive nonton bola",
        "jalalive live streaming",
        "site:jala*.com jalalive",
    ]

    PATTERN = re.compile(r'https?://(?:www\.)?(jalalive|jalaace|jalas\d+|jalalivebola)[^"\'\s<>]*', re.I)

    def __init__(self, known_domains: List[str] = None):
        self.known_domains = set(known_domains or [])
        self.discovered: List[str] = []

    async def search(self, query: str, engine_url: str) -> List[str]:
        found = []
        try:
            url = engine_url.format(query=query.replace(" ", "+"))
            async with httpx.AsyncClient(
                timeout=15,
                follow_redirects=True,
                headers={
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                                  "AppleWebKit/537.36 (KHTML, like Gecko) "
                                  "Chrome/125.0.0.0 Safari/537.36",
                    "Accept": "text/html,application/xhtml+xml",
                },
            ) as client:
                resp = await client.get(url)
                if resp.status_code != 200:
                    return []

                text = resp.text
                matches = self.PATTERN.findall(text)
                # Fix: PATTERN captures the full URL, not just group
                for m in self.PATTERN.finditer(text):
                    domain_url = m.group(0).rstrip("/")
                    if domain_url not in self.known_domains and domain_url not in found:
                        found.append(domain_url)

        except Exception as e:
            logger.debug(f"Mirror search error ({engine_url}): {e}")

        return found

    async def find_all(self) -> List[str]:
        all_found = []
        for query in self.SEARCH_QUERIES:
            for engine in self.SEARCH_URLS:
                found = await self.search(query, engine)
                all_found.extend(found)
                await asyncio.sleep(1.5)  # be polite

        # Dedup
        unique = list(dict.fromkeys(all_found))
        self.discovered = [u for u in unique if u not in self.known_domains]
        logger.info(f"MirrorFinder: discovered {len(self.discovered)} new domains")
        return self.discovered

    async def validate(self, url: str) -> bool:
        try:
            async with httpx.AsyncClient(timeout=10, follow_redirects=True) as client:
                resp = await client.get(url, headers={
                    "User-Agent": "Mozilla/5.0",
                })
                if resp.status_code == 200:
                    # Check if it looks like a JalaLive page
                    soup = BeautifulSoup(resp.text, "lxml")
                    text = soup.get_text().lower()
                    keywords = ["jalalive", "j alalive", "nonton bola", "live streaming", "jala live"]
                    if any(kw in text for kw in keywords):
                        return True
                    # Also check if title contains relevant keywords
                    title = soup.title.string.lower() if soup.title else ""
                    if "jalalive" in title or "jala" in title:
                        return True
            return False
        except Exception:
            return False
