import json
import sys
import os
import shutil

from loklok_api_mobile import (
    make_api_call, get_movie_detail, get_play_info, get_play_info_ios,
    get_all_qualities, login as api_login, is_logged_in, SESSION,
    load_movie_db, search_db, filter_db,
)

STREAM_HOST = "localhost"
STREAM_PORT = 8765

def clear():
    w = shutil.get_terminal_size().columns
    print("\n" + "=" * w)

def header(title):
    w = shutil.get_terminal_size().columns
    print("=" * w)
    if SESSION["logged_in"]:
        u = SESSION.get("userName", "")
        s = f"  {title}  |  User: {u}"
    else:
        s = f"  {title}  |  [Belum Login]"
    print(s)
    print("=" * w)

def pause():
    input("\n  [Enter] ")

def pilih(options, title="MENU"):
    clear()
    header(title)
    for i, (label, _) in enumerate(options, 1):
        print(f"  {i}. {label}")
    print(f"  {len(options)+1}. Kembali")
    print()
    try:
        c = int(input("  Pilih: "))
        if 1 <= c <= len(options):
            return options[c-1][1]()
    except (ValueError, EOFError, KeyboardInterrupt):
        pass
    return "back"

# --- Data helpers ---

def get_unique_tags():
    movies = load_movie_db()
    tags = set()
    for m in movies:
        for t in m.get("tags", []):
            tags.add(t)
    return sorted(tags)

def get_unique_years():
    movies = load_movie_db()
    years = set()
    for m in movies:
        y = m.get("year")
        if y:
            years.add(str(y))
    return sorted(years, reverse=True)

def get_unique_areas():
    movies = load_movie_db()
    areas = set()
    for m in movies:
        for a in m.get("area", []):
            areas.add(a)
    return sorted(areas)

# --- Browse functions ---

def browse_category():
    tags = get_unique_tags()
    if not tags:
        print("\n  Database kosong.")
        pause()
        return
    while True:
        clear()
        header("CATEGORY")
        page = 0
        page_size = 25
        total = len(tags)
        while True:
            start = page * page_size
            end = min(start + page_size, total)
            clear()
            header(f"CATEGORY (hal {page+1}/{(total-1)//page_size+1})")
            for i, t in enumerate(tags[start:end], start + 1):
                print(f"  {i:2}. {t}")
            print()
            print(f"  [{total} tags]")
            print("  [n] Next  [p] Prev  [0] Kembali")
            print()
            try:
                c = input("  Pilih tag: ").strip()
                if c == "0":
                    return
                if c == "n" and end < total:
                    page += 1
                    continue
                if c == "p" and page > 0:
                    page -= 1
                    continue
                idx = int(c)
                if 1 <= idx <= total:
                    tag = tags[idx - 1]
                    filtered = filter_db(tag=tag)
                    if filtered:
                        list_db_movie(filtered, f"CATEGORY: {tag}")
                    return
            except (ValueError, EOFError, KeyboardInterrupt):
                return

def browse_year():
    years = get_unique_years()
    if not years:
        print("\n  Database kosong.")
        pause()
        return
    while True:
        clear()
        header("TAHUN")
        page = 0
        page_size = 25
        total = len(years)
        while True:
            start = page * page_size
            end = min(start + page_size, total)
            clear()
            header(f"TAHUN (hal {page+1}/{(total-1)//page_size+1})")
            for i, y in enumerate(years[start:end], start + 1):
                print(f"  {i:2}. {y}")
            print()
            print(f"  [{total} tahun]")
            print("  [n] Next  [p] Prev  [0] Kembali")
            print()
            try:
                c = input("  Pilih tahun: ").strip()
                if c == "0":
                    return
                if c == "n" and end < total:
                    page += 1
                    continue
                if c == "p" and page > 0:
                    page -= 1
                    continue
                idx = int(c)
                if 1 <= idx <= total:
                    yr = years[idx - 1]
                    filtered = filter_db(year=yr)
                    if filtered:
                        list_db_movie(filtered, f"TAHUN {yr}")
                    return
            except (ValueError, EOFError, KeyboardInterrupt):
                return

def browse_country():
    areas = get_unique_areas()
    if not areas:
        print("\n  Database kosong.")
        pause()
        return
    while True:
        clear()
        header("NEGARA")
        page = 0
        page_size = 25
        total = len(areas)
        while True:
            start = page * page_size
            end = min(start + page_size, total)
            clear()
            header(f"NEGARA (hal {page+1}/{(total-1)//page_size+1})")
            for i, a in enumerate(areas[start:end], start + 1):
                print(f"  {i:2}. {a}")
            print()
            print(f"  [{total} negara]")
            print("  [n] Next  [p] Prev  [0] Kembali")
            print()
            try:
                c = input("  Pilih negara: ").strip()
                if c == "0":
                    return
                if c == "n" and end < total:
                    page += 1
                    continue
                if c == "p" and page > 0:
                    page -= 1
                    continue
                idx = int(c)
                if 1 <= idx <= total:
                    area = areas[idx - 1]
                    filtered = filter_db(area=area)
                    if filtered:
                        list_db_movie(filtered, f"NEGARA: {area}")
                    return
            except (ValueError, EOFError, KeyboardInterrupt):
                return

# --- Movie display ---

def list_db_movie(movies, sumber="DATABASE", sort="id"):
    if not movies:
        print("\n  Tidak ada hasil.")
        pause()
        return
    movies = list(movies)
    if sort == "year":
        movies.sort(key=lambda m: m.get("year") or "", reverse=True)
    else:
        movies.sort(key=lambda m: int(m.get("id") or 0))
    page = 0
    page_size = 25
    total = len(movies)
    while True:
        start = page * page_size
        end = min(start + page_size, total)
        clear()
        header(f"MOVIE - {sumber} (hal {page+1}/{(total-1)//page_size+1})")
        for i, m in enumerate(movies[start:end], start + 1):
            t = m.get("title", "?")
            y = m.get("year", "")
            eps = m.get("eps", "?")
            a = m.get("area_summary", "")
            print(f"  {i:2}. {t}" + (f" ({y})" if y else "") + f" - {eps} eps" + (f" [{a}]" if a else ""))
            print(f"      ID: {m['id']}")
        print()
        print(f"  [{total} movie]")
        print("  [n] Next  [p] Prev  [0] Kembali")
        print()
        try:
            c = input("  Pilih movie (0 kembali): ").strip()
            if c == "0":
                return
            if c == "n" and end < total:
                page += 1
                continue
            if c == "p" and page > 0:
                page -= 1
                continue
            idx = int(c)
            if 1 <= idx <= total:
                detail_movie(movies[idx - 1]["id"])
        except (ValueError, EOFError, KeyboardInterrupt):
            return

def search_movie():
    clear()
    header("CARI MOVIE")
    try:
        kw = input("  Kata kunci: ").strip()
        if not kw:
            return
    except (EOFError, KeyboardInterrupt):
        return
    print("\n  Mencari di database lokal...")
    local = search_db(kw)
    if local:
        list_db_movie(local, f"HASIL: {kw}")
        return
    print(f"\n  Tidak ditemukan di database: '{kw}'")
    print("  Coba gunakan 'Scan API' untuk")
    print("  mencari ID movie tertentu.")
    pause()

# --- Login ---

def do_login():
    clear()
    header("LOGIN")
    try:
        email = input("  Email: ").strip()
        pwd = input("  Password: ").strip()
        if not email or not pwd:
            return
    except (EOFError, KeyboardInterrupt):
        return
    print("\n  Login...")
    result = api_login(email, pwd)
    if result:
        print(f"  Berhasil! User: {result.get('userName', '?')}")
        print(f"  Token: {result.get('token', '')[:30]}...")
    else:
        print("  Login gagal. Cek email/password.")
    pause()

def do_logout():
    from loklok_api_mobile import set_auth
    set_auth()
    print("\n  Logout berhasil.")
    pause()

# --- Scan API ---

def _fetch_movie(tid):
    def _fetch(cat):
        r = make_api_call("GET", "/cms/web/movieDrama/get",
                         params={"id": tid, "category": cat})
        return r.json()
    d = _fetch(1)
    if d.get("code") != "00000":
        d = _fetch(0)
    if d.get("code") == "00000":
        mv = d["data"]
        return {
            "id": int(tid),
            "title": mv.get("enName") or mv.get("title") or mv.get("name", "?"),
            "year": mv.get("year", ""),
            "eps": mv.get("episodeCount", len(mv.get("episodeVo", []))),
            "alias": mv.get("aliasName", ""),
            "area": [a.get("name") for a in mv.get("areaList", []) if isinstance(a, dict)],
            "tags": [t.get("name") for t in mv.get("tagList", []) if isinstance(t, dict)],
            "cover": mv.get("coverVerticalUrl") or mv.get("coverHorizontalUrl", ""),
            "type": mv.get("drameTypeVo", {}).get("drameName", ""),
            "intro": (mv.get("introduction") or "")[:150],
        }
    return None

def scan_ids():
    import concurrent.futures
    clear()
    header("SCAN API")
    print("  1. Scan dari Home (rekomendasi API)")
    print("  2. Scan manual (range ID)")
    print("  0. Kembali")
    print()
    try:
        c = int(input("  Pilih mode: ").strip())
    except (ValueError, EOFError, KeyboardInterrupt):
        return
    if c == 1:
        scan_from_home()
    elif c == 2:
        scan_range()
    pause()

def scan_from_home():
    import concurrent.futures
    clear()
    header("SCAN FROM HOME")
    print("  Mengambil ID movie dari halaman beranda...")

    nav_ids = [1, 2, 3, 119, 120, 165]
    all_cids = set()
    for nav in nav_ids:
        r = make_api_call("GET", "/home/h5/getHome",
                          params={"navigationId": nav, "page": 0},
                          client_type="H5", version_code="32")
        if r.status_code != 200:
            print(f"  nav={nav}: HTTP {r.status_code}")
            continue
        d = r.json()
        if d.get("code") != "00000":
            print(f"  nav={nav}: {d.get('msg','?')}")
            continue
        items = []
        for sect in d.get("data", {}).get("recommendItems", []):
            for x in sect.get("recommendContentVOList", []):
                cid = x.get("cid") or x.get("id")
                if cid:
                    items.append(str(cid))
        all_cids.update(items)
        print(f"  nav={nav}: {len(items)} ID ditemukan")

    if not all_cids:
        print("\n  Tidak ada ID ditemukan dari Home.")
        return

    print(f"\n  Total {len(all_cids)} ID unik. Mengambil detail...")

    existing = {str(m["id"]) for m in load_movie_db()}
    new_ids = [cid for cid in all_cids if cid not in existing]
    print(f"  {len(new_ids)} ID baru, {len(all_cids) - len(new_ids)} sudah di DB.\n")

    if not new_ids:
        print("  Semua ID sudah ada di database.")
        return

    found = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=15) as ex:
        futs = {ex.submit(_fetch_movie, cid): cid for cid in new_ids}
        done = 0
        for fut in concurrent.futures.as_completed(futs):
            done += 1
            r = fut.result()
            if r:
                found.append(r)
                print(f"  [{done}/{len(new_ids)}] BARU: [{r['id']}] {r['title']} ({r['year']})")
            else:
                cid = futs[fut]
                print(f"  [{done}/{len(new_ids)}] GAGAL: ID {cid}")

    if found:
        from loklok_api_mobile import save_movie_db
        all_movies = load_movie_db() + found
        all_movies.sort(key=lambda m: int(m["id"]) if str(m["id"]).isdigit() else 0)
        save_movie_db(all_movies)
        print(f"\n  ✅ {len(found)} movie baru ditambahkan ke database!")
    else:
        print("\n  Tidak ada movie baru ditemukan.")

def scan_range():
    import concurrent.futures
    clear()
    header("SCAN RANGE")
    print("  Masukkan rentang ID untuk dipindai.\n")
    try:
        start = int(input("  ID mulai: ").strip())
        end = int(input("  ID akhir: ").strip())
    except (ValueError, EOFError, KeyboardInterrupt):
        return
    if start < 0 or end <= start or end - start > 1000:
        print("\n  Rentang tidak valid atau terlalu besar (max 1000).")
        return
    print(f"\n  Memindai {start}-{end}...")
    existing = {str(m["id"]) for m in load_movie_db()}
    found = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=15) as ex:
        futs = {ex.submit(_fetch_movie, i): i for i in range(start, end + 1)}
        for fut in concurrent.futures.as_completed(futs):
            r = fut.result()
            if r:
                found.append(r)
                sid = str(r["id"])
                if sid not in existing:
                    print(f"  BARU: [{r['id']}] {r['title']} ({r['year']})")
                else:
                    print(f"  SUDAH: [{r['id']}] {r['title']} ({r['year']})")
    new_movies = [m for m in found if str(m["id"]) not in existing]
    if new_movies:
        from loklok_api_mobile import save_movie_db
        all_movies = load_movie_db() + new_movies
        all_movies.sort(key=lambda m: int(m["id"]) if str(m["id"]).isdigit() else 0)
        save_movie_db(all_movies)
        print(f"\n  ✅ {len(new_movies)} movie baru ditambahkan ke database!")
    else:
        print(f"\n  Tidak ada movie baru ditemukan.")

# --- Movie detail & stream ---

def get_detail(mid):
    resp = get_movie_detail(mid, category=1)
    data = resp.json()
    if data.get("code") == "00000" and data.get("data"):
        return data["data"], 1
    resp = get_movie_detail(mid, category=0)
    data = resp.json()
    if data.get("code") == "00000" and data.get("data"):
        return data["data"], 0
    return None, None

def detail_movie(cid):
    if not cid:
        print("\n  ID tidak valid.")
        pause()
        return
    mv, cat = get_detail(cid)
    if mv is None:
        print(f"\n  Movie tidak ditemukan (ID: {cid})")
        pause()
        return
    judul = mv.get("title") or mv.get("enName") or mv.get("name", "?")
    alias = mv.get("aliasName", "")
    tahun = mv.get("year", "")
    negara = ", ".join(a.get("name", "") for a in mv.get("areaList", []) if isinstance(a, dict))
    intro = mv.get("introduction", "")
    eps = mv.get("episodeVo", [])
    jml = mv.get("episodeCount", len(eps))

    while True:
        clear()
        header(judul)
        if alias:
            print(f"  Alias   : {alias}")
        if tahun:
            print(f"  Tahun   : {tahun}")
        if negara:
            print(f"  Negara  : {negara}")
        print(f"  Episode : {jml}")
        tipe = mv.get("drameTypeVo", {})
        if tipe:
            print(f"  Tipe    : {tipe.get('drameName', '')}")
        if intro:
            s = intro[:250] + "..." if len(intro) > 250 else intro
            print(f"\n  {s}")
        print()
        for i, ep in enumerate(eps[:20], 1):
            sn = ep.get("seriesNo", i)
            view = "Y" if ep.get("viewable") else "N"
            defs = ", ".join(d.get("code", "") for d in ep.get("definitionList", []))
            line = f"  {sn:3}. [{view}] EP-{sn}"
            if defs:
                line += f"  {defs}"
            print(line)
        if len(eps) > 20:
            print(f"  ... +{len(eps)-20} episode")
        print()
        try:
            c = int(input("  Pilih episode (0 kembali): "))
            if c == 0:
                return
            if 1 <= c <= len(eps):
                ep = eps[c-1]
                stream_url(cid, ep.get("id"), judul, ep.get("seriesNo", c), cat,
                           detail_subs=ep.get("subtitlingList") or [])
        except (ValueError, EOFError, KeyboardInterrupt):
            return

QUALITY_MAP = {
    "GROOT_HD": ("1080P", 0),
    "GROOT_SD": ("720P", 1),
    "GROOT_LD": ("540P", 2),
    "GROOT_FD": ("360P", 3),
}

def stream_url(mid, eid, judul, enum, category=1, detail_subs=None):
    if not eid:
        print("\n  Episode ID tidak ditemukan.")
        pause()
        return

    quals = get_all_qualities(mid, eid, category)
    if not quals:
        print("\n  Gagal mengambil URL stream.")
        pause()
        return

    clear()
    header("STREAM URL")
    print(f"  Judul   : {judul}")
    print(f"  Episode : {enum}")
    print()

    sorted_quals = sorted(quals.items(),
                          key=lambda x: QUALITY_MAP.get(x[0], (x[0], 99))[1])
    urls = []
    for code, (url, dur, subs) in sorted_quals:
        label, _ = QUALITY_MAP.get(code, (code, 99))
        if url:
            dur_str = f" ({dur // 60}m)" if dur else ""
            print(f"  [{len(urls)+1}] {label}{dur_str}")
            urls.append((label, url, subs, code))
        else:
            print(f"  [ ] {label} — tidak tersedia")

    print()
    if not urls:
        print("  Tidak ada stream URL tersedia.")
        pause()
        return

    print("  [0] Kembali")
    print()
    try:
        a = int(input("  Pilih kualitas: "))
        if a == 0:
            return
        if 1 <= a <= len(urls):
            label, url, play_subs = urls[a-1][:3]
            clear()
            header(f"{judul} — {label}")
            print(f"  URL: {url}\n")
            src = detail_subs or play_subs
            idn = [s for s in src if isinstance(s, dict) and s.get("languageAbbr") == "in_ID" and s.get("subtitlingUrl")]
            eng = [s for s in src if isinstance(s, dict) and s.get("languageAbbr") == "en" and s.get("subtitlingUrl")]
            shown = idn + eng
            if shown:
                print("  Subtitle:")
                for s in shown:
                    lang = s.get("language") or s.get("languageAbbr") or ""
                    su = s.get("subtitlingUrl") or ""
                    print(f"    {lang}: {su}")
                print()
            print("  [1] Salin URL stream")
            print("  [2] Buka di browser")
            sub_options = []
            for s in shown:
                su = s.get("subtitlingUrl") or ""
                if su:
                    lang = s.get("language") or s.get("languageAbbr") or "?"
                    sub_options.append((lang, su))
            for i, (lang, _) in enumerate(sub_options, 1):
                print(f"  [{i+2}] Salin subtitle ({lang})")
            serve_idx = len(sub_options) + 3
            print(f"  [{serve_idx}] Serve stream (M3U8)")
            print("  [0] Kembali")
            print()
            try:
                b = input("  Pilih: ").strip()
                if b == "0":
                    return
                if b == "1":
                    salin(url)
                elif b == "2":
                    import webbrowser
                    webbrowser.open(url)
                    print("  Membuka browser...")
                    pause()
                elif b.isdigit():
                    bi = int(b)
                    if bi == serve_idx:
                        serve_stream(url, sub_options, judul)
                    elif 3 <= bi <= 2 + len(sub_options):
                        _, su = sub_options[bi - 3]
                        salin(su)
            except (ValueError, EOFError, KeyboardInterrupt):
                pass
    except (ValueError, EOFError, KeyboardInterrupt):
        pass

def serve_stream(stream_url, sub_options, title):
    import threading, re
    import requests as req
    from http.server import HTTPServer, BaseHTTPRequestHandler

    host = STREAM_HOST
    port = STREAM_PORT

    m3u8_lines = ["#EXTM3U", "#EXT-X-VERSION:6"]
    if sub_options:
        for i, (lang, _) in enumerate(sub_options):
            abbr = "in_ID" if i == 0 else "en"
            default = "YES" if i == 0 else "NO"
            uri = f"http://{host}:{port}/sub/{i}.vtt"
            m3u8_lines.append(f'#EXT-X-MEDIA:TYPE=SUBTITLES,GROUP-ID="subs",NAME="{lang}",DEFAULT={default},AUTOSELECT={default},LANGUAGE="{abbr}",URI="{uri}"')
        m3u8_lines.append(f'#EXT-X-STREAM-INF:BANDWIDTH=8000000,SUBTITLES="subs"')
    else:
        m3u8_lines.append('#EXT-X-STREAM-INF:BANDWIDTH=8000000')
    m3u8_lines.append(stream_url)
    m3u8_content = "\n".join(m3u8_lines) + "\n"

    req.packages.urllib3.disable_warnings()
    vtt_cache = {}

    class Handler(BaseHTTPRequestHandler):
        def do_GET(self):
            if self.path == "/stream.m3u8":
                self._m3u8()
            elif self.path.startswith("/sub/"):
                self._subtitle()
            else:
                self.send_error(404)

        def _m3u8(self):
            self.send_response(200)
            self.send_header("Content-Type", "application/vnd.apple.mpegurl")
            self.end_headers()
            self.wfile.write(m3u8_content.encode())

        def _subtitle(self):
            try:
                idx = int(self.path.split("/")[-1].split(".")[0])
                if not (0 <= idx < len(sub_options)):
                    raise ValueError
            except (ValueError, IndexError):
                self.send_error(404)
                return

            if idx not in vtt_cache:
                _, srt_url = sub_options[idx]
                try:
                    r = req.get(srt_url, verify=False, timeout=10)
                    if r.status_code != 200:
                        self.send_error(502)
                        return
                    vtt = "WEBVTT\n\n" + re.sub(r'(\d{2}:\d{2}:\d{2}),(\d{3})', r'\1.\2', r.text)
                    vtt_cache[idx] = vtt
                except Exception:
                    self.send_error(502)
                    return

            self.send_response(200)
            self.send_header("Content-Type", "text/vtt; charset=utf-8")
            self.end_headers()
            self.wfile.write(vtt_cache[idx].encode("utf-8"))

        def log_message(self, fmt, *args):
            pass

    server = HTTPServer(("0.0.0.0", port), Handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()

    clear()
    header("STREAM SERVER")
    print(f"  Judul : {title}")
    print(f"  URL   : http://{host}:{port}/stream.m3u8")
    print(f"\n  Buka URL di atas di VLC/mpv/IINA.")
    print(f"\n  Tekan Enter untuk berhenti...")
    input()

    server.shutdown()
    server.server_close()


def salin(url):
    import subprocess
    try:
        proc = subprocess.Popen(["xclip", "-selection", "clipboard"],
                                stdin=subprocess.PIPE)
        proc.communicate(input=url.encode())
        print("  URL disalin ke clipboard!")
    except FileNotFoundError:
        try:
            proc = subprocess.Popen(["pbcopy"], stdin=subprocess.PIPE)
            proc.communicate(input=url.encode())
            print("  URL disalin ke clipboard!")
        except FileNotFoundError:
            print("  Clipboard tidak tersedia. Salin manual:")
            print(f"  {url}")
    pause()

# --- Settings ---

def settings_menu():
    global STREAM_HOST, STREAM_PORT
    while True:
        clear()
        header("SETTINGS")
        print(f"  [1] Host stream : {STREAM_HOST}")
        print(f"  [2] Port stream : {STREAM_PORT}")
        print()
        print("  [0] Kembali")
        print()
        try:
            c = int(input("  Pilih: ").strip())
            if c == 0:
                return
            elif c == 1:
                h = input(f"  Host [{STREAM_HOST}]: ").strip()
                if h:
                    STREAM_HOST = h
            elif c == 2:
                p = input(f"  Port [{STREAM_PORT}]: ").strip()
                if p:
                    pn = int(p)
                    if 1024 <= pn <= 65535:
                        STREAM_PORT = pn
                    else:
                        print("  Port harus 1024-65535")
                        pause()
        except ValueError:
            print("  Port harus angka")
            pause()
        except (EOFError, KeyboardInterrupt):
            return


# --- Menu utama ---

def main():
    ops = [
        ("Cari Movie", search_movie),
        ("Category", browse_category),
        ("Tahun", browse_year),
        ("Negara", browse_country),
        ("Login" if not is_logged_in() else "Logout", do_login if not is_logged_in() else do_logout),
        ("Scan API", scan_ids),
        ("Settings", settings_menu),
    ]
    while True:
        r = pilih(ops, "LOKLOK STREAM CLI")
        if r == "back":
            break
    print("\n  Sampai jumpa!")

def main_cli():
    import argparse
    parser = argparse.ArgumentParser(description="Loklok Stream CLI")
    parser.add_argument("--id", type=str, help="ID movie untuk langsung lihat detail")
    parser.add_argument("--episode", type=int, help="Nomor episode (dengan --id)")
    parser.add_argument("--login", action="store_true", help="Login dulu")
    parser.add_argument("--email", type=str, help="Email untuk login")
    parser.add_argument("--pwd", type=str, help="Password untuk login")
    args = parser.parse_args()

    if args.login and args.email and args.pwd:
        result = api_login(args.email, args.pwd)
        if result:
            print(f"Login berhasil: {result.get('userName', '?')}")
        else:
            print("Login gagal.")
            return

    if args.id:
        if args.episode:
            resp = get_movie_detail(args.id, category=1)
            data = resp.json()
            if data.get("code") == "00000":
                eps = data.get("data", {}).get("episodeVo", [])
                for ep in eps:
                    if ep.get("seriesNo") == args.episode:
                        stream_url(args.id, ep.get("id"),
                                   data["data"].get("enName") or args.id,
                                   args.episode)
                        return
            print(f"  Episode {args.episode} tidak ditemukan untuk ID {args.id}")
            return
        detail_movie(args.id)
        return

    try:
        main()
    except (KeyboardInterrupt, EOFError):
        print("\n  Keluar...")

if __name__ == "__main__":
    main_cli()
