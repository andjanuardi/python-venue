import hashlib
import logging
import re
from typing import List, Optional

from bs4 import BeautifulSoup

from config.settings import settings
from scrapers.base_scraper import BaseScraper
from models.match import Match

logger = logging.getLogger(__name__)


class ScheduleScraper(BaseScraper):
    async def scrape(self) -> List[Match]:
        html = await self.fetch(self.domain)
        if not html:
            logger.warning(f"No HTML from {self.domain}")
            return []

        soup = BeautifulSoup(html, "lxml")

        # Use domain-specific parser if available
        domain_key = self.domain.replace("https://", "").replace("http://", "").rstrip("/")
        parser_method = getattr(self, f"_parse_{domain_key.replace('.', '_')}", None)
        if parser_method:
            matches = parser_method(soup)
        else:
            matches = self._parse_generic(soup)

        logger.info(f"Found {len(matches)} matches on {self.domain}")
        return matches

    # ─── reboundac.com ────────────────────────────────────────────
    def _parse_reboundac_com(self, soup: BeautifulSoup) -> List[Match]:
        matches = []
        container = soup.select_one("div.grid.grid-cols-1")
        if not container:
            return self._parse_generic(soup)

        cards = container.select("div.glass-dark")
        for card in cards:
            try:
                flex_items = card.find_all("div", class_="flex-1")
                if len(flex_items) < 2:
                    continue

                # League / group
                group_tag = flex_items[0].select_one("p.text-emerald-500")
                league = group_tag.get_text(strip=True) if group_tag else None

                # Teams — use text-xl to specifically target team names
                home_tag = flex_items[0].select_one("p.text-xl")
                away_tag = flex_items[1].select_one("p.text-xl")
                home_team = home_tag.get_text(strip=True) if home_tag else "Unknown"
                away_team = away_tag.get_text(strip=True) if away_tag else "Unknown"

                # Time
                time_span = card.select_one("span.text-3xl")
                time_val = time_span.get_text(strip=True) if time_span else None

                match_id = hashlib.md5(f"{home_team}{away_team}{time_val}{self.domain}".encode()).hexdigest()[:12]

                matches.append(Match(
                    match_id=match_id,
                    home_team=home_team,
                    away_team=away_team,
                    time=time_val,
                    league=league,
                    domain=self.domain,
                ))
            except Exception as e:
                logger.debug(f"Error parsing card: {e}")
                continue

        return matches

    # ─── jalalive.cc / blog-style ─────────────────────────────────
    def _parse_jalalive_cc(self, soup: BeautifulSoup) -> List[Match]:
        return self._parse_generic(soup)

    # ─── Generic fallback ─────────────────────────────────────────
    def _parse_generic(self, soup: BeautifulSoup) -> List[Match]:
        matches = []
        items = self._find_match_items(soup)

        for item in items:
            match = self._extract_match(item)
            if match:
                matches.append(match)

        return matches

    def _find_match_items(self, soup: BeautifulSoup) -> list:
        candidates = soup.find_all(["article", "tr", "li", "div"])
        scored = []
        for el in candidates:
            text = el.get_text(strip=True)
            if len(text) < 20:
                continue
            score = 0
            if el.find(["time", "span", "strong"]):
                score += 1
            if el.find("a"):
                score += 1
            lower = text.lower()
            keywords = ["vs", "fc", "live", "stream", "nonton", " - ", ":",
                        "premier", "liga", "champions", "world cup"]
            score += sum(1 for kw in keywords if kw in lower)
            if score >= 3:
                scored.append((score, el))
        scored.sort(key=lambda x: x[0], reverse=True)
        return [el for _, el in scored[:50]]

    def _extract_match(self, item) -> Optional[Match]:
        try:
            text = item.get_text(" ", strip=True)
            links = item.find_all("a", href=True)
            detail_url = None
            for a in links:
                href = a["href"]
                if href.startswith("/") or href.startswith("http"):
                    detail_url = href if href.startswith("http") else f"{self.domain}{href}"
                    break

            lines = [l.strip() for l in text.split() if l.strip()]
            if len(lines) < 2:
                return None

            match_id = hashlib.md5(f"{text}{self.domain}".encode()).hexdigest()[:12]
            match = Match(
                match_id=match_id,
                home_team=lines[0] if len(lines) > 0 else "Unknown",
                away_team=lines[-1] if len(lines) > 1 else "Unknown",
                detail_url=detail_url,
                domain=self.domain,
            )
            time_tag = item.find("time")
            if time_tag:
                match.date = time_tag.get("datetime") or time_tag.get_text(strip=True)
            for span in item.find_all(["span", "div"]):
                cls = " ".join(span.get("class", []))
                txt = span.get_text(strip=True)
                if not txt:
                    continue
                lower_cls = cls.lower()
                if "date" in lower_cls or "tanggal" in lower_cls:
                    match.date = txt
                elif "time" in lower_cls or "jam" in lower_cls or "kickoff" in lower_cls:
                    match.time = txt
                elif "league" in lower_cls or "liga" in lower_cls or "competition" in lower_cls:
                    match.league = txt
            return match
        except Exception as e:
            logger.debug(f"Error parsing match item: {e}")
            return None
