#!/usr/bin/env python3
import argparse
import asyncio
import json
import logging
import os
import signal
import sys
from datetime import datetime
from typing import List, Optional

from config.settings import settings
from scrapers.schedule_scraper import ScheduleScraper
from scrapers.stream_scraper import StreamScraper
from scrapers.news_scraper import NewsScraper
from scrapers.livescore_scraper import LivescoreScraper
from scrapers.mirror_finder import MirrorFinder
from monitors.domain_monitor import DomainMonitor
from storage.database import Database
from storage.exporters import json_exporter, csv_exporter
from models.match import Match
from models.stream import StreamLink
from models.news import NewsArticle

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


async def scrape_livescores(db: Database):
    """Update livescores untuk match yang belum selesai"""
    matches_data = await db.get_matches(limit=20)
    pending = [m for m in matches_data if m.get("status") not in ("ft", "full time", "selesai")]

    if not pending:
        logger.info("No pending matches for livescore update")
        return

    pending_matches = [Match(**m) for m in pending]
    scraper = LivescoreScraper()
    updated = await scraper.scrape_many(pending_matches)

    changed = 0
    for m in updated:
        if m.home_score is not None or m.away_score is not None:
            await db.upsert_match(m)
            changed += 1

    logger.info(f"Updated {changed}/{len(updated)} livescores")
    json_exporter.export_matches(updated, "livescores.json")


async def scrape_news(domain: str = None, db: Database = None):
    target = domain or "https://jalalive.cc"
    scraper = NewsScraper(domain=target)
    logger.info(f"Scraping news from {target}...")
    articles = await scraper.scrape()

    if db and articles:
        count = 0
        for a in articles:
            try:
                await db._conn.execute("""
                    INSERT OR IGNORE INTO news (news_id, title, date, excerpt, url, thumbnail, source, scraped_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    a.news_id, a.title, a.date,
                    a.excerpt, a.url, a.thumbnail, a.source,
                    a.scraped_at.isoformat() if hasattr(a.scraped_at, 'isoformat') else a.scraped_at,
                ))
                count += 1
            except Exception:
                pass
        await db._conn.commit()
        logger.info(f"Saved {count} news articles to database")

    path = json_exporter.export_news(articles, "news.json")
    logger.info(f"Exported {len(articles)} news to {path}")


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
    logger.info(f"Found {new_count} new valid mirrors")
    return monitor


async def run_daemon():
    """Run scheduler daemon"""
    from scheduler.task_scheduler import TaskScheduler
    scheduler = TaskScheduler()

    stop_event = asyncio.Event()

    def shutdown():
        logger.info("Shutdown signal received...")
        stop_event.set()

    loop = asyncio.get_running_loop()
    for sig in (signal.SIGINT, signal.SIGTERM):
        try:
            loop.add_signal_handler(sig, shutdown)
        except NotImplementedError:
            # Windows fallback
            pass

    await scheduler.start()
    logger.info("Daemon running. Press Ctrl+C to stop.")

    try:
        await stop_event.wait()
    except asyncio.CancelledError:
        pass
    finally:
        await scheduler.stop()
        logger.info("Daemon stopped.")


async def run_all(domain: str = None):
    logger.info("=== JalaLive Scraper — Full Run ===")
    start = datetime.now()

    db = Database()
    await db.connect()
    try:
        monitor = DomainMonitor()
        if domain:
            monitor.add_domain(domain, "manual")
        active = monitor.get_first_active()
        if not active:
            logger.warning("No active domains, running health check...")
            await monitor.check_all()
            active = monitor.get_first_active()
        target = active["url"] if active else (domain or settings.PRIMARY_DOMAIN)

        # Schedules
        matches = await scrape_schedules(target, db)

        # Streams
        if matches:
            await scrape_streams(matches, target, db)

        # Livescores
        await scrape_livescores(db)

        # News
        await scrape_news(db=db)

        # Mirrors
        await find_mirrors()
    finally:
        await db.close()

    elapsed = (datetime.now() - start).total_seconds()
    logger.info(f"Done in {elapsed:.1f}s")


def run_api():
    import uvicorn
    from api.app import app
    logger.info("Starting API server on http://0.0.0.0:8000")
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")


def main():
    parser = argparse.ArgumentParser(description="JalaLive Scraper — Phase 4")
    parser.add_argument(
        "--scrape",
        choices=["schedules", "streams", "livescores", "news", "all", "domains", "mirrors"],
        default="all",
        help="What to run (default: all)",
    )
    parser.add_argument("--domain", default=None, help="Override domain")
    parser.add_argument(
        "--daemon",
        action="store_true",
        help="Run as persistent daemon with scheduler",
    )
    parser.add_argument(
        "--api",
        action="store_true",
        help="Start REST API server",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=8000,
        help="API server port (default: 8000)",
    )
    parser.add_argument(
        "--export",
        choices=["json", "csv", "db"],
        default="json",
        help="Export format (default: json)",
    )

    args = parser.parse_args()

    if args.api:
        run_api()
        return

    # Handle daemon mode
    if args.daemon:
        asyncio.run(run_daemon())
        return

    if args.scrape == "domains":
        asyncio.run(check_domains())
    elif args.scrape == "mirrors":
        asyncio.run(find_mirrors())
    elif args.scrape == "schedules":
        async def run():
            db = Database()
            await db.connect()
            try:
                await scrape_schedules(args.domain, db)
            finally:
                await db.close()
        asyncio.run(run())
    elif args.scrape == "streams":
        async def run():
            schedules_path = os.path.join(settings.DATA_DIR, "schedules.json")
            if os.path.exists(schedules_path):
                with open(schedules_path) as f:
                    data = json.load(f)
                matches = [Match(**m) for m in data]
                db = Database()
                await db.connect()
                try:
                    await scrape_streams(matches, args.domain, db)
                finally:
                    await db.close()
            else:
                logger.error("No schedules.json found. Run `--scrape schedules` first.")
                sys.exit(1)
        asyncio.run(run())
    elif args.scrape == "livescores":
        async def run():
            db = Database()
            await db.connect()
            try:
                await scrape_livescores(db)
            finally:
                await db.close()
        asyncio.run(run())
    elif args.scrape == "news":
        async def run():
            db = Database()
            await db.connect()
            try:
                await scrape_news(args.domain, db)
            finally:
                await db.close()
        asyncio.run(run())
    else:
        asyncio.run(run_all(args.domain))


if __name__ == "__main__":
    main()
