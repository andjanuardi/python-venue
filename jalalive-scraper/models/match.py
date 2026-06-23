from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


class League(BaseModel):
    name: str
    country: Optional[str] = None


class Match(BaseModel):
    match_id: str = Field(description="Unique identifier (hash of teams + date)")
    home_team: str
    away_team: str
    date: Optional[str] = None
    time: Optional[str] = None
    league: Optional[str] = None
    home_score: Optional[int] = None
    away_score: Optional[int] = None
    status: Optional[str] = None
    detail_url: Optional[str] = None
    domain: str = Field(description="Source domain")
    scraped_at: datetime = Field(default_factory=datetime.utcnow)
