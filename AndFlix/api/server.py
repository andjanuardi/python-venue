import os
import traceback
import threading
from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

from .loklok_api_mobile import get_play_info_ios
from .scan import load_db, save_db, scan_all, scan_status

API_DIR = os.path.dirname(os.path.abspath(__file__))
COVER_DIR = os.path.join(API_DIR, "cover")

app = FastAPI(title="AndFlix API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

os.makedirs(COVER_DIR, exist_ok=True)
app.mount("/api/cover", StaticFiles(directory=COVER_DIR), name="cover")

TYPE_MAP = {
    1: "Series", 2: "Movie", 3: "Anime",
    119: "Trending", 120: "New Releases", 165: "Popular",
}
REVERSE_TYPE = {"Series": 1, "Movie": 2, "Anime": 3}
COVER_URL = "/api/cover/"


def _cover(item):
    return COVER_URL + item["coverV"] if item.get("coverV") else ""


def _coverH(item):
    return COVER_URL + item["coverH"] if item.get("coverH") else ""


def _card(item):
    return {
        "id": item["id"],
        "title": item["title"],
        "cover": _cover(item),
        "coverH": _coverH(item),
        "score": item.get("score", 0),
        "year": item.get("year", ""),
    }


def _detail(item):
    eps = item.get("episodeVo", [])
    return {
        "id": item["id"],
        "title": item["title"],
        "year": str(item.get("year", "")),
        "eps": item.get("eps", len(eps)),
        "alias": item.get("alias", ""),
        "area": item.get("area", []),
        "tags": item.get("tags", []),
        "cover": _cover(item),
        "coverH": _coverH(item),
        "type": item.get("type", ""),
        "intro": (item.get("intro") or "")[:300],
        "score": item.get("score", 0),
        "episodeVo": eps,
    }


def _search_db(kw):
    q = kw.lower().strip()
    if not q:
        return []
    db = load_db()
    results = []
    for m in db:
        if q in m.get("title", "").lower():
            results.append(_card(m))
    return results[:20]


@app.get("/api/home")
def home():
    try:
        db = load_db()
        sections = []
        seen = {"Series": set(), "Movie": set(), "Anime": set()}
        for m in db:
            t = m.get("type", "")
            if t in seen:
                seen[t].add(m["id"])
        for tname, ids in seen.items():
            items = [m for m in db if m["id"] in ids]
            items.sort(key=lambda m: -(m.get("score") or 0))
            sections.append({"title": tname, "items": [_card(m) for m in items[:10]]})

        trending = sorted(db, key=lambda m: -(m.get("score") or 0))[:10]
        sections.append({"title": "Trending", "items": [_card(m) for m in trending]})
        return {"sections": sections}
    except Exception as e:
        traceback.print_exc()
        return JSONResponse({"error": str(e)}, status_code=500)


@app.get("/api/movie/browse/{page_id}")
def browse(page_id: int):
    try:
        db = load_db()
        label = TYPE_MAP.get(page_id, "Browse")
        if page_id in REVERSE_TYPE:
            tname = REVERSE_TYPE[page_id]
            items = [m for m in db if m.get("type") == tname]
            items.sort(key=lambda m: -(m.get("score") or 0))
        elif page_id == 119:
            items = sorted(db, key=lambda m: -(m.get("score") or 0))
        elif page_id == 120:
            items = sorted(db, key=lambda m: -(int(m.get("year", "0"))))
        elif page_id == 165:
            items = sorted(db, key=lambda m: -(m.get("score") or 0))
        else:
            items = db

        return {"title": label, "pageId": page_id, "items": [_card(m) for m in items]}
    except Exception as e:
        traceback.print_exc()
        return JSONResponse({"error": str(e)}, status_code=500)


@app.get("/api/search")
def search(q: str = Query(..., min_length=1)):
    try:
        results = _search_db(q)
        return {"query": q, "results": results}
    except Exception as e:
        traceback.print_exc()
        return JSONResponse({"error": str(e)}, status_code=500)


@app.get("/api/movies/{movie_id}")
def movie_detail(movie_id: int):
    try:
        db = load_db()
        for m in db:
            if int(m["id"]) == movie_id:
                return {"data": _detail(m)}
        return JSONResponse({"error": "Movie not found"}, status_code=404)
    except Exception as e:
        traceback.print_exc()
        return JSONResponse({"error": str(e)}, status_code=500)


@app.get("/api/movies/{movie_id}/play")
def movie_play(
    movie_id: int,
    episodeId: int = Query(...),
    category: int = 1,
    quality: str = "GROOT_SD",
):
    try:
        r = get_play_info_ios(movie_id, episodeId, category, definition=quality)
        if r.status_code != 200:
            return JSONResponse({"error": f"API returned {r.status_code}"}, status_code=502)
        data = r.json()
        if data.get("code") != "00000":
            return JSONResponse({"error": data.get("msg", "Unknown error")}, status_code=502)

        pi = data.get("data", {})
        subs = pi.get("subtitlingList") or []
        return {
            "mediaUrl": pi.get("mediaUrl", ""),
            "totalDuration": pi.get("totalDuration"),
            "currentDefinition": pi.get("currentDefinition", quality),
            "subtitles": [
                {"url": s.get("subtitlingUrl"), "language": s.get("language"), "languageAbbr": s.get("languageAbbr")}
                for s in subs if s.get("subtitlingUrl")
            ],
        }
    except Exception as e:
        traceback.print_exc()
        return JSONResponse({"error": str(e)}, status_code=500)


@app.get("/api/scan")
def scan():
    if scan_status.get("running"):
        return JSONResponse({"status": "running", **scan_status})

    thread = threading.Thread(target=scan_all, daemon=True)
    thread.start()
    return {"status": "started", **scan_status}


@app.get("/api/scan/status")
def scan_state():
    return {"status": "running" if scan_status.get("running") else "idle", **scan_status}
