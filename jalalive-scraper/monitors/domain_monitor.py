import asyncio
import logging
from datetime import datetime
from typing import Dict, List, Optional

import httpx
import yaml

from config.settings import settings

logger = logging.getLogger(__name__)


class DomainMonitor:
    def __init__(self, config_path: str = None):
        self.config_path = config_path or settings.DOMAINS_CONFIG_PATH
        self.domains: List[Dict] = []
        self._load()

    def _load(self):
        try:
            with open(self.config_path) as f:
                data = yaml.safe_load(f)
                self.domains = data.get("domains", [])
            logger.info(f"Loaded {len(self.domains)} domains from config")
        except FileNotFoundError:
            logger.warning(f"Domain config not found: {self.config_path}")
            self.domains = []

    def _save(self):
        with open(self.config_path, "w") as f:
            yaml.dump({"domains": self.domains}, f, default_flow_style=False, allow_unicode=True)

    def get_active_domains(self) -> List[Dict]:
        return [d for d in self.domains if d.get("status") == "active"]

    def get_first_active(self) -> Optional[Dict]:
        active = self.get_active_domains()
        # Prefer schedule type
        for d in active:
            if d.get("type") == "schedule":
                return d
        return active[0] if active else None

    async def check_domain(self, domain: Dict) -> str:
        url = domain["url"]
        try:
            async with httpx.AsyncClient(timeout=10, follow_redirects=True) as client:
                resp = await client.get(url, headers={
                    "User-Agent": "Mozilla/5.0 (compatible; JalaLiveMonitor/1.0)",
                    "Accept": "text/html",
                })
                if resp.status_code == 200:
                    domain["status"] = "active"
                    domain["last_check"] = datetime.utcnow().isoformat()
                    return "active"
                elif resp.status_code in (403, 429):
                    domain["status"] = "rate_limited"
                    domain["last_check"] = datetime.utcnow().isoformat()
                    return "rate_limited"
                else:
                    domain["status"] = "dead"
                    domain["last_check"] = datetime.utcnow().isoformat()
                    return "dead"
        except Exception as e:
            logger.warning(f"Health check failed for {url}: {e}")
            domain["status"] = "dead"
            domain["last_check"] = datetime.utcnow().isoformat()
            return "dead"

    async def check_all(self) -> Dict[str, str]:
        results = {}
        for domain in self.domains:
            status = await self.check_domain(domain)
            results[domain["url"]] = status
            await asyncio.sleep(0.5)  # rate limit
        self._save()
        return results

    def add_domain(self, url: str, label: str = None, domain_type: str = "landing", parser: str = "generic", notes: str = ""):
        existing = [d for d in self.domains if d["url"] == url]
        if existing:
            logger.info(f"Domain already in pool: {url}")
            return
        self.domains.append({
            "url": url,
            "label": label or url.replace("https://", "").split("/")[0],
            "type": domain_type,
            "status": "untested",
            "last_check": None,
            "parser": parser,
            "notes": notes,
        })
        self._save()
        logger.info(f"Added new domain: {url}")
