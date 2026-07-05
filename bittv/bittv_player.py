import json, os, subprocess, sys, shutil, time, base64, urllib.request

CACHE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")
CONFIG_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "config.json")

B64TABLE = {c: i for i, c in enumerate(b'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/')}

def clear():
    os.system("cls" if os.name == "nt" else "clear")

def tw():
    return shutil.get_terminal_size().columns

def header(title):
    w = tw()
    print("=" * w)
    print(f"  {title}")
    print("=" * w)

def progress_msg(msg):
    w = tw()
    print(f"\r  {msg:<{w-2}}", end="", flush=True)

def done_msg(msg):
    w = tw()
    print(f"\r  {msg:<{w-2}}")

def load_config():
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE) as f:
            cfg = json.load(f)
        if "ffplay_path" in cfg:
            cfg["player_path"] = cfg.pop("ffplay_path")
            save_config(cfg)
        return cfg
    return {"player_path": ""}

def save_config(cfg):
    with open(CONFIG_FILE, "w") as f:
        json.dump(cfg, f)

def find_player(custom=""):
    if custom and os.path.isfile(custom):
        return custom
    local = os.path.join(os.path.dirname(os.path.abspath(__file__)), "mpv", "mpv.exe")
    if os.path.isfile(local):
        return local
    found = shutil.which("mpv")
    if found:
        return found
    return ""

def find_ffmpeg():
    local = os.path.join(os.path.dirname(os.path.abspath(__file__)), "ffmpeg", "ffmpeg.exe")
    if os.path.isfile(local):
        return local
    found = shutil.which("ffmpeg")
    if found:
        return found
    return ""

def b64decode_lenient(s):
    filtered = bytes(c for c in s if c in B64TABLE)
    if not filtered:
        return b""
    padding = (4 - len(filtered) % 4) % 4
    if padding:
        filtered += b"=" * padding
    return base64.b64decode(filtered)

DECRYPT_PY = os.path.join(os.path.dirname(os.path.abspath(__file__)), "decrypt.py")

def load_country_data(code, force=False):
    dec_path = os.path.join(CACHE_DIR, f"{code}_decrypted.json")
    raw_path = os.path.join(CACHE_DIR, f"{code}.json")
    cache_ok = os.path.exists(dec_path) and os.path.exists(raw_path)
    if cache_ok and not force:
        try:
            cache_ok = time.time() - os.path.getmtime(raw_path) <= 3600
        except:
            cache_ok = False
    if not cache_ok:
        progress_msg(f"Decrypting {code}.json...")
        try:
            ret = subprocess.run([sys.executable, DECRYPT_PY, code], timeout=120)
            if ret.returncode != 0:
                done_msg(f"FAILED {code}.json")
                return [], {}
        except FileNotFoundError:
            done_msg("FAILED: decrypt.py not found")
            return [], {}
        except subprocess.TimeoutExpired:
            done_msg("FAILED: decrypt.py timed out")
            return [], {}
    try:
        with open(dec_path, encoding="utf-8") as f:
            d = json.load(f)
    except:
        return [], {}
    channels = d.get("info", [])
    countrylist = d.get("country_list", d.get("countrylist", []))
    return channels, countrylist

def decode_ck(b64):
    if not b64:
        return None
    try:
        d = json.loads(b64decode_lenient(b64.encode("ascii")).decode("utf-8"))
        if "keys" in d and d["keys"]:
            k = d["keys"][0]
            kh = b64decode_lenient(k.get("k", "").encode("ascii")).hex()
            kidh = b64decode_lenient(k.get("kid", "").encode("ascii")).hex()
            return {"key": kh, "kid": kidh, "type": d.get("type", "temporary")}
    except:
        pass
    return None



def test_url(url, hdrs=None):
    result = {"alive": False, "code": 0, "error": ""}
    if not url:
        result["error"] = "URL kosong"
        return result
    hdrs = hdrs or {}
    req = urllib.request.Request(url, method="HEAD")
    for k, v in hdrs.items():
        if v and v != "none":
            req.add_header(k, v)
    req.add_header("User-Agent", "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Firefox/128.0")
    try:
        resp = urllib.request.urlopen(req, timeout=15)
        result["code"] = resp.getcode()
        result["alive"] = 200 <= result["code"] < 400
    except urllib.error.HTTPError as e:
        result["code"] = e.code
        result["error"] = f"HTTP {e.code}"
    except urllib.error.URLError as e:
        result["error"] = f"Connection failed: {e.reason}"
    except Exception as e:
        result["error"] = str(e)
    return result

def parse_hdrs(s):
    if not s or s in ("none", '{"x-data":"none"}'):
        return {}
    try:
        return json.loads(s)
    except:
        return {}

def play_ff(url, hdrs, ck, path, jenis=""):
    cmd = [path, "-v"]
    for k, v in hdrs.items():
        if v and v != "none":
            if k.lower() == "user-agent":
                cmd.append(f"--user-agent={v}")
            else:
                cmd.append(f"--http-header-fields={k}: {v}")
    if ck and jenis == "dash-clearkey":
        cmd.append(f"--demuxer-lavf-o=cenc_decryption_key={ck['key']}")
    cmd.append(url)
    print(f"  $ {' '.join(cmd)}")
    try:
        subprocess.run(cmd)
        return True
    except Exception as e:
        print(f"  Gagal: {e}")
        return False

def play(ch, cfg):
    jenis = ch.get("jenis", "hls")
    url = ch.get("hls", "")
    hdrs = parse_hdrs(ch.get("header_iptv", ""))
    fp = cfg.get("player_path") or find_player()
    print()
    header(f"Now Playing: {ch['name']}")
    print(f"  URL  : {url}")
    print(f"  Type : {jenis}")
    if hdrs:
        print(f"  Headers:")
        for k, v in hdrs.items():
            print(f"    {k}: {v}")
    if not url:
        print("  ERROR: Stream URL kosong!")
        input("  Enter...")
        return
    if not fp:
        print("  ERROR: mpv tidak ditemukan. Install mpv atau set path di Settings.")
        input("  Enter...")
        return
    ck = decode_ck(ch.get("url_license", "")) if jenis == "dash-clearkey" else None
    if ck:
        print(f"  DRM: ClearKey (kid={ck['kid'][:16]}... key={ck['key'][:16]}...)")
    print()
    print("  >> Testing link...")
    r = test_url(url, hdrs)
    if r["alive"]:
        print(f"  STATUS: \033[92mALIVE\033[0m (HTTP {r['code']})")

        c = input("  > Launch mpv? [Y/n]: ").strip().upper()
        if c != "N":
            play_ff(url, hdrs, ck, fp, jenis)
        else:
            print("  Dibatalkan.")
    else:
        print(f"  STATUS: \033[91mDOWN\033[0m ({r['error']})")
    input("  Enter...")

def server_stream(ch, cfg):
    import socket, threading
    from http.server import HTTPServer, BaseHTTPRequestHandler

    url = ch.get("hls", "")
    jenis = ch.get("jenis", "hls")
    hdrs = parse_hdrs(ch.get("header_iptv", ""))
    ck = decode_ck(ch.get("url_license", "")) if jenis == "dash-clearkey" else None

    if not url:
        print("  ERROR: Stream URL kosong!")
        return

    ff = cfg.get("ffmpeg_path") or find_ffmpeg()
    if not ff:
        print("  ERROR: ffmpeg tidak ditemukan!")
        return

    try:
        p = input("  Port [8080]: ").strip()
        port = int(p) if p else 8080
    except:
        port = 8080

    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(("8.8.8.8", 80))
        local_ip = s.getsockname()[0]
    except:
        local_ip = "127.0.0.1"
    finally:
        s.close()

    tmpdir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "stream")
    os.makedirs(tmpdir, exist_ok=True)

    cmd = [ff]
    for k, v in hdrs.items():
        if v and v != "none":
            if k.lower() == "user-agent":
                cmd.extend(["-user_agent", v])
            else:
                cmd.extend(["-headers", f"{k}: {v}"])
    if ck:
        cmd.extend(["-cenc_decryption_key", ck["key"]])
    cmd.extend(["-i", url, "-c", "copy", "-f", "hls",
                "-hls_list_size", "20", "-hls_flags", "delete_segments",
                "stream.m3u8"])

    print(f"  $ {' '.join(cmd)}")
    try:
        proc = subprocess.Popen(cmd, cwd=tmpdir)
    except Exception as e:
        print(f"  ERROR: Gagal start ffmpeg: {e}")
        shutil.rmtree(tmpdir, ignore_errors=True)
        return

    class StreamHandler(BaseHTTPRequestHandler):
        def do_GET(self):
            p = self.path
            if p == "/":
                self.send_response(200)
                self.send_header("Content-Type", "text/html; charset=utf-8")
                self.end_headers()
                info = f"""<html><body>
<h1>BitTV Stream Server</h1>
<p>Channel: <b>{ch.get('name', '?')}</b></p>
<p>Type: {jenis}</p>
<p><a href="stream.m3u8">stream.m3u8</a></p>"""
                if ck:
                    info += f"<p>DRM ClearKey:</p><pre>kid={ck['kid']}\nkey={ck['key']}</pre>"
                info += "</body></html>"
                self.wfile.write(info.encode("utf-8"))
            else:
                fp = os.path.normpath(os.path.join(tmpdir, p.lstrip("/")))
                if fp.startswith(tmpdir) and os.path.isfile(fp):
                    ext = os.path.splitext(p)[1].lstrip(".")
                    ct = {"ts": "video/MP2T", "m3u8": "application/vnd.apple.mpegurl", "mp4": "video/mp4"}.get(ext, "application/octet-stream")
                    try:
                        with open(fp, "rb") as f:
                            self.send_response(200)
                            self.send_header("Content-Type", ct)
                            self.end_headers()
                            self.wfile.write(f.read())
                    except:
                        self.send_error(404)
                else:
                    self.send_error(404)
        def log_message(self, fmt, *args):
            print(f"    [{self.client_address[0]}] {fmt % args}")

    try:
        server = HTTPServer(("0.0.0.0", port), StreamHandler)
    except OSError:
        print(f"  ERROR: Port {port} sudah dipakai!")
        proc.kill()
        shutil.rmtree(tmpdir, ignore_errors=True)
        return

    t_srv = threading.Thread(target=server.serve_forever, daemon=True)
    t_srv.start()

    print(f"\n  Server Stream: http://{local_ip}:{port}/")
    print(f"  Folder: {tmpdir}")
    print(f"  M3U8 Playlist: http://{local_ip}:{port}/stream.m3u8")
    if ck:
        print(f"  DRM ClearKey : kid={ck['kid']}")
        print(f"                 key={ck['key']}")
        print("  mpv device lain: mpv --demuxer-lavf-o=cenc_decryption_key=KEY http://IP:PORT/stream.m3u8")
    print("  Press Enter to stop...")
    try:
        input()
    except:
        pass
    finally:
        proc.kill()
        server.shutdown()
        for f in os.listdir(tmpdir):
            try:
                os.remove(os.path.join(tmpdir, f))
            except:
                pass
        print("  Server stopped. stream/ cleaned.")

def detail(ch, cfg):
    clear()
    header("Channel Detail")
    print(f"  ID        : {ch.get('id', '-')}")
    print(f"  Name      : {ch.get('name', '-')}")
    print(f"  Tagline   : {ch.get('tagline', '-')}")
    print(f"  URL       : {ch.get('hls', '-')}")
    print(f"  Type      : {ch.get('jenis', '-')}")
    print(f"  Premium   : {'Yes' if ch.get('premium') == 't' else 'No'}")
    print(f"  Country   : {ch.get('country_name', '-')} ({ch.get('alpha_2_code', '-')})")
    print(f"  Live      : {'Yes' if ch.get('is_live') == 't' else 'No'}")
    if ch.get("t_stamp"):
        try:
            ts = int(ch["t_stamp"])
            if ts > 0:
                import datetime
                print(f"  Event     : {datetime.datetime.fromtimestamp(ts).strftime('%Y-%m-%d %H:%M')}")
        except (ValueError, TypeError):
            pass
    hdrs = parse_hdrs(ch.get("header_iptv", ""))
    if hdrs:
        print(f"  Headers   :")
        for k, v in hdrs.items():
            print(f"    {k}: {v}")
    if ch.get("url_license"):
        ck = decode_ck(ch["url_license"])
        if ck:
            print(f"  DRM       : ClearKey ({ck['type']})")
            print(f"    Key ID  : {ck['kid']}")
            print(f"    Key     : {ck['key']}")
    print()
    print("  [T] Test Link")
    print("  [P] Play")
    print("  [S] Server Stream")
    print("  [B] Back")
    c = input("  Pilih: ").strip().upper()
    if c == "T":
        r = test_url(ch.get("hls", ""), hdrs)
        if r["alive"]:
            print(f"\n  STATUS: \033[92mALIVE\033[0m (HTTP {r['code']})")
        else:
            print(f"\n  STATUS: \033[91mDOWN\033[0m ({r['error']})")
        input("  Enter...")
    elif c == "P":
        play(ch, cfg)
    elif c == "S":
        server_stream(ch, cfg)

def list_channels(chs, cfg, title="Channels"):
    pp = 10
    pg = 0
    while True:
        clear()
        header(title)
        tot = len(chs)
        s = pg * pp
        e = min(s + pp, tot)
        for i, ch in enumerate(chs[s:e], s + 1):
            j = ch.get("jenis", "?")
            live = "LIVE" if ch.get("is_live") == "t" else "   "
            print(f"  {i:>3}. [{live}] [{j:14}] {ch.get('name', '?')}")
        print(f"\n  Page {pg + 1}/{(tot - 1) // pp + 1} ({tot})")
        print(f"  [N] Next  [P] Prev  [num] Select  [S] Search  [F] Filter  [L] Live only  [T] Test Page  [Q] Back")
        c = input("  Pilih: ").strip().upper()
        if c == "N" and e < tot:
            pg += 1
        elif c == "P" and pg > 0:
            pg -= 1
        elif c == "L":
            live_chs = [ch for ch in chs if ch.get("is_live") == "t"]
            if live_chs:
                list_channels(live_chs, cfg, f"Live Events ({len(live_chs)})")
            else:
                print("  Tidak ada live event.")
                input("  Enter...")
        elif c == "S":
            q = input("  Cari: ").strip().lower()
            if q:
                flt = [ch for ch in chs if q in ch.get("name", "").lower() or q == ch.get("id", "")]
                if flt:
                    list_channels(flt, cfg, f"Search: '{q}'")
        elif c == "F":
            print("  1. All  2. HLS  3. DASH  4. DASH-ClearKey  5. TS  6. Live Events")
            f = input("  Pilih: ").strip()
            m = {"2": "hls", "3": "dash", "4": "dash-clearkey", "5": "ts"}
            if f == "6":
                flt = [ch for ch in chs if ch.get("is_live") == "t"]
                if flt:
                    list_channels(flt, cfg, "Live Events")
            elif f in m:
                flt = [ch for ch in chs if ch.get("jenis") == m[f]]
                list_channels(flt, cfg, f"Filter: {m[f]}")
        elif c == "T":
            print()
            for i, ch in enumerate(chs[s:e], s + 1):
                print(f"  Testing {i}. {ch['name']}... ", end="")
                r = test_url(ch.get("hls", ""), parse_hdrs(ch.get("header_iptv", "")))
                if r["alive"]:
                    print(f"\033[92mALIVE\033[0m ({r['code']})")
                else:
                    print(f"\033[91mDOWN\033[0m ({r['error']})")
            input("  Enter...")
        elif c == "Q":
            return
        else:
            try:
                n = int(c)
                if 1 <= n <= tot:
                    detail(chs[n - 1], cfg)
            except ValueError:
                pass

def cache_size():
    total = 0
    for f in os.listdir(CACHE_DIR):
        p = os.path.join(CACHE_DIR, f)
        if os.path.isfile(p):
            total += os.path.getsize(p)
    return total

def settings(cfg, countries, on_country_change=None):
    while True:
        clear()
        header("Settings")
        f = cfg.get("player_path", "") or "(auto)"
        def_c = cfg.get("country", "")
        def_c_name = countries.get(def_c, "(none)") if def_c else "(none)"
        print(f"  1. Player path    : {f}")
        print(f"  2. Default country : {def_c_name} [{def_c or '-'}]")
        print(f"  3. Clear cache")
        print(f"  4. Info")
        print(f"  Q. Back")
        c = input("  Pilih: ").strip().upper()
        if c == "1":
            p = input("  Player path: ").strip()
            if p and not os.path.isfile(p):
                print(f"  Warning: file tidak ditemukan: {p}")
            cfg["player_path"] = p
            save_config(cfg)
            input("  Enter...")
        elif c == "2":
            clear()
            header("Select Default Country")
            sorted_c = sorted(countries.items(), key=lambda x: x[1])
            print("  0. (none)")
            for i, (code, name) in enumerate(sorted_c, 1):
                print(f"  {i:>2}. [{code}] {name}")
            try:
                sel = int(input("  Pilih: ").strip())
                new_code = None
                if sel == 0:
                    cfg.pop("country", None)
                elif 1 <= sel <= len(sorted_c):
                    new_code = sorted_c[sel - 1][0]
                    cfg["country"] = new_code
                save_config(cfg)
                if new_code and on_country_change:
                    on_country_change(new_code)
            except ValueError:
                pass
        elif c == "3":
            sz = cache_size()
            if sz == 0:
                print("  Cache sudah kosong.")
            else:
                print(f"  Ukuran cache: {sz/1024:.0f} KB")
                konf = input("  Hapus semua? [y/N]: ").strip().upper()
                if konf == "Y":
                    for f in os.listdir(CACHE_DIR):
                        fp = os.path.join(CACHE_DIR, f)
                        if os.path.isfile(fp):
                            os.remove(fp)
                    print("  Cache cleared!")
            input("  Enter...")
        elif c == "4":
            clear()
            header("Info")
            print("  BitTV Player v2.0")
            print(f"  Player : {find_player() or 'NOT FOUND'}")
            print(f"  FFmpeg : {find_ffmpeg() or 'NOT FOUND'}")
            print(f"  Cache  : {cache_size()/1024:.0f} KB ({len(os.listdir(CACHE_DIR))} files)")
            print(f"  Config : {CONFIG_FILE}")
            print(f"  Countries: {len(countries)}")
            print(f"  Available codes: {', '.join(sorted(countries))} + AN, EV (alias ID)")
            input("  Enter...")
        elif c == "Q":
            save_config(cfg)
            return

def main():
    cfg = load_config()
    if not cfg.get("player_path"):
        fb = find_player()
        if fb:
            cfg["player_path"] = fb
            save_config(cfg)
    if not cfg.get("ffmpeg_path"):
        fb_ff = find_ffmpeg()
        if fb_ff:
            cfg["ffmpeg_path"] = fb_ff
            save_config(cfg)

    default_country = cfg.get("country", "")
    if not default_country:
        cfg["country"] = "ID"
        save_config(cfg)
        default_country = "ID"

    os.makedirs(CACHE_DIR, exist_ok=True)
    chs, countrylist_raw = load_country_data(default_country)
    if not chs and not countrylist_raw:
        print("  ERROR: Gagal decrypt default country!")
        sys.exit(1)

    country_cache = {}
    seen_ids = set()
    chs = [ch for ch in chs if ch.get("id") not in seen_ids]
    for ch in chs:
        seen_ids.add(ch.get("id"))
    country_cache[default_country] = chs

    sp_countries = {}
    for c in countrylist_raw:
        code = c.get("alpha_2_code") or c.get("alpha_2", "")
        name = c.get("country_name") or c.get("name", "") or code
        if code:
            sp_countries[code] = name
    if default_country not in sp_countries:
        sp_countries[default_country] = default_country

    COUNTRY_SOURCE = {code: code for code in sp_countries}
    COUNTRY_SOURCE["AN"] = "ID"
    COUNTRY_SOURCE["EV"] = "ID"

    if default_country not in sp_countries:
        cfg["country"] = "ID"
        save_config(cfg)
        default_country = "ID"

    if not cfg.get("ffmpeg_path"):
        print("  Warning: ffmpeg tidak ditemukan -- Server Stream tidak tersedia.\n")

    def all_channels():
        ch = []
        for src_chs in country_cache.values():
            ch.extend(src_chs)
        return ch

    def channels_for_code(code):
        result = []
        for src_chs in country_cache.values():
            result.extend(ch for ch in src_chs if ch.get("alpha_2_code") == code)
        return result

    def ensure_code_loaded(code):
        if code not in COUNTRY_SOURCE:
            return
        src = COUNTRY_SOURCE[code]
        if src not in country_cache:
            chs, _ = load_country_data(src)
            chs = [ch for ch in chs if ch.get("id") not in seen_ids]
            for ch in chs:
                seen_ids.add(ch.get("id"))
            country_cache[src] = chs

    def ensure_all_countries_loaded():
        for src in sorted(set(COUNTRY_SOURCE.values())):
            if src not in country_cache:
                chs, _ = load_country_data(src)
                chs = [ch for ch in chs if ch.get("id") not in seen_ids]
                for ch in chs:
                    seen_ids.add(ch.get("id"))
                country_cache[src] = chs

    sorted_countries = sorted(sp_countries.items(), key=lambda x: x[1])

    while True:
        chs = all_channels()
        total = len(chs)
        live = sum(1 for c in chs if c.get("is_live") == "t")
        jenis = {}
        for c in chs:
            t = c.get("jenis", "?")
            jenis[t] = jenis.get(t, 0) + 1
        jenis_str = " | ".join(f"{k.upper()}: {v}" for k, v in sorted(jenis.items()))
        src_info = " + ".join(sorted(country_cache.keys())) if country_cache else "(none)"

        clear()
        header("BitTV Player v2.0")
        print(f"  {total} channels | {live} LIVE")
        print(f"  {jenis_str}")
        print(f"  Countries: {len(sorted_countries)}  |  Loaded: {src_info}")
        def_country = cfg.get("country", "")
        if def_country and def_country in sp_countries:
            print(f"  Default: {sp_countries[def_country]} [{def_country}]")
        print()
        print("  [1] Browse All Channels")
        print("  [2] Browse by Country")
        print("  [3] Live Events")
        print("  [4] Search")
        print("  [5] Filter by Type")
        print("  [6] Refresh")
        print("  [7] Settings")
        print("  [Q] Quit")
        c = input("\n  Pilih: ").strip().upper()

        if c == "1":
            if chs:
                list_channels(chs, cfg, f"All Channels ({total})")
            else:
                print("  Tidak ada channel. Pilih negara dulu via [2].")
                input("  Enter...")

        elif c == "2":
            while True:
                clear()
                header("Select Country")
                for i, (code, name) in enumerate(sorted_countries, 1):
                    cnt = len(channels_for_code(code))
                    print(f"  {i:>2}. [{code}] {name} ({cnt})")
                print(f"\n  {len(sorted_countries)+1}. Back")
                try:
                    sel = int(input("  Pilih: ").strip())
                    if 1 <= sel <= len(sorted_countries):
                        code, name = sorted_countries[sel - 1]
                        ensure_code_loaded(code)
                        flt = channels_for_code(code)
                        if flt:
                            list_channels(flt, cfg, f"{name} ({code}) - {len(flt)}")
                        else:
                            print(f"  Tidak ada channel untuk {name}.")
                            input("  Enter...")
                    elif sel == len(sorted_countries) + 1:
                        break
                except ValueError:
                    pass
                except:
                    break

        elif c == "3":
            ensure_all_countries_loaded()
            live_chs = [c for c in all_channels() if c.get("is_live") == "t"]
            if live_chs:
                live_chs.sort(key=lambda x: int(x.get("t_stamp", "0") or "0"))
                list_channels(live_chs, cfg, f"Live Events ({len(live_chs)})")
            else:
                print("  Tidak ada live event.")
                input("  Enter...")

        elif c == "4":
            q = input("  Cari: ").strip().lower()
            if q:
                flt = [c for c in chs if q in c.get("name", "").lower() or q == c.get("id", "")]
                if flt:
                    list_channels(flt, cfg, f"Search: '{q}' ({len(flt)})")
                else:
                    print("  Tidak ada hasil.")
                    input("  Enter...")

        elif c == "5":
            print("  1. HLS  2. DASH  3. DASH-ClearKey  4. TS  5. Live Events")
            f = input("  Pilih: ").strip()
            m = {"1": "hls", "2": "dash", "3": "dash-clearkey", "4": "ts"}
            if f == "5":
                ensure_all_countries_loaded()
                flt = [c for c in all_channels() if c.get("is_live") == "t"]
                if flt:
                    list_channels(flt, cfg, f"Live Events ({len(flt)})")
            elif f in m:
                flt = [c for c in chs if c.get("jenis") == m[f]]
                list_channels(flt, cfg, f"Filter: {m[f].upper()} ({len(flt)})")

        elif c == "6":
            country_cache.clear()
            seen_ids.clear()
            dc = cfg.get("country", "ID")
            chs, countrylist_raw = load_country_data(dc, force=True)
            if countrylist_raw:
                new_ctry = {}
                for c2 in countrylist_raw:
                    code = c2.get("alpha_2_code") or c2.get("alpha_2", "")
                    name = c2.get("country_name") or c2.get("name", "") or code
                    if code:
                        new_ctry[code] = name
                if dc not in new_ctry:
                    new_ctry[dc] = dc
                sp_countries = new_ctry
                COUNTRY_SOURCE.clear()
                COUNTRY_SOURCE.update({code: code for code in sp_countries})
                COUNTRY_SOURCE["AN"] = "ID"
                COUNTRY_SOURCE["EV"] = "ID"
                sorted_countries = sorted(sp_countries.items(), key=lambda x: x[1])
            chs = [ch for ch in chs if ch.get("id") not in seen_ids]
            for ch in chs:
                seen_ids.add(ch.get("id"))
            country_cache[dc] = chs
            print()
            input("  Enter...")

        elif c == "7":
            def _switch_country(code):
                country_cache.clear()
                seen_ids.clear()
                ensure_code_loaded(code)
            settings(cfg, sp_countries, _switch_country)
            save_config(cfg)

        elif c == "Q":
            print("  Sampai jumpa!")
            break

if __name__ == "__main__":
    main()
