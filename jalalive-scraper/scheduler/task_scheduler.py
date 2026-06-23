import asyncio
import logging
from datetime import datetime
from typing import List, Optional

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger

from config.settings import settings
from monitors.domain_monitor import DomainMonitor
from scrapers.schedule_scraper import ScheduleScraper
from scrapers.stream_scraper import StreamScraper
from scrapers.news_scraper import NewsScraper
from scrapers.livescore_scraper import LivescoreScraper
from scrapers.mirror_finder import MirrorFinder
from storage.database import Database
from storage.exporters import json_exporter

logger = logging.getLogger(__name__)


class TaskScheduler:
    def __init__(self):
        self.scheduler = AsyncIOScheduler()
        self.db: Optional[Database] = None
        self._running = False

    async def start(self):
        self.db = Database()
        await self.db.connect()

        # Register jobs
        self.scheduler.add_job(
            self.job_schedules,
            IntervalTrigger(minutes=15),
            id="schedules",
            name="Scrape match schedules",
            replace_existing=True,
        )
        self.scheduler.add_job(
            self.job_livescores,
            IntervalTrigger(minutes=2),
            id="livescores",
            name="Update livescores",
            replace_existing=True,
        )
        self.scheduler.add_job(
            self.job_news,
            IntervalTrigger(hours=1),
            id="news",
            name="Scrape news articles",
            replace_existing=True,
        )
        self.scheduler.add_job(
            self.job_health,
            IntervalTrigger(hours=1),
            id="health",
            name="Domain health check",
            replace_existing=True,
        )
        self.scheduler.add_job(
            self.job_mirrors,
            IntervalTrigger(hours=6),
            id="mirrors",
            name="Discover new mirrors",
            replace_existing=True,
        )

        self.scheduler.start()
        self._running = True
        logger.info("Scheduler started with 5 jobs")

        # Run initial jobs immediately
        logger.info("Running initial jobs...")
        await self.job_schedules()
        await self.job_news()
        await self.job_health()

    async def stop(self):
        if self.scheduler.running:
            self.scheduler.shutdown(wait=False)
        if self.db:
            await self.db.close()
        self._running = False
        logger.info("Scheduler stopped")

    async def job_schedules(self):
        logger.info("[Scheduler] Running: schedules")
        monitor = DomainMonitor()
        active = monitor.get_first_active()
        if not active:
            await monitor.check_all()
            active = monitor.get_first_active()
        if not active:
            logger.warning("[Scheduler] No active domain for schedules")
            return

        scraper = ScheduleScraper(domain=active["url"])
        matches = await scraper.scrape()
        if matches:
            count = await self.db.upsert_matches(matches)
            json_exporter.export_matches(matches, "schedules.json")
            logger.info(f"[Scheduler] Saved {count} matches")

    async def job_livescores(self):
        logger.info("[Scheduler] Running: livescores")
        matches_data = await self.db.get_matches(limit=20)

        if not matches_data:
            logger.debug("[Scheduler] No matches to check")
            return

        # Only update matches that might be live (no full-time result)
        pending = [m for m in matches_data if m.get("status") not in ("ft", "full time", "selesai")]

        if not pending:
            logger.debug("[Scheduler] No pending matches for livescore")
            return

        # Convert to Match objects
        from models.match import Match
        pending_matches = [Match(**m) for m in pending]

        scraper = LivescoreScraper()
        updated = await scraper.scrape_many(pending_matches)

        changed = 0
        for m in updated:
            if m.home_score is not None or m.away_score is not None:
                await self.db.upsert_match(m)
                changed += 1

        if changed:
            logger.info(f"[Scheduler] Updated {changed} livescores")

    async def job_news(self):
        logger.info("[Scheduler] Running: news")
        monitor = DomainMonitor()
        # Prefer blog-type domains for news
        blog_domains = [d for d in monitor.domains if d.get("type") in ("blog", "landing") and d.get("status") == "active"]

        for domain in blog_domains[:2]:  # max 2 domains
            scraper = NewsScraper(domain=domain["url"])
            articles = await scraper.scrape()
            if articles:
                # Save to DB
                db_count = 0
                for article in articles:
                    try:
                        await self.db._conn.execute("""
                            INSERT OR IGNORE INTO news (news_id, title, date, excerpt, url, thumbnail, source, scraped_at)
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                        """, (
                            article.news_id, article.title, article.date,
                            article.excerpt, article.url, article.thumbnail,
                            article.source,
                            article.scraped_at.isoformat() if hasattr(article.scraped_at, 'isoformat') else article.scraped_at,
                        ))
                        db_count += 1
                    except Exception:
                        pass
                await self.db._conn.commit()
                logger.info(f"[Scheduler] Saved {db_count} news articles from {domain['url']}")

    async def job_health(self):
        logger.info("[Scheduler] Running: domain health check")
        monitor = DomainMonitor()
        await monitor.check_all()

    async def job_mirrors(self):
        logger.info("[Scheduler] Running: mirror discovery")
        monitor = DomainMonitor()
        known = [d["url"] for d in monitor.domains]
        finder = MirrorFinder(known_domains=known)
        discovered = await finder.find_all()

        new_count = 0
        for url in discovered:
            valid = await finder.validate(url)
            if valid:
                monitor.add_domain(url, notes="auto-discovered by scheduler")
                new_count += 1

        logger.info(f"[Scheduler] Found {new_count} new mirrors")

    async def run_once(self):
        """Run all jobs once (for CLI --scrape all in daemon mode)"""
        await self.job_schedules()
        await self.job_news()
        await self.job_livescores()
        await self.job_health()
        await self.job_mirrors()

    def is_running(self) -> bool:
        return self._running
