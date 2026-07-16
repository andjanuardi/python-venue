# World Cup 2026 Predictor — Agent Guide

## Entrypoint & modes

- `main.py` — CLI entrypoint, uses `asyncio.run(main())`.
- Arguments: `--interactive` (arrow-key TUI), `--live` (real API data + remaining knockout), `--simulate` (full 48-team pre-tournament), `--no-cache`, `--simulations N`, `--no-html`.
- Default mode: `--live` (falls back to `--simulate` if API fails).

## Running

```
run.bat                          # Windows: uses venv\Scripts\python.exe
venv\Scripts\python.exe -X utf8 main.py --interactive
venv\Scripts\python.exe -X utf8 main.py --live
venv\Scripts\python.exe -X utf8 main.py --simulate --simulations 50000
```

- `run.bat` auto-installs deps via `requirements.txt`.
- Must run from a real `cmd.exe` (prompt_toolkit needs a Win32 console).

## Venv gotcha

The project `venv` was created with `C:\Users\Andri Januardi\AppData\Local\Programs\Python\Python312\python.exe`. Do **not** recreate venv with the Inkscape-bundled Python (`C:\Program Files\Inkscape\bin\python.exe`) — its SSL cert store is broken (cmake build downloads fail). Always use the AppData Python for venv creation.

## Async gotcha

All `questionary` prompts inside async functions **must** use `.ask_async()` + `await`, never `.ask()` (which calls `asyncio.run()` and will crash with `RuntimeError: asyncio.run() cannot be called from a running event loop`). This applies to `questionary.select`, `questionary.text`, `questionary.press_any_key_to_continue`, etc.

## Project layout

| File | Role |
|---|---|
| `main.py` | CLI entrypoint, arg parsing, orchestration |
| `config.py` | Constants: ELO params, URLs, simulation counts |
| `models.py` | Pydantic models: `Team`, `GroupInfo`, `SimulationResult`, `TeamStats` |
| `prediction.py` | ELO engine, group draw, knockout simulation, live bracket builder |
| `scrapers.py` | HTTP scraping (Wikipedia + wc2026.moothz.win API), JSON cache |
| `output.py` | Rich CLI tables, matplotlib charts (Agg backend), Jinja2 HTML report |
| `interactive.py` | questionary-based TUI menu, Settings, progress bars |
| `templates/report.html` | Jinja2 HTML report template |
| `data/` | Scraped JSON cache: `fifa_rankings.json`, `wc_history.json`, `wc2026_live.json`, `qualified_teams.json` |
| `output_data/` | Generated HTML report: `worldcup_2026_prediction.html` |

## Key config defaults

- Full simulation: 10,000 runs
- Live simulation: 50,000 runs
- 48 teams, 12 groups of 4, top 2 + 8 best 3rd advance to R32
- ELO: initial 1500, K=60 group / 80 knockout / 40 qualifying / 20 friendly
- API: `https://wc2026.moothz.win/get/{teams,groups,games}`

## Testing / verification

No test suite, no typechecker, no linter configured. Run the simulation to verify:
```
venv\Scripts\python.exe -X utf8 main.py --simulate --simulations 1000
```

## Output

- Rich-formatted top-20 table + champion/dark horse to stdout.
- `output_data/worldcup_2026_prediction.html` — standalone HTML report with charts (bar, pie, stage advancement), group tables, bracket.
