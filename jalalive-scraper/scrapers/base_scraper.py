import asyncio
import random
import logging
from typing import Optional, List

import httpx
from fake_useragent import UserAgent

from config.settings import settings

logger = logging.getLogger(__name__)

ua = UserAgent()


class BaseScraper:
    def __init__(self, domain: Optional[str] = None):
        self.domain = domain or settings.PRIMARY_DOMAIN
        self.timeout = settings.REQUEST_TIMEOUT

    def _get_headers(self) -> dict:
        return {
            "User-Agent": random.choice(settings.USER_AGENTS),
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "id-ID,id;q=0.9,en-US;q=0.8,en;q=0.7",
            "Referer": self.domain,
            "DNT": "1",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1",
        }

    async def fetch(self, url: str) -> Optional[str]:
        for attempt in range(1, settings.RETRY_COUNT + 1):
            try:
                async with httpx.AsyncClient(
                    headers=self._get_headers(),
                    timeout=self.timeout,
                    follow_redirects=True,
                ) as client:
                    logger.info(f"Fetching [{attempt}/{settings.RETRY_COUNT}]: {url}")
                    resp = await client.get(url)
                    resp.raise_for_status()
                    logger.info(f"Got response {resp.status_code} ({len(resp.text)} bytes)")
                    return resp.text
            except httpx.HTTPStatusError as e:
                logger.warning(f"HTTP error for {url}: {e.response.status_code}")
                if attempt < settings.RETRY_COUNT:
                    await asyncio.sleep(settings.RETRY_DELAY * attempt)
            except httpx.RequestError as e:
                logger.warning(f"Request error for {url}: {e}")
                if attempt < settings.RETRY_COUNT:
                    await asyncio.sleep(settings.RETRY_DELAY * attempt)
        logger.error(f"Failed to fetch {url} after {settings.RETRY_COUNT} attempts")
        return None

    def build_url(self, path: str = "") -> str:
        return f"{self.domain.rstrip('/')}/{path.lstrip('/')}"
