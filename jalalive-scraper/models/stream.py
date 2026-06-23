from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


class StreamLink(BaseModel):
    match_id: str
    label: Optional[str] = None
    url: str
    type: str = Field(default="unknown", description="iframe, direct, redirect")
    quality: Optional[str] = None
    server: Optional[str] = None
    domain: str = Field(description="Source domain")
    scraped_at: datetime = Field(default_factory=datetime.utcnow)
