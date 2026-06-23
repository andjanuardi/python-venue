#!/usr/bin/env python3
import argparse
import asyncio
import json
import logging
import os
import sys
from datetime import datetime
from typing import List, Optional

from config.settings import settings
from scrapers.schedule_scraper import ScheduleScraper
from scrapers.stream_scraper import StreamScraper
from scrapers.mirror_finder import MirrorFinder
from monitors.domain_monitor import DomainMonitor
from storage.database import Database
from storage.exporters import json_exporter, csv_exporter
from models.match import Match
from models.stream import StreamLink

# --- Logging ---
os.makedirs(settings.LOG_DIR, exist_ok=True)
os.makedirs(settings.DATA_DIR, exist_ok=True)

logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL),
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[
        logging.FileHandler(settings.LOG_FILE),
        logging.StreamHandler(),
    ],
)
logger = logging.getLogger(__name__)


async def scrape_schedules(domain: str = None, db: Database = None) -> List[Match]:
    target = domain or settings.PRIMARY_DOMAIN
    scraper = ScheduleScraper(domain=target)
    logger.info(f"Scraping schedules from {scraper.domain}...")
    matches = await scraper.scrape()

    if db and matches:
        count = await db.upsert_matches(matches)
        logger.info(f"Saved {count} matches to database")

    # Export JSON
    path = json_exporter.export_matches(matches, "schedules.json")
    logger.info(f"Exported {len(matches)} matches to {path}")
    return matches


async def scrape_streams(matches: List[Match], domain: str = None, db: Database = None) -> List[StreamLink]:
    target = domain or settings.PRIMARY_DOMAIN
    scraper = StreamScraper(domain=target)
    logger.info(f"Scraping stream links for {len(matches)} matches...")
    links = await scraper.scrape_matches(matches)

    if db and links:
        count = await db.upsert_streams(links)
        logger.info(f"Saved {count} streams to database")

    path = json_exporter.export_streams(links, "streams.json")
    logger.info(f"Exported {len(links)} streams to {path}")
    return links


async def check_domains():
    monitor = DomainMonitor()
    logger.info("Checking all domains...")
    results = await monitor.check_all()
    for url, status in results.items():
        logger.info(f"  {url}: {status}")

    active = monitor.get_active_domains()
    logger.info(f"Active domains: {len(active)}")
    return monitor


async def find_mirrors():
    monitor = DomainMonitor()
    known = [d["url"] for d in monitor.domains]
    finder = MirrorFinder(known_domains=known)

    logger.info("Searching for new mirror domains...")
    discovered = await finder.find_all()

    new_count = 0
    for url in discovered:
        logger.info(f"Validating {url}...")
        valid = await finder.validate(url)
        if valid:
            monitor.add_domain(url, notes="auto-discovered")
            new_count += 1
            logger.info(f"  -> Added to pool")
        else:
            logger.info(f"  -> Not a JalaLive mirror, skipped")

    logger.info(f"Found {new_count} new valid mirrors")
    return monitor


async def run_all(domain: str = None):
    logger.info("=== JalaLive Scraper — Full Run ===")
    start = datetime.now()

    db = Database()
    await db.connect()
    try:
        # Step 1: Health check
        monitor = DomainMonitor()
        if domain:
            monitor.add_domain(domain, "manual")

        active = monitor.get_first_active()
        if not active:
            logger.warning("No active domains, running health check...")
            await monitor.check_all()
            active = monitor.get_first_active()

        if active:
            logger.info(f"Using domain: {active['url']} ({active.get('type', 'unknown')})")
            target = active["url"]
        else:
            target = domain or settings.PRIMARY_DOMAIN
            logger.warning(f"No active domain, falling back to {target}")

        # Step 2: Schedules
        matches = await scrape_schedules(target, db)

        # Step 3: Streams
        if matches:
            await scrape_streams(matches, target, db)
        else:
            logger.warning("No matches found, skipping stream scraping")

        # Step 4: Try to find new mirrors (lightweight)
        await find_mirrors()

    finally:
        await db.close()

    elapsed = (datetime.now() - start).total_seconds()
    logger.info(f"Done in {elapsed:.1f}s")


def main():
    parser = argparse.ArgumentParser(description="JalaLive Scraper — Phase 2")
    parser.add_argument(
        "--scrape",
        choices=["schedules", "streams", "all", "domains", "mirrors"],
        default="all",
        help="What to run (default: all)",
    )
    parser.add_argument("--domain", default=None, help="Override domain")
    parser.add_argument(
        "--export",
        choices=["json", "csv", "db", "all"],
        default="json",
        help="Export format (default: json)",
    )

    args = parser.parse_args()

    if args.scrape == "domains":
        asyncio.run(check_domains())
    elif args.scrape == "mirrors":
        asyncio.run(find_mirrors())
    elif args.scrape == "schedules":
        db = Database()
        asyncio.run(db.connect())
        try:
            asyncio.run(scrape_schedules(args.domain, db))
        finally:
            asyncio.run(db.close())
    elif args.scrape == "streams":
        schedules_path = os.path.join(settings.DATA_DIR, "schedules.json")
        if os.path.exists(schedules_path):
            with open(schedules_path) as f:
                data = json.load(f)
            matches = [Match(**m) for m in data]
            db = Database()
            asyncio.run(db.connect())
            try:
                asyncio.run(scrape_streams(matches, args.domain, db))
            finally:
                asyncio.run(db.close())
        else:
            logger.error("No schedules.json found. Run `--scrape schedules` first.")
            sys.exit(1)
    else:
        asyncio.run(run_all(args.domain))


if __name__ == "__main__":
    main()
