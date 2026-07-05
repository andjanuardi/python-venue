# BitTV Live - Agent Guide

## Overview
Pure Python (stdlib only) IPTV player that fetches, decrypts, and plays BitTV streams via mpv.

## Entry points
- `bittv_player.py` — main CLI player (`python bittv_player.py`)
- `decrypt.py` — decrypt a single country JSON (`python decrypt.py ID`)
- `decrypt_all.py` — batch decrypt all country JSONs to `data/` (hardcodes fixed country list)

## Key architecture
- No package manager / virtualenv needed — stdlib only + `mpv` on PATH, `ffmpeg` on PATH (for Server Stream)
- Cache dir: `data/` — stores per-country `{CODE}.json` (raw), `{CODE}_decrypted.json`
- **Single source of truth for decryption**: `decrypt.py` — `bittv_player.py` calls it via `subprocess.run([sys.executable, "decrypt.py", code])` when raw file is >3600s stale or missing
- Data sources: Country JSONs (`ID.json`, etc.) — base62-encoded ciphertext from GitHub raw
- Country list comes from the `country_list` field inside each decrypted country JSON
- Custom decryption (`k0`): `reverse → lenient b64decode → reverse → filter non-b64 → manual b64decode → reverse`
- Per-country files have a P2 prefix (variable offset); `find_prefix()` in `decrypt.py` scans 0–199 to locate JSON start

## Startup flow
1. Load `config.json` (player path, ffmpeg path, default country)
2. Auto-detect `mpv` and `ffmpeg` on PATH if not in config, then save to config
3. Decrypt default country → get channel list + country list from decrypted JSON
4. If no default country in config → defaults to `ID`

## Stream playback
- `hls` — direct mpv
- `dash` — direct mpv
- `dash-clearkey` — direct mpv with `--demuxer-lavf-o=cenc_decryption_key=KEY`
- **Server Stream**: uses `ffmpeg` to re-stream via local HTTP server; needs `ffmpeg` on PATH or local `ffmpeg/ffmpeg.exe`
- `stream/` directory is a runtime artifact from Server Stream — not source code

## Settings menu
- **[1] Player path** — set custom path (warns if file not found)
- **[2] Default country** — change → auto-load new country immediately (no restart)
- **[3] Clear cache** — shows cache size, asks confirmation before deleting
- **[4] Info** — player path, ffmpeg path, cache size/file count, country count, available codes

## Commands
- `python bittv_player.py` — launch the TUI player
- `python decrypt.py ID` — decrypt a single country JSON
- `python decrypt_all.py` — decrypt all country JSONs
- Ensure `mpv` is on PATH or set in Settings (or place `mpv/mpv.exe` next to script)

## Known quirks
- Country source aliases: `AN→ID`, `EV→ID`
- Some country URLs return 404 (`RU`, `TR`, `UA`)
- Premium channel list behind Cloudflare (inaccessible to scripts)
- `config.json` is gitignored (contains machine-local Windows paths)
- **No tests** exist in this repo
