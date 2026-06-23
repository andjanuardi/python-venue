from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Query, HTTPException
from pydantic import BaseModel

from storage.database import Database

router = APIRouter(prefix="/api/v1", tags=["data"])


# --- Response models ---
class MatchOut(BaseModel):
    match_id: str
    home_team: str
    away_team: str
    date: Optional[str] = None
    time: Optional[str] = None
    league: Optional[str] = None
    home_score: Optional[int] = None
    away_score: Optional[int] = None
    status: Optional[str] = None
    domain: str
    scraped_at: str


class StreamOut(BaseModel):
    match_id: str
    label: Optional[str] = None
    url: str
    type: str
    quality: Optional[str] = None
    server: Optional[str] = None
    domain: str


class NewsOut(BaseModel):
    news_id: str
    title: str
    date: Optional[str] = None
    excerpt: Optional[str] = None
    url: str
    thumbnail: Optional[str] = None
    source: str
    scraped_at: str


class DomainOut(BaseModel):
    url: str
    label: Optional[str] = None
    type: Optional[str] = None
    status: str
    last_check: Optional[str] = None
    notes: Optional[str] = None


class HealthOut(BaseModel):
    status: str
    database: str
    active_domains: int
    total_matches: int
    uptime: str


# --- Helpers ---
async def get_db() -> Database:
    from config.settings import settings
    db = Database()
    await db.connect()
    return db


# --- Endpoints ---

@router.get("/matches", response_model=List[MatchOut])
async def list_matches(
    league: Optional[str] = Query(None),
    date: Optional[str] = Query(None),
    limit: int = Query(50, le=200),
):
    db = await get_db()
    try:
        rows = await db.get_matches(limit=limit, league=league, date=date)
        return [MatchOut(**r) for r in rows]
    finally:
        await db.close()


@router.get("/matches/{match_id}", response_model=MatchOut)
async def get_match(match_id: str):
    db = await get_db()
    try:
        rows = await db.get_matches(limit=1)
        for r in rows:
            if r["match_id"] == match_id:
                return MatchOut(**r)
        raise HTTPException(404, f"Match {match_id} not found")
    finally:
        await db.close()


@router.get("/matches/{match_id}/streams", response_model=List[StreamOut])
async def get_match_streams(match_id: str):
    db = await get_db()
    try:
        rows = await db.get_streams(match_id=match_id)
        return [StreamOut(**r) for r in rows]
    finally:
        await db.close()


@router.get("/streams", response_model=List[StreamOut])
async def list_streams():
    db = await get_db()
    try:
        rows = await db.get_streams()
        return [StreamOut(**r) for r in rows]
    finally:
        await db.close()


@router.get("/news", response_model=List[NewsOut])
async def list_news(limit: int = Query(20, le=100)):
    db = await get_db()
    try:
        cursor = await db._conn.execute(
            "SELECT * FROM news ORDER BY date DESC LIMIT ?", (limit,)
        )
        rows = await cursor.fetchall()
        return [NewsOut(**dict(r)) for r in rows]
    finally:
        await db.close()


@router.get("/domains", response_model=List[DomainOut])
async def list_domains(status: Optional[str] = Query(None)):
    import yaml
    from config.settings import settings

    with open(settings.DOMAINS_CONFIG_PATH) as f:
        data = yaml.safe_load(f)

    domains = data.get("domains", [])
    if status:
        domains = [d for d in domains if d.get("status") == status]
    return [DomainOut(**d) for d in domains]
