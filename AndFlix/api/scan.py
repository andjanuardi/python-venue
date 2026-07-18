import os
import time
import json
import threading
import requests
from concurrent.futures import ThreadPoolExecutor, as_completed

from .loklok_api_mobile import get_movie_detail, get_home

API_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(API_DIR, "db.json")
COVER_DIR = os.path.join(API_DIR, "cover")
H5_KWARGS = {"client_type": "H5", "version_code": "32"}
NAV_IDS = [1, 2, 3, 119, 120, 165]
MAX_PAGES = 10

scan_status = {"running": False, "total": 0, "done": 0, "new": 0, "errors": 0}
db_lock = threading.RLock()


def _download(url, path):
    if os.path.exists(path):
        return True
    if not url:
        return False
    try:
        r = requests.get(url, timeout=15, proxies={"http": "", "https": ""})
        if r.status_code == 200:
            os.makedirs(os.path.dirname(path), exist_ok=True)
            with open(path, "wb") as f:
                f.write(r.content)
            return True
    except Exception:
        pass
    return False


def _extract(mv, tid):
    eps = []
    for i, ep in enumerate(mv.get("episodeVo", [])):
        subs = ep.get("subtitlingList") or []
        sub_url = {}
        for s in subs:
            abbr = s.get("languageAbbr", "")
            url = s.get("subtitlingUrl", "")
            if abbr == "in_ID" and url:
                sub_url["id"] = url
            elif abbr == "en" and url:
                sub_url["en"] = url
        eps.append({
            "id": ep.get("id"),
            "seriesNo": ep.get("seriesNo", i + 1),
            "name": ep.get("name", f"Episode {ep.get('seriesNo', i + 1)}"),
            "viewable": ep.get("viewable", False),
            "definitionList": ep.get("definitionList", []),
            "subtitle_url": sub_url,
        })

    coverV_url = mv.get("coverVerticalUrl") or mv.get("coverHorizontalUrl") or ""
    coverH_url = mv.get("coverHorizontalUrl") or ""
    coverV_file = f"{tid}-V.webp"
    coverH_file = f"{tid}-H.webp"

    return {
        "id": int(tid),
        "title": mv.get("enName") or mv.get("title") or mv.get("name", "?"),
        "year": str(mv.get("year", "")),
        "eps": mv.get("episodeCount", len(eps)),
        "alias": mv.get("aliasName", ""),
        "area": [a.get("name") for a in mv.get("areaList", []) if isinstance(a, dict)],
        "tags": [t.get("name") for t in mv.get("tagList", []) if isinstance(t, dict)],
        "type": mv.get("drameTypeVo", {}).get("drameName", ""),
        "intro": (mv.get("introduction") or "")[:300],
        "score": mv.get("score", 0),
        "coverV": coverV_file,
        "coverH": coverH_file,
        "coverVUrl": coverV_url,
        "coverHUrl": coverH_url,
        "episodeVo": eps,
    }


def _fetch_one(tid):
    for cat in [1, 0]:
        try:
            r = get_movie_detail(tid, cat)
            if r.status_code != 200:
                continue
            d = r.json()
            if d.get("code") == "00000" and d.get("data"):
                return _extract(d["data"], tid)
        except Exception:
            continue
    return None


def _collect_ids():
    all_ids = set()
    for nav in NAV_IDS:
        for page in range(MAX_PAGES):
            try:
                r = get_home(nav, page, **H5_KWARGS)
                if r.status_code != 200:
                    break
                d = r.json()
                if d.get("code") != "00000":
                    break
                items = d.get("data", {}).get("recommendItems", [])
                if not items:
                    break
                count = 0
                for sect in items:
                    for x in sect.get("recommendContentVOList", []):
                        cid = x.get("cid") or x.get("id")
                        if cid:
                            all_ids.add(str(cid))
                            count += 1
                if count == 0:
                    break
            except Exception:
                break
    return all_ids


def load_db():
    if os.path.exists(DB_PATH):
        with open(DB_PATH, encoding="utf-8") as f:
            return json.load(f)
    return []


def save_db(movies):
    with db_lock:
        os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
        tmp = DB_PATH + ".tmp"
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(movies, f, indent=2, ensure_ascii=False)
        if os.path.exists(DB_PATH):
            os.replace(tmp, DB_PATH)
        else:
            os.rename(tmp, DB_PATH)


def scan_all():
    global scan_status
    scan_status = {"running": True, "total": 0, "done": 0, "new": 0, "errors": 0}

    os.makedirs(COVER_DIR, exist_ok=True)
    all_ids = _collect_ids()

    existing = {str(m["id"]) for m in load_db()}
    new_ids = [cid for cid in all_ids if cid not in existing]
    scan_status["total"] = len(new_ids)

    if not new_ids:
        scan_status["running"] = False
        return scan_status

    found = []
    with ThreadPoolExecutor(max_workers=15) as ex:
        futures = {ex.submit(_fetch_one, cid): cid for cid in new_ids}
        for f in as_completed(futures):
            scan_status["done"] += 1
            result = f.result()
            if result:
                found.append(result)
                scan_status["new"] += 1
            else:
                scan_status["errors"] += 1

    all_movies = load_db() + found
    all_movies.sort(key=lambda m: int(m["id"]))
    save_db(all_movies)

    scan_status["running"] = False
    return scan_status
