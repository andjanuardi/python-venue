import logging
from typing import List, Optional

from bs4 import BeautifulSoup

from scrapers.base_scraper import BaseScraper
from models.stream import StreamLink
from models.match import Match

logger = logging.getLogger(__name__)


class StreamScraper(BaseScraper):
    async def scrape_match(self, match: Match) -> List[StreamLink]:
        url = match.detail_url
        if not url:
            logger.debug(f"No detail URL for match {match.match_id}")
            return []

        html = await self.fetch(url)
        if not html:
            return []

        soup = BeautifulSoup(html, "lxml")
        links = self._extract_stream_links(soup, match.match_id)
        logger.info(f"Found {len(links)} stream links for match {match.match_id}")
        return links

    async def scrape_matches(self, matches: List[Match]) -> List[StreamLink]:
        all_links = []
        for match in matches:
            links = await self.scrape_match(match)
            all_links.extend(links)
        return all_links

    def _extract_stream_links(self, soup: BeautifulSoup, match_id: str) -> List[StreamLink]:
        links = []

        # 1. Cari iframe (sumber streaming utama)
        iframes = soup.find_all("iframe", src=True)
        for iframe in iframes:
            src = iframe["src"].strip()
            if src and not src.startswith("javascript"):
                links.append(StreamLink(
                    match_id=match_id,
                    url=src,
                    type="iframe",
                    domain=self.domain,
                ))

        # 2. Cari anchor dengan href mengarah ke stream
        for a in soup.find_all("a", href=True):
            href = a["href"].strip()
            if not href or href.startswith("#") or href.startswith("javascript"):
                continue
            lower = href.lower()
            keywords = ["youtube", "stream", "live", "redirect", "play", "watch"]
            if any(kw in lower for kw in keywords):
                label = a.get_text(strip=True) or None
                links.append(StreamLink(
                    match_id=match_id,
                    url=href if href.startswith("http") else f"{self.domain}{href}",
                    type="redirect",
                    label=label,
                    domain=self.domain,
                ))

        # 3. Cari elemen dengan class/ID indikatif stream
        for div in soup.find_all(["div", "section"], class_=lambda c: c and any(
            kw in " ".join(c).lower() for kw in ["stream", "player", "video", "embed"]
        )):
            inner_iframes = div.find_all("iframe", src=True)
            for iframe in inner_iframes:
                src = iframe["src"].strip()
                if src and not any(l.url == src for l in links):
                    links.append(StreamLink(
                        match_id=match_id,
                        url=src,
                        type="iframe",
                        domain=self.domain,
                    ))

        return links
