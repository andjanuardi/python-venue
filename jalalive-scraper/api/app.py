import asyncio
import logging
import time
from contextlib import asynccontextmanager

import yaml
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from prometheus_client import Counter, Histogram, generate_latest, CONTENT_TYPE_LATEST
from starlette.responses import Response

from api.routes import router
from config.settings import settings
from monitors.domain_monitor import DomainMonitor
from storage.database import Database

logger = logging.getLogger(__name__)

# --- Prometheus metrics ---
REQUEST_COUNT = Counter("jalalive_requests_total", "Total API requests", ["method", "endpoint"])
REQUEST_LATENCY = Histogram("jalalive_request_duration_seconds", "Request latency", ["endpoint"])
SCRAPE_DURATION = Histogram("jalalive_scrape_duration_seconds", "Scrape job duration")
DOMAIN_ACTIVE = Counter("jalalive_domain_active", "Active domain count")

# --- App state ---
app_state = {"start_time": time.time(), "db": None}


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    db = Database()
    await db.connect()
    app_state["db"] = db
    logger.info("API server started")
    yield
    # Shutdown
    await db.close()
    logger.info("API server stopped")


app = FastAPI(
    title="JalaLive Scraper API",
    description="REST API untuk data scraping JalaLive (jalas30.com)",
    version="3.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routes
app.include_router(router)


# --- Middleware ---
@app.middleware("http")
async def metrics_middleware(request, call_next):
    REQUEST_COUNT.labels(method=request.method, endpoint=request.url.path).inc()
    start = time.time()
    response = await call_next(request)
    REQUEST_LATENCY.labels(endpoint=request.url.path).observe(time.time() - start)
    return response


# --- Built-in endpoints ---

@app.get("/health")
async def health():
    db = app_state.get("db")
    db_status = "connected" if db and db._conn else "disconnected"

    try:
        if db and db._conn:
            cursor = await db._conn.execute("SELECT COUNT(*) as c FROM matches")
            total_matches = (await cursor.fetchone())["c"]
        else:
            total_matches = 0
    except Exception:
        total_matches = 0

    monitor = DomainMonitor()
    active_count = len(monitor.get_active_domains())

    uptime = time.time() - app_state.get("start_time", time.time())

    return {
        "status": "ok",
        "database": db_status,
        "active_domains": active_count,
        "total_matches": total_matches,
        "uptime_seconds": round(uptime, 1),
    }


@app.get("/metrics")
async def metrics():
    return Response(content=generate_latest(), media_type=CONTENT_TYPE_LATEST)


@app.post("/scrape")
async def trigger_scrape():
    """Trigger a full scrape run via API"""
    from main import run_all

    start = time.time()
    try:
        await run_all()
        duration = time.time() - start
        SCRAPE_DURATION.observe(duration)
        return {"status": "ok", "duration_seconds": round(duration, 1)}
    except Exception as e:
        raise HTTPException(500, f"Scrape failed: {e}")
