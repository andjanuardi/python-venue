# AGENTS.md — Loklok Stream CLI

## Quick start
```bash
pip install -r requirements.txt
python cli.py                          # interactive menu
python cli.py --id 25016               # movie detail
python cli.py --id 25016 --episode 1   # stream URL for episode
python cli.py --login --email x --pwd y
python cookie_gen.py --email x --pwd y --format console
python cookie_gen.py --email x --pwd y --format all --no-header  # all formats, cookie-only
```

## Architecture
- **`cli.py`** — interactive TUI + argparse entrypoint. Entry: `main_cli()`.
- **`loklok_api_mobile.py`** — primary API client. Default `clientType=ANDROID`, `versionCode=42`. Scan-from-home uses `clientType=H5`, `versionCode=32`.
- **`cookie_gen.py`** — standalone cookie generator. Entry: `main_cli()`. Supports `--no-header` for scriptable output.
- **`movie_db.json`** — local movie database (JSON, ~1900 entries, ~1MB). Path resolved from `__file__`. **Windows**: must open with `encoding="utf-8"` or cp1252 breaks on non-ASCII chars. `save_movie_db()` overwrites the entire file.
- **`requirements.txt`** — only deps: `pycryptodome` and `requests`.
- **No** tests, no CI, no lockfile, no formatter config.
- API base: `https://h5-api.hehekang.com`. All requests require custom signing headers (`currentTime`, `sign`, `aesKey`).

## Key quirks
- **Dependency**: needs `pycryptodome` (PyCryptodome, not PyCrypto).
- **Signing**: `make_api_call` generates random 16-char key, RSA-encrypts it (PKCS1_v1_5 padding), sorts params → base64 → AES-ECB → MD5. See `get_sign()` in `loklok_api_mobile.py`. GET uses `params` for signing, POST uses `data` body.
- **Login**: field name is `pwd`, not `password`. Session stored in module-level `SESSION` dict.
- **Scanning**: `scan_from_home()` fetches IDs across 6 navigation categories (1, 2, 3, 119, 120, 165) with H5 client type, then fetches details via ANDROID client. Uses `ThreadPoolExecutor(max_workers=15)`.
- **Stream qualities**: `GROOT_HD` (1080P), `GROOT_SD` (720P), `GROOT_LD` (540P), `GROOT_FD` (360P). Fetched in parallel via `get_all_qualities()` using iOS play info endpoint with 4 parallel workers.
- **Subtitles**: Extracted from `episodeVo[index].subtitlingList` in movie detail response (`/cms/web/movieDrama/get`). Prioritized: **Bahasa Indonesia** (`in_ID`) first, **English** (`en`) second. Fallback to `subtitlingList` from playInfo if detail is empty. Subtitle CDN: `subtitles.netpop.app`.
- **Preview vs full**: Free preview is 15–300s. Full episode requires logged-in VIP subscription.
- **Ranking**: endpoint `/cms/h5/recommendRanking/more/v3` broken server-side (B0001).
- **Search**: `/cms/v2/h5/search/searchWithKeyWord` always returns empty — search relies on local `movie_db.json`.
- **Cookie gen**: outputs 3 formats (console JS, EditThisCookie JSON, curl header). `--no-header` prints raw cookie text only.

## File conventions
- UI text mixed Indonesian/English (menu labels, prompts, error messages).
- String formatting uses f-strings with 2-space indentation prefix (`print(f"  ...")`).
- `pause()` calls `input()` for blocking — cannot use in automated/headless mode.
- Clipboard copies via `xclip` (Linux) → `pbcopy` (macOS) fallback — no Windows support.
- `.venv/` recommended for virtual environment.

## Reference files
- `API_ENDPOINTS.md` — full endpoint inventory from reverse-engineered Nuxt JS bundles.
