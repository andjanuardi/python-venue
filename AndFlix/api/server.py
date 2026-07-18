import os
import re
import hashlib
import time
import traceback
import threading
import requests
from fastapi import FastAPI, Query, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse, Response, StreamingResponse

from .loklok_api_mobile import get_movie_detail, get_play_info_ios, get_all_qualities, LANG_MAP, get_home
from .scan import load_db, save_db, scan_all, scan_status, _download, db_lock, _fetch_one

PLAY_CACHE = {}
PLAY_CACHE_TTL = 600  # 10 menit
PLAY_CACHE_LOCK = threading.Lock()


def _get_cached_play(movie_id, episode_id, category, quality):
    key = (movie_id, episode_id, category, quality)
    now = time.time()
    with PLAY_CACHE_LOCK:
        entry = PLAY_CACHE.get(key)
        if entry and (now - entry["ts"]) < PLAY_CACHE_TTL:
            return entry["data"]
    try:
        r = get_play_info_ios(movie_id, episode_id, category, definition=quality)
        if r.status_code != 200:
            return None
        data = r.json()
        if data.get("code") != "00000":
            return None
        with PLAY_CACHE_LOCK:
            PLAY_CACHE[key] = {"data": data, "ts": now}
        return data
    except Exception:
        return None

HOME_NAV_IDS = [1, 2, 3, 119, 120, 165]
H5_KWARGS = {"client_type": "H5", "version_code": "32"}


def _ensure_movie_in_db(movie_id):
    with db_lock:
        db = load_db()
        for m in db:
            if str(m["id"]) == str(movie_id):
                return m
        result = _fetch_one(str(movie_id))
        if result:
            db.append(result)
            db.sort(key=lambda m: int(m["id"]))
            save_db(db)
        return result


API_DIR = os.path.dirname(os.path.abspath(__file__))
COVER_DIR = os.path.join(API_DIR, "cover")
SUBTITLE_DIR = os.path.join(API_DIR, "subtitles")

app = FastAPI(title="AndFlix API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

os.makedirs(COVER_DIR, exist_ok=True)
os.makedirs(SUBTITLE_DIR, exist_ok=True)


@app.get("/api/cover/{filename:path}")
def cover_proxy(filename: str):
    m = re.match(r"(\d+)-([VH])\.webp$", filename)
    if not m:
        return JSONResponse({"error": "Invalid filename"}, status_code=400)

    mid = int(m.group(1))
    is_v = m.group(2) == "V"
    url_key = "coverVUrl" if is_v else "coverHUrl"

    with db_lock:
        db = load_db()
        found_item = None
        url = None
        for item in db:
            if int(item["id"]) == mid:
                found_item = item
                url = item.get(url_key)
                break

        if found_item and not url:
            for cat in [1, 0]:
                try:
                    r = get_movie_detail(mid, cat)
                    if r.status_code != 200:
                        continue
                    d = r.json()
                    if d.get("code") == "00000" and d.get("data"):
                        data = d["data"]
                        url = data.get("coverVerticalUrl") or data.get("coverHorizontalUrl") or ""
                        if url:
                            found_item[url_key] = url
                            save_db(db)
                            break
                except Exception:
                    continue

    if url:
        try:
            resp = requests.get(url, stream=True, timeout=15)
            return StreamingResponse(
                resp.iter_content(chunk_size=8192),
                status_code=resp.status_code,
                media_type=resp.headers.get("content-type", "image/webp"),
            )
        except Exception:
            pass

    return JSONResponse({"error": "Cover not found"}, status_code=404)


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
    eps_out = []
    mid = item["id"]
    for ep in eps:
        e = dict(ep)
        sub = e.get("subtitle_url", {})
        e["subtitle_url"] = {
            k: f"/api/subtitle/{mid}/{ep['id']}/{k}"
            for k, v in sub.items() if v
        }
        eps_out.append(e)
    return {
        "id": mid,
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
        "episodeVo": eps_out,
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
    results.sort(key=lambda x: str(x.get("year", "0")).zfill(4), reverse=True)
    return results[:20]


@app.get("/api/home")
def home():
    try:
        sections = []
        for nav in HOME_NAV_IDS:
            try:
                r = get_home(nav, 0, **H5_KWARGS)
                if r.status_code != 200:
                    continue
                d = r.json()
                if d.get("code") != "00000":
                    continue
                items = d.get("data", {}).get("recommendItems", [])
                for sec in items:
                    title = sec.get("browseName", TYPE_MAP.get(nav, "Browse"))
                    content = sec.get("recommendContentVOList", [])
                    out = []
                    for item in content:
                        mid = item.get("cid") or item.get("id")
                        if not mid:
                            continue
                        movie = _ensure_movie_in_db(mid)
                        if movie:
                            out.append(_card(movie))
                    if out:
                        sections.append({"title": title, "items": out})
            except Exception:
                continue

        if sections:
            return {"sections": sections}

        db = load_db()
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


@app.get("/api/movies/count")
def movie_count():
    try:
        db = load_db()
        return {"count": len(db)}
    except Exception:
        return {"count": 0}


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


@app.api_route("/api/movies/{movie_id}/play", methods=["GET", "HEAD"])
def movie_play(
    movie_id: int,
    episodeId: int = Query(...),
    category: int = 1,
    quality: str = "GROOT_SD",
    request: Request = None,
):
    try:
        if request and request.method == "HEAD":
            return Response()

        data = _get_cached_play(movie_id, episodeId, category, quality)
        if not data:
            return JSONResponse({"error": "Cannot get play info"}, status_code=502)

        pi = data.get("data", {})
        subs = pi.get("subtitlingList") or []

        if not subs:
            db = load_db()
            for m in db:
                if m.get("id") == movie_id:
                    for ep in m.get("episodeVo", []):
                        if ep.get("id") == episodeId:
                            for lang, url in ep.get("subtitle_url", {}).items():
                                if url:
                                    subs.append({
                                        "language": LANG_MAP.get(lang, lang),
                                        "languageAbbr": lang,
                                        "subtitlingUrl": url,
                                        "url": f"/api/subtitle/{movie_id}/{episodeId}/{lang}",
                                    })
                            break
                    break

        qualities = get_all_qualities(movie_id, episodeId, category)

        return {
            "mediaUrl": pi.get("mediaUrl", ""),
            "totalDuration": pi.get("totalDuration"),
            "currentDefinition": pi.get("currentDefinition", quality),
            "qualities": qualities,
            "subtitles": [
                {"url": s.get("url") or f"/api/subtitle/url?url={s.get('subtitlingUrl')}", "language": s.get("language"), "languageAbbr": s.get("languageAbbr")}
                for s in subs if s.get("subtitlingUrl") or s.get("url")
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


@app.post("/api/movies/add/{movie_id}")
def movie_add(movie_id: int):
    try:
        with db_lock:
            db = load_db()
            if any(str(m["id"]) == str(movie_id) for m in db):
                return JSONResponse(
                    {"error": "Already exists", "id": movie_id},
                    status_code=409,
                )

            result = _fetch_one(str(movie_id))
            if not result:
                return JSONResponse({"error": "Fetch failed"}, status_code=502)

            db.append(result)
            db.sort(key=lambda m: int(m["id"]))
            save_db(db)
        return {"data": _detail(result)}
    except Exception as e:
        traceback.print_exc()
        return JSONResponse({"error": str(e)}, status_code=500)


@app.get("/api/subtitle/{movie_id}/{episode_id}/{lang}")
def subtitle_proxy(movie_id: int, episode_id: int, lang: str):
    filepath = os.path.join(SUBTITLE_DIR, str(movie_id), str(episode_id), f"{lang}.vtt")
    if os.path.exists(filepath):
        return FileResponse(filepath, media_type="text/vtt")

    db = load_db()
    for m in db:
        if int(m["id"]) == movie_id:
            for ep in m.get("episodeVo", []):
                if int(ep["id"]) == episode_id:
                    cdn_url = ep.get("subtitle_url", {}).get(lang)
                    if cdn_url and _download(cdn_url, filepath):
                        return FileResponse(filepath, media_type="text/vtt")
                    break
            break
    return JSONResponse({"error": "Subtitle not found"}, status_code=404)


@app.get("/api/subtitle/url")
def subtitle_url_proxy(url: str = Query(...)):
    cache_key = hashlib.md5(url.encode()).hexdigest()
    cache_path = os.path.join(SUBTITLE_DIR, "_cache", f"{cache_key}.vtt")
    if os.path.exists(cache_path):
        return FileResponse(cache_path, media_type="text/vtt")
    os.makedirs(os.path.dirname(cache_path), exist_ok=True)
    if _download(url, cache_path):
        return FileResponse(cache_path, media_type="text/vtt")
    return JSONResponse({"error": "Failed to fetch"}, status_code=502)
