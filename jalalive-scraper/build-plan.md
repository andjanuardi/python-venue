# Build Plan: JalaLive Scraper (jalas30.com)

## Deskripsi

Aplikasi scraping untuk **JalaLive** — platform streaming sepak bola live asal Indonesia.
Domain utama `jalas30.com` dan mirror-mirornya (`jalalive.cc`, `jalalive3.id`, `jalaace2.com`, dll).
Data target: jadwal pertandingan, link streaming, livescore, berita bola, daftar domain mirror.

---

## Phase 1 — Foundation (Estimasi: 2-3 jam)

**Tujuan:** Scraper dasar dapat berjalan dari 1 mirror domain, output JSON.

### Tasks

1. **Setup project**
   - Struktur direktori
   - `requirements.txt`: httpx, beautifulsoup4, lxml, fake-useragent, pydantic
   - `config/settings.py`: user-agent list, delay, timeout, domain pool

2. **Base scraper** (`scrapers/base_scraper.py`)
   - Async HTTP client dengan retry (3x) & exponential backoff
   - Rotasi User-Agent
   - Random delay 1-3 detik antar request

3. **Schedule scraper** (`scrapers/schedule_scraper.py`)
   - Ambil HTML dari mirror domain (contoh: jalalive.cc)
   - Parse jadwal pertandingan (tanggal, jam, tim tuan rumah, tim tandang, liga, link detail)
   - Output: `data/schedules.json`

4. **Stream link scraper** (`scrapers/stream_scraper.py`)
   - Follow link detail tiap pertandingan
   - Ekstrak link streaming (iframe src / redirect URL)
   - Output: `data/streams.json`

5. **Data models** (`models/match.py`, `models/stream.py`)
   - Pydantic models: Match, StreamLink, League

6. **CLI entry** (`main.py`)
   - Argparse untuk memilih mode scraping
   - Running: `python main.py --scrape all --export json`

### Deliverables Phase 1

- File berjalan: `main.py`, `base_scraper.py`, `schedule_scraper.py`, `stream_scraper.py`
- Output JSON: `data/schedules.json`, `data/streams.json`
- Logging ke file: `logs/scraper.log`

---

## Phase 2 — Multi-Domain & Anti-Block (Estimasi: 2-3 jam)

**Tujuan:** Stabil, tidak mudah diblokir, multi-mirror.

### Tasks

1. **Domain pool & health checker**
   - `config/domains.yaml`: daftar domain + status (active/dead)
   - `monitors/domain_monitor.py`: cek HTTP 200 tiap domain, update status
   - Auto-fallback jika domain utama mati

2. **Mirror finder** (`scrapers/mirror_finder.py`)
   - Cari domain mirror baru via web search
   - Keywords: "jalalive link alternatif", "jalas30 domain baru"
   - Validasi otomatis sebelum ditambahkan ke pool

3. **Database storage** (`storage/database.py`)
   - SQLite (dev) / PostgreSQL (production)
   - Tabel: `matches`, `stream_links`, `domains`, `logs`
   - Dedup berdasarkan match_id / hash

4. **Exporter** (`storage/exporters/`)
   - `json_exporter.py`
   - `csv_exporter.py`

### Deliverables Phase 2

- Scraper otomatis pilih domain aktif dari pool
- Data tersimpan di SQLite
- Domain baru terdeteksi otomatis

---

## Phase 3 — Realtime & News (Estimasi: 3-4 jam)

**Tujuan:** Livescore update, berita, scheduler periodik.

### Tasks

1. **Livescore scraper** (`scrapers/livescore_scraper.py`)
   - Scrape halaman detail tiap X menit
   - Ambil skor, menit, statistik pertandingan
   - Update hanya jika ada perubahan

2. **News scraper** (`scrapers/news_scraper.py`)
   - Scrape section berita/artikel dari mirror site
   - Title, date, excerpt, link, thumbnail

3. **Scheduler** (`scheduler/task_scheduler.py`)
   - APScheduler
   - Schedule: jadwal tiap 15 menit, livescore tiap 2 menit (saat live)
   - Health check domain tiap 1 jam
   - Mirror finder tiap 6 jam

4. **Anti-detection upgrades**
   - Rotasi proxy (free proxy list)
   - Browser-like headers
   - Playwright fallback untuk JS-rendered pages

### Deliverables Phase 3

- Livescore update real-time
- Berita terkumpul otomatis
- Scraper berjalan 24/7 via scheduler

---

## Phase 4 — API & Monitoring (Opsional, Estimasi: 2-3 jam)

**Tujuan:** REST API untuk akses data, monitoring dashboard.

### Tasks

1. **FastAPI app** (`api/app.py`)
   - `GET /matches` — filter date, league
   - `GET /matches/{id}` — detail + stream link
   - `GET /livescores` — skor live
   - `GET /news` — berita
   - `GET /domains` — status domain pool
   - `GET /health` — status scraper

2. **Monitoring** (opsional)
   - Prometheus metrics
   - Grafana dashboard

### Deliverables Phase 4

- REST API dokumentasi otomatis (Swagger)
- Siap deploy

---

## Estimasi Total: 9-13 jam

| Phase | Jam | Dependensi |
|-------|-----|------------|
| 1 | 2-3 | - |
| 2 | 2-3 | Phase 1 |
| 3 | 3-4 | Phase 2 |
| 4 | 2-3 | Phase 3 |

---

## Catatan Teknis

- **Selector per domain** di `config/selectors.yaml`
- **Error handling**: setiap error ter-log tanpa stop scraper
- **Rate limiting**: max 1 request / 2 detik per domain
- **Data freshness**: timestamp `scraped_at` di setiap record
- **Idempotency**: skip record jika hash sama dengan record terakhir
- **Legal**: scraping hanya untuk riset/penggunaan pribadi, tidak mendistribusikan ulang konten berhak cipta
