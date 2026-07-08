# AGENTS.md — Loklok Stream CLI

## Quick start
```bash
pip install requests pycryptodome
python cli.py                          # interactive menu
python cli.py --id 25016               # movie detail
python cli.py --id 25016 --episode 1   # stream URL for episode
python cli.py --login --email x --pwd y
python cookie_gen.py --email x --pwd y --format console
```

## Architecture
- **`cli.py`** — interactive TUI + argparse entrypoint. Entry: `main_cli()`.
- **`loklok_api_mobile.py`** — primary API client (`clientType=ANDROID`, `versionCode=42`) with RSA+AES+MD5 signing logic (`make_api_call`). Caches movie DB in-memory.
- **`cookie_gen.py`** — standalone cookie generator for browser injection.
- **`movie_db.json`** — local movie database (JSON, ~700 entries). Path resolved from `__file__`. **Windows**: must open with `encoding="utf-8"` or cp1252 breaks on non-ASCII chars.
- **No package.json, no setup.py, no CI, no tests.**
- API base: `https://h5-api.hehekang.com`. All requests require custom signing headers (`currentTime`, `sign`, `aesKey`).

## Key quirks
- **Dependency**: needs `pycryptodome` (PyCryptodome, not PyCrypto) and `requests`. No lockfile.
- **Signing**: `make_api_call` auto-generates a random AES key, RSA-encrypts it, serializes sorted params → base64 → AES-ECB → MD5. See `get_sign()` in `loklok_api_mobile.py:126`.
- **Login**: field name is `pwd`, not `password`. Session stored in module-level `SESSION` dict. Login returns `token`, `userId`, `deviceid`.
- **Cookie gen**: `cookie_gen.py` outputs 3 formats: console JS, EditThisCookie JSON, curl header. Token expires — regenerate needed page.
- **Menu**: 6 items — Cari Movie (local search), Category (filter by tag), Tahun (filter by year), Negara (filter by area), Login/Logout, Scan API. All browse menus use paginated list (25/page, n/p keys).
- **Movie DB**: `movie_db.json` is a local cache. `scan_ids()` → `scan_from_home()` collects IDs from `/home/h5/getHome` (H5 client) across 6 navigation categories, then fetches details via `/cms/web/movieDrama/get` (ANDROID client). Also supports manual range scan (max 1000).
- **Stream qualities**: `GROOT_HD` (1080P), `GROOT_SD` (720P), `GROOT_LD` (540P), `GROOT_FD` (360P). Fetched in parallel via `get_all_qualities()` using iOS play info endpoint.
- **Preview vs full**: Free preview is 15–300s. Full episode requires logged-in VIP subscription.
- **Ranking**: requires login. Endpoint `/cms/h5/recommendRanking/more/v3` is broken server-side (B0001).
- **Search**: `/cms/v2/h5/search/searchWithKeyWord` always returns empty — search relies on local `movie_db.json`.

## File conventions
- UI text in Indonesian (menu labels, prompts, error messages).
- String formatting uses f-strings with 2-space indentation prefix (`print(f"  ...")`).
- `pause()` calls `input()` for blocking — cannot use in automated/headless mode.
- Clipboard copies via `xclip` (Linux) → `pbcopy` (macOS) fallback — no Windows support.
