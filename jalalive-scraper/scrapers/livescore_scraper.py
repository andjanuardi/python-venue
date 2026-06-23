import hashlib
import logging
import re
from typing import List, Optional

import httpx
from bs4 import BeautifulSoup

from config.settings import settings
from models.match import Match
from scrapers.base_scraper import BaseScraper

logger = logging.getLogger(__name__)

# Fallback free API as backup
FOOTBALL_DATA_API = "https://api.football-data.org/v4"


class LivescoreScraper(BaseScraper):
    def __init__(self, domain: str = None, football_api_key: str = None):
        super().__init__(domain=domain)
        self.api_key = football_api_key

    async def scrape_google(self, match: Match) -> Match:
        """Parse livescore dari Google search result (Knowledge Graph)"""
        query = f"{match.home_team} {match.away_team} skor"
        url = f"https://www.google.com/search?q={query.replace(' ', '+')}"

        html = await self.fetch(url)
        if not html:
            logger.debug(f"No HTML from Google for {match.home_team} vs {match.away_team}")
            return match

        soup = BeautifulSoup(html, "lxml")

        # Try to find score in Google Knowledge Panel
        score = self._extract_google_score(soup)
        if score:
            match.home_score = score.get("home")
            match.away_score = score.get("away")
            match.status = score.get("status", match.status)

        return match

    def _extract_google_score(self, soup: BeautifulSoup) -> Optional[dict]:
        result = {}

        # Pattern 1: div with score data (most common)
        score_div = soup.find("div", class_=lambda c: c and any(
            kw in " ".join(c).lower() for kw in ["imso-hov", "imso-score", "score"]
        ) if c else False)

        if score_div:
            spans = score_div.find_all("span")
            nums = [s.get_text(strip=True) for s in spans if s.get_text(strip=True).isdigit()]
            if len(nums) >= 2:
                result["home"] = int(nums[0])
                result["away"] = int(nums[1])

        # Pattern 2: Knowledge Panel score text (e.g. "2 - 1")
        if "home" not in result:
            for div in soup.find_all("div"):
                text = div.get_text(strip=True)
                match_score = re.match(r'(\d+)\s*[-–:]\s*(\d+)', text)
                if match_score:
                    # Verify this is in a sports context
                    parent_text = (div.parent.get_text(strip=True) if div.parent else "").lower()
                    if any(kw in parent_text for kw in ["goal", "skor", "score", "football", "bola"]):
                        result["home"] = int(match_score.group(1))
                        result["away"] = int(match_score.group(2))
                        break

        # Pattern 3: Try to find "LIVE" / "HALFTIME" / "FT" status
        for div in soup.find_all(["div", "span"]):
            text = div.get_text(strip=True).upper()
            if text in ("LIVE", "HALFTIME", "HT", "FT", "FULL TIME", "SELESAI"):
                result["status"] = text.lower()
                break

        if "home" in result:
            result.setdefault("status", "live")
            return result

        return None

    async def scrape_api(self, match: Match) -> Match:
        """Fallback menggunakan football-data.org API"""
        if not self.api_key:
            return match

        # Search for match by team names
        try:
            async with httpx.AsyncClient(
                base_url=FOOTBALL_DATA_API,
                headers={"X-Auth-Token": self.api_key},
                timeout=10,
            ) as client:
                # Get matches for today
                resp = await client.get("/matches")
                if resp.status_code != 200:
                    return match

                data = resp.json()
                for m in data.get("matches", []):
                    home = m.get("homeTeam", {}).get("name", "").lower()
                    away = m.get("awayTeam", {}).get("name", "").lower()
                    if match.home_team.lower() in home and match.away_team.lower() in away:
                        score = m.get("score", {})
                        full_time = score.get("fullTime", {})
                        match.home_score = full_time.get("home")
                        match.away_score = full_time.get("away")
                        match.status = m.get("status", "").lower()
                        break
        except Exception as e:
            logger.debug(f"API fallback error: {e}")

        return match

    async def scrape_many(self, matches: List[Match]) -> List[Match]:
        """Update livescore untuk semua match yang diberikan"""
        updated = []
        for match in matches:
            try:
                # Primary: Google scrape
                match = await self.scrape_google(match)
                updated.append(match)
            except Exception as e:
                logger.warning(f"Livescore error for {match.match_id}: {e}")
                updated.append(match)
        return updated
