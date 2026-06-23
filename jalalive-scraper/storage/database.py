import asyncio
import json
import logging
import os
from datetime import datetime
from typing import List, Optional

import aiosqlite

from config.settings import settings

logger = logging.getLogger(__name__)

SCHEMA = """
CREATE TABLE IF NOT EXISTS matches (
    match_id TEXT PRIMARY KEY,
    home_team TEXT NOT NULL,
    away_team TEXT NOT NULL,
    date TEXT,
    time TEXT,
    league TEXT,
    home_score INTEGER,
    away_score INTEGER,
    status TEXT,
    detail_url TEXT,
    domain TEXT NOT NULL,
    scraped_at TEXT NOT NULL,
    UNIQUE(match_id)
);

CREATE TABLE IF NOT EXISTS stream_links (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    match_id TEXT NOT NULL,
    label TEXT,
    url TEXT NOT NULL,
    type TEXT DEFAULT 'unknown',
    quality TEXT,
    server TEXT,
    domain TEXT NOT NULL,
    scraped_at TEXT NOT NULL,
    FOREIGN KEY (match_id) REFERENCES matches(match_id),
    UNIQUE(match_id, url)
);

CREATE TABLE IF NOT EXISTS domains (
    url TEXT PRIMARY KEY,
    label TEXT,
    type TEXT DEFAULT 'landing',
    status TEXT DEFAULT 'untested',
    last_check TEXT,
    parser TEXT DEFAULT 'generic',
    notes TEXT,
    added_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS news (
    news_id TEXT PRIMARY KEY,
    title TEXT NOT NULL,
    date TEXT,
    excerpt TEXT,
    url TEXT NOT NULL UNIQUE,
    thumbnail TEXT,
    source TEXT NOT NULL,
    scraped_at TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_matches_date ON matches(date);
CREATE INDEX IF NOT EXISTS idx_matches_league ON matches(league);
CREATE INDEX IF NOT EXISTS idx_matches_domain ON matches(domain);
CREATE INDEX IF NOT EXISTS idx_stream_match ON stream_links(match_id);
CREATE INDEX IF NOT EXISTS idx_news_source ON news(source);
CREATE INDEX IF NOT EXISTS idx_news_date ON news(date);
"""


class Database:
    def __init__(self, db_path: str = None):
        self.db_path = db_path or os.path.join(settings.DATA_DIR, "jalalive.db")
        self._conn: Optional[aiosqlite.Connection] = None

    async def connect(self):
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        self._conn = await aiosqlite.connect(self.db_path)
        self._conn.row_factory = aiosqlite.Row
        await self._conn.executescript(SCHEMA)
        await self._conn.commit()
        logger.info(f"Database connected: {self.db_path}")

    async def close(self):
        if self._conn:
            await self._conn.close()
            logger.info("Database closed")

    async def upsert_match(self, match) -> bool:
        await self._conn.execute("""
            INSERT INTO matches (match_id, home_team, away_team, date, time, league,
                                 home_score, away_score, status, detail_url, domain, scraped_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(match_id) DO UPDATE SET
                home_score = COALESCE(excluded.home_score, matches.home_score),
                away_score = COALESCE(excluded.away_score, matches.away_score),
                status = COALESCE(excluded.status, matches.status),
                scraped_at = excluded.scraped_at
        """, (
            match.match_id, match.home_team, match.away_team,
            match.date, match.time, match.league,
            match.home_score, match.away_score, match.status,
            match.detail_url, match.domain,
            match.scraped_at.isoformat() if hasattr(match.scraped_at, 'isoformat') else match.scraped_at,
        ))
        await self._conn.commit()
        return True

    async def upsert_matches(self, matches: list) -> int:
        count = 0
        for match in matches:
            try:
                await self.upsert_match(match)
                count += 1
            except Exception as e:
                logger.warning(f"Failed to insert match {match.match_id}: {e}")
        await self._conn.commit()
        return count

    async def upsert_stream(self, stream) -> bool:
        try:
            await self._conn.execute("""
                INSERT INTO stream_links (match_id, label, url, type, quality, server, domain, scraped_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(match_id, url) DO NOTHING
            """, (
                stream.match_id, stream.label, stream.url, stream.type,
                stream.quality, stream.server, stream.domain,
                stream.scraped_at.isoformat() if hasattr(stream.scraped_at, 'isoformat') else stream.scraped_at,
            ))
            await self._conn.commit()
            return True
        except Exception as e:
            logger.warning(f"Failed to insert stream: {e}")
            return False

    async def upsert_streams(self, streams: list) -> int:
        count = 0
        for stream in streams:
            if await self.upsert_stream(stream):
                count += 1
        return count

    async def upsert_domain(self, domain: dict):
        await self._conn.execute("""
            INSERT INTO domains (url, label, type, status, last_check, parser, notes, added_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(url) DO UPDATE SET
                status = excluded.status,
                last_check = excluded.last_check,
                label = excluded.label,
                type = excluded.type,
                parser = excluded.parser,
                notes = excluded.notes
        """, (
            domain["url"], domain.get("label"), domain.get("type"),
            domain.get("status"), domain.get("last_check"),
            domain.get("parser"), domain.get("notes"),
            datetime.utcnow().isoformat(),
        ))
        await self._conn.commit()

    async def get_matches(self, limit: int = 50, league: str = None, date: str = None) -> List[dict]:
        query = "SELECT * FROM matches WHERE 1=1"
        params = []
        if league:
            query += " AND league = ?"
            params.append(league)
        if date:
            query += " AND date = ?"
            params.append(date)
        query += " ORDER BY date, time LIMIT ?"
        params.append(limit)

        cursor = await self._conn.execute(query, params)
        rows = await cursor.fetchall()
        return [dict(row) for row in rows]

    async def get_streams(self, match_id: str = None) -> List[dict]:
        if match_id:
            cursor = await self._conn.execute(
                "SELECT * FROM stream_links WHERE match_id = ?", (match_id,)
            )
        else:
            cursor = await self._conn.execute("SELECT * FROM stream_links")
        rows = await cursor.fetchall()
        return [dict(row) for row in rows]
