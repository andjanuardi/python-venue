from pydantic_settings import BaseSettings
from typing import List
import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


class Settings(BaseSettings):
    # Domain pool
    DOMAINS: List[str] = [
        "https://reboundac.com",
        "https://jalalive.cc",
        "https://www.jalalive3.id",
        "https://jalaace5.com",
        "https://jalalive11.com",
    ]

    PRIMARY_DOMAIN: str = "https://reboundac.com"

    # Request settings
    REQUEST_TIMEOUT: int = 30
    RETRY_COUNT: int = 3
    RETRY_DELAY: float = 2.0
    REQUEST_DELAY: tuple = (1.0, 3.0)

    # User agents
    USER_AGENTS: List[str] = [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_5) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.5 Safari/605.1.15",
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:127.0) Gecko/20100101 Firefox/127.0",
    ]

    # Paths
    DATA_DIR: str = os.path.join(BASE_DIR, "data")
    LOG_DIR: str = os.path.join(BASE_DIR, "logs")
    DOMAINS_CONFIG_PATH: str = os.path.join(BASE_DIR, "config", "domains.yaml")
    DB_PATH: str = os.path.join(BASE_DIR, "data", "jalalive.db")

    # Logging
    LOG_LEVEL: str = "INFO"
    LOG_FILE: str = os.path.join(LOG_DIR, "scraper.log")


settings = Settings()
