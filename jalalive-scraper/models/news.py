from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


class NewsArticle(BaseModel):
    news_id: str = Field(description="Unique identifier")
    title: str
    date: Optional[str] = None
    excerpt: Optional[str] = None
    url: str
    thumbnail: Optional[str] = None
    source: str = Field(description="Source domain")
    scraped_at: datetime = Field(default_factory=datetime.utcnow)
