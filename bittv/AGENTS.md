# BitTV Live - Agent Guide

## Overview
Pure Python (stdlib only) IPTV player that fetches, decrypts, and plays BitTV streams via mpv.

## Entry points
- `bittv_player.py` — main CLI player (`python bittv_player.py`)
- `decrypt.py` — decrypt a single country JSON (`python decrypt.py ID`)
- `decrypt_all.py` — batch decrypt all country JSONs to `data/`
- `test_*.py` in `temp/` — ad-hoc experiments; run standalone with `python temp/test_foo.py`

## Key architecture
- No package manager / virtualenv needed — stdlib only + mpv on PATH
- Windows-only: mpv for playback
- Cache dir: `data/` — stores `SP.json`, per-country `{CODE}.json` (raw), `{CODE}_decrypted.json`
- **Single source of truth for decryption**: `decrypt.py` — `bittv_player.py` calls it via `subprocess.run([sys.executable, "decrypt.py", code])` when cache is stale
- Data sources:
  - SP.json (country list only): plain JSON from `cdn.jsdelivr.net`, used for country navigation
  - Country JSONs (`ID.json`, etc.): base62-encoded ciphertext from GitHub raw
- Custom decryption (`k0`): `reverse → lenient b64decode → reverse → filter non-b64 → manual b64decode → reverse`
- Per-country files have a P2 prefix (variable offset); `find_prefix()` in `decrypt.py` scans 0–199 to locate JSON start

## Startup flow
1. Load `config.json` (player path, default country)
2. Fetch SP.json for country list (13 countries)
3. If config has a default country → auto-decrypt via `decrypt.py`
4. If no default country → force user to pick one first

## Stream types
- `hls` — direct mpv
- `dash` — direct mpv
- `dash-clearkey` — direct mpv with `--demuxer-lavf-o=cenc_decryption_key=KEY`

## Important files
- `bittv-api-docs.txt` — reverse engineering docs (Firebase RC keys, endpoints, data structure, decryption notes)
- `decrypt.py` — standalone decryption tool, also used internally by `bittv_player.py`

## Settings menu
- **[1] Player path** — set custom path (warns if file not found)
- **[2] Default country** — change → auto-load new country immediately (no restart)
- **[3] Clear cache** — shows cache size, asks confirmation before deleting
- **[4] Info** — player path, cache size/file count, SP country count, available codes

## Commands
- `python bittv_player.py` — launch the TUI player
- `python decrypt.py ID` — decrypt a single country JSON
- `python decrypt_all.py` — decrypt all country JSONs
- `python temp/test_*.py` — run individual experiments
- Ensure `mpv` is on PATH or set in player Settings (or place `mpv/mpv.exe` next to script)

## Known quirks
- Country source aliases: `AN→ID`, `EV→ID`
- Some country URLs return 404 (`RU`, `TR`, `UA`)
- Premium channel list is behind Cloudflare (inaccessible to scripts)
