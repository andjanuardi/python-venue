import json
import random
import re
import asyncio
from typing import Optional, Any

import requests
from bs4 import BeautifulSoup

from config import (
    DATA_DIR, USER_AGENTS, REQUEST_TIMEOUT, RETRIES,
    FIFA_RANKINGS_URL, WC_2026_URL, WC_2026_QUALIFYING_URL, WC_PERFORMANCE_URL,
    WC2026_TEAMS_URL, WC2026_GROUPS_URL, WC2026_GAMES_URL, CONF_MAP,
)


async def fetch_page(url: str) -> Optional[str]:
    for attempt in range(RETRIES):
        try:
            resp = await asyncio.to_thread(
                lambda u=url: requests.get(
                    u,
                    headers={"User-Agent": random.choice(USER_AGENTS)},
                    timeout=REQUEST_TIMEOUT,
                )
            )
            resp.raise_for_status()
            return resp.text
        except Exception as e:
            if attempt == RETRIES - 1:
                print(f"  [!] Failed to fetch {url}: {e}")
                return None
            await asyncio.sleep(1 * (attempt + 1))
    return None


async def fetch_json(url: str) -> Optional[Any]:
    text = await fetch_page(url)
    if text:
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            pass
    return None


def load_cache(filename: str):
    path = DATA_DIR / filename
    if path.exists():
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    return None


def save_cache(filename: str, data):
    path = DATA_DIR / filename
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


async def scrape_qualified_teams(use_cache=True) -> list[dict]:
    live_data = await scrape_wc2026_live(use_cache=use_cache)
    if live_data and live_data.get("teams"):
        conf_map_local = {
            "USA": "CONCACAF", "Canada": "CONCACAF", "Mexico": "CONCACAF",
        }
        return [
            {"name": t.get("name_en", f"Team_{t.get('id','?')}"),
             "confederation": conf_map_local.get(t.get("name_en", ""), "UEFA")}
            for t in live_data["teams"]
        ]
    return _default_qualified_teams()


def _default_qualified_teams() -> list[dict]:
    return [
        {"name": "Mexico", "confederation": "CONCACAF"},
        {"name": "USA", "confederation": "CONCACAF"},
        {"name": "Canada", "confederation": "CONCACAF"},
        {"name": "Argentina", "confederation": "CONMEBOL"},
        {"name": "Brazil", "confederation": "CONMEBOL"},
        {"name": "Uruguay", "confederation": "CONMEBOL"},
        {"name": "Ecuador", "confederation": "CONMEBOL"},
        {"name": "Paraguay", "confederation": "CONMEBOL"},
        {"name": "Colombia", "confederation": "CONMEBOL"},
        {"name": "England", "confederation": "UEFA"},
        {"name": "France", "confederation": "UEFA"},
        {"name": "Spain", "confederation": "UEFA"},
        {"name": "Portugal", "confederation": "UEFA"},
        {"name": "Germany", "confederation": "UEFA"},
        {"name": "Netherlands", "confederation": "UEFA"},
        {"name": "Belgium", "confederation": "UEFA"},
        {"name": "Switzerland", "confederation": "UEFA"},
        {"name": "Italy", "confederation": "UEFA"},
        {"name": "Croatia", "confederation": "UEFA"},
        {"name": "Sweden", "confederation": "UEFA"},
        {"name": "Norway", "confederation": "UEFA"},
        {"name": "Austria", "confederation": "UEFA"},
        {"name": "Czech Republic", "confederation": "UEFA"},
        {"name": "Turkey", "confederation": "UEFA"},
        {"name": "Japan", "confederation": "AFC"},
        {"name": "South Korea", "confederation": "AFC"},
        {"name": "Australia", "confederation": "AFC"},
        {"name": "Saudi Arabia", "confederation": "AFC"},
        {"name": "Iran", "confederation": "AFC"},
        {"name": "Qatar", "confederation": "AFC"},
        {"name": "Iraq", "confederation": "AFC"},
        {"name": "Jordan", "confederation": "AFC"},
        {"name": "Uzbekistan", "confederation": "AFC"},
        {"name": "Egypt", "confederation": "CAF"},
        {"name": "Senegal", "confederation": "CAF"},
        {"name": "Morocco", "confederation": "CAF"},
        {"name": "Ivory Coast", "confederation": "CAF"},
        {"name": "Ghana", "confederation": "CAF"},
        {"name": "Algeria", "confederation": "CAF"},
        {"name": "South Africa", "confederation": "CAF"},
        {"name": "Tunisia", "confederation": "CAF"},
        {"name": "Cape Verde", "confederation": "CAF"},
        {"name": "Haiti", "confederation": "CONCACAF"},
        {"name": "Panama", "confederation": "CONCACAF"},
        {"name": "Democratic Republic of the Congo", "confederation": "CAF"},
        {"name": "New Zealand", "confederation": "OFC"},
        {"name": "Curaçao", "confederation": "CONCACAF"},
        {"name": "Scotland", "confederation": "UEFA"},
        {"name": "Bosnia and Herzegovina", "confederation": "UEFA"},
    ]


async def scrape_wc2026_live(use_cache=True) -> dict:
    cache_file = "wc2026_live.json"
    if use_cache:
        cached = load_cache(cache_file)
        if cached:
            print("  [✓] Using cached WC2026 live data")
            return cached

    print("  [~] Fetching live 2026 World Cup data...")
    teams = await fetch_json(WC2026_TEAMS_URL)
    groups_data = await fetch_json(WC2026_GROUPS_URL)
    games = await fetch_json(WC2026_GAMES_URL)

    if not teams or not groups_data or not games:
        print("  [!] Failed to fetch live data from API")
        return {}

    result = {
        "teams": teams.get("teams", teams) if isinstance(teams, dict) else teams,
        "groups": groups_data.get("groups", groups_data) if isinstance(groups_data, dict) else groups_data,
        "games": games.get("games", games) if isinstance(games, dict) else games or [],
    }

    save_cache(cache_file, result)
    print(f"  [✓] Fetched {len(result['teams'])} teams, "
          f"{len(result['groups'])} groups, {len(result['games'])} matches")
    return result


async def scrape_fifa_rankings(use_cache=True) -> list[dict]:
    cache_file = "fifa_rankings.json"
    if use_cache:
        cached = load_cache(cache_file)
        if cached and len(cached) > 30:
            print("  [✓] Using cached FIFA rankings")
            return cached

    print("  [~] Scraping FIFA rankings from Wikipedia...")
    html = await fetch_page(FIFA_RANKINGS_URL)
    if not html:
        print("  [!] Falling back to default FIFA rankings")
        return _default_fifa_rankings()

    soup = BeautifulSoup(html, "lxml")
    rankings = []
    seen_names = set()
    tables = soup.find_all("table")

    for table in tables:
        rows = table.find_all("tr")
        for row in rows[1:]:
            cells = row.find_all("td")
            if len(cells) < 3:
                continue
            a_tag = cells[1].find("a") if len(cells) > 1 else None
            if not a_tag:
                continue
            team_name = a_tag.get_text(strip=True)
            team_name = re.sub(r'\(.*?\)', '', team_name).strip()
            if not team_name or team_name.isdigit() or len(team_name) < 3:
                continue
            if team_name in seen_names:
                continue
            rank_text = cells[0].get_text(strip=True)
            rank_match = re.search(r'\d+', rank_text)
            if not rank_match:
                continue
            rank = int(rank_match.group())
            points_text = cells[2].get_text(strip=True)
            points_match = re.search(r'[\d,.]+', points_text)
            points = float(points_match.group().replace(",", "")) if points_match else 0
            seen_names.add(team_name)
            if rank <= 100:
                rankings.append({"name": team_name, "rank": rank, "points": points})

    defaults = _default_fifa_rankings()
    scraped_names = {r["name"] for r in rankings}
    merged = list(rankings)
    for d in defaults:
        if d["name"] not in scraped_names:
            merged.append(d)
    merged.sort(key=lambda x: x["rank"])

    save_cache(cache_file, merged)
    if rankings:
        print(f"  [✓] Scraped {len(rankings)} teams, merged with {len(merged)} total")
    else:
        print(f"  [~] Using default FIFA rankings ({len(merged)} teams)")
    return merged


def _default_fifa_rankings() -> list[dict]:
    return [
        {"name": "Argentina", "rank": 1, "points": 1860},
        {"name": "France", "rank": 2, "points": 1840},
        {"name": "Brazil", "rank": 3, "points": 1820},
        {"name": "England", "rank": 4, "points": 1800},
        {"name": "Spain", "rank": 5, "points": 1780},
        {"name": "Portugal", "rank": 6, "points": 1760},
        {"name": "Netherlands", "rank": 7, "points": 1740},
        {"name": "Germany", "rank": 8, "points": 1730},
        {"name": "Belgium", "rank": 9, "points": 1720},
        {"name": "Italy", "rank": 10, "points": 1710},
        {"name": "Croatia", "rank": 11, "points": 1700},
        {"name": "Uruguay", "rank": 12, "points": 1680},
        {"name": "Colombia", "rank": 13, "points": 1660},
        {"name": "Morocco", "rank": 14, "points": 1650},
        {"name": "Switzerland", "rank": 15, "points": 1640},
        {"name": "Denmark", "rank": 16, "points": 1630},
        {"name": "Japan", "rank": 17, "points": 1620},
        {"name": "USA", "rank": 18, "points": 1610},
        {"name": "Mexico", "rank": 19, "points": 1600},
        {"name": "Senegal", "rank": 20, "points": 1590},
        {"name": "Austria", "rank": 21, "points": 1580},
        {"name": "Serbia", "rank": 22, "points": 1570},
        {"name": "Poland", "rank": 23, "points": 1560},
        {"name": "Ukraine", "rank": 24, "points": 1550},
        {"name": "Ecuador", "rank": 25, "points": 1540},
        {"name": "Nigeria", "rank": 26, "points": 1530},
        {"name": "Egypt", "rank": 27, "points": 1520},
        {"name": "Tunisia", "rank": 28, "points": 1510},
        {"name": "South Korea", "rank": 29, "points": 1500},
        {"name": "Australia", "rank": 30, "points": 1490},
        {"name": "Iran", "rank": 31, "points": 1480},
        {"name": "Algeria", "rank": 32, "points": 1470},
        {"name": "Cameroon", "rank": 33, "points": 1460},
        {"name": "Canada", "rank": 34, "points": 1450},
        {"name": "Turkey", "rank": 35, "points": 1440},
        {"name": "Costa Rica", "rank": 36, "points": 1430},
        {"name": "Sweden", "rank": 37, "points": 1420},
        {"name": "Peru", "rank": 38, "points": 1410},
        {"name": "Chile", "rank": 39, "points": 1400},
        {"name": "Saudi Arabia", "rank": 40, "points": 1390},
        {"name": "Ghana", "rank": 41, "points": 1380},
        {"name": "Ivory Coast", "rank": 42, "points": 1370},
        {"name": "Paraguay", "rank": 43, "points": 1360},
        {"name": "Qatar", "rank": 44, "points": 1350},
        {"name": "Panama", "rank": 45, "points": 1340},
        {"name": "Jamaica", "rank": 46, "points": 1330},
        {"name": "New Zealand", "rank": 47, "points": 1320},
        {"name": "Iraq", "rank": 48, "points": 1310},
    ]


async def scrape_historical_wc_data(use_cache=True) -> list[dict]:
    cache_file = "wc_history.json"
    if use_cache:
        cached = load_cache(cache_file)
        if cached:
            print("  [✓] Using cached historical WC data")
            return cached

    print("  [~] Scraping historical World Cup data...")
    html = await fetch_page(WC_PERFORMANCE_URL)
    if not html:
        print("  [!] Falling back to default historical data")
        return _default_wc_history()

    soup = BeautifulSoup(html, "lxml")
    teams_data = []
    table = soup.find("table", class_="wikitable")
    if table:
        rows = table.find_all("tr")
        for row in rows[1:]:
            cells = row.find_all(["th", "td"])
            if len(cells) < 3:
                continue
            a = cells[0].find("a")
            if not a:
                continue
            team_name = a.get_text(strip=True)
            appearances = 0
            best_result = "Group Stage"
            for i, cell in enumerate(cells[1:], 1):
                text = cell.get_text(strip=True)
                if i == 1:
                    try:
                        appearances = int(text) if text.isdigit() else 0
                    except ValueError:
                        appearances = 0
                if i == 2:
                    best_result = text if text else "Group Stage"
            if team_name:
                teams_data.append({
                    "name": team_name,
                    "appearances": appearances,
                    "best_result": best_result,
                })

    if teams_data:
        save_cache(cache_file, teams_data)
        print(f"  [✓] Scraped historical data for {len(teams_data)} teams")
        return teams_data

    return _default_wc_history()


def _default_wc_history() -> list[dict]:
    return [
        {"name": "Brazil", "appearances": 22, "best_result": "Champion"},
        {"name": "Germany", "appearances": 20, "best_result": "Champion"},
        {"name": "Italy", "appearances": 18, "best_result": "Champion"},
        {"name": "Argentina", "appearances": 18, "best_result": "Champion"},
        {"name": "England", "appearances": 16, "best_result": "Champion"},
        {"name": "France", "appearances": 16, "best_result": "Champion"},
        {"name": "Spain", "appearances": 16, "best_result": "Champion"},
        {"name": "Uruguay", "appearances": 14, "best_result": "Champion"},
        {"name": "Netherlands", "appearances": 11, "best_result": "Runner-up"},
        {"name": "Croatia", "appearances": 6, "best_result": "Runner-up"},
        {"name": "Belgium", "appearances": 14, "best_result": "Third place"},
        {"name": "Sweden", "appearances": 12, "best_result": "Runner-up"},
        {"name": "Portugal", "appearances": 8, "best_result": "Third place"},
        {"name": "Switzerland", "appearances": 12, "best_result": "Quarter-finals"},
        {"name": "Denmark", "appearances": 6, "best_result": "Quarter-finals"},
        {"name": "Serbia", "appearances": 13, "best_result": "Fourth place"},
        {"name": "Mexico", "appearances": 17, "best_result": "Quarter-finals"},
        {"name": "Japan", "appearances": 7, "best_result": "Round of 16"},
        {"name": "South Korea", "appearances": 11, "best_result": "Fourth place"},
        {"name": "USA", "appearances": 11, "best_result": "Third place"},
        {"name": "Morocco", "appearances": 6, "best_result": "Fourth place"},
        {"name": "Senegal", "appearances": 3, "best_result": "Quarter-finals"},
        {"name": "Nigeria", "appearances": 6, "best_result": "Round of 16"},
        {"name": "Colombia", "appearances": 6, "best_result": "Quarter-finals"},
        {"name": "Paraguay", "appearances": 8, "best_result": "Quarter-finals"},
        {"name": "Ecuador", "appearances": 4, "best_result": "Round of 16"},
        {"name": "Costa Rica", "appearances": 6, "best_result": "Quarter-finals"},
        {"name": "Iran", "appearances": 6, "best_result": "Group Stage"},
        {"name": "Saudi Arabia", "appearances": 6, "best_result": "Round of 16"},
        {"name": "Australia", "appearances": 6, "best_result": "Round of 16"},
        {"name": "Canada", "appearances": 3, "best_result": "Group Stage"},
        {"name": "Algeria", "appearances": 4, "best_result": "Round of 16"},
        {"name": "Cameroon", "appearances": 8, "best_result": "Quarter-finals"},
        {"name": "Ghana", "appearances": 4, "best_result": "Quarter-finals"},
        {"name": "Ivory Coast", "appearances": 3, "best_result": "Group Stage"},
        {"name": "Egypt", "appearances": 3, "best_result": "Group Stage"},
        {"name": "Tunisia", "appearances": 6, "best_result": "Group Stage"},
        {"name": "Poland", "appearances": 9, "best_result": "Third place"},
        {"name": "Austria", "appearances": 7, "best_result": "Third place"},
        {"name": "Turkey", "appearances": 2, "best_result": "Third place"},
        {"name": "Ukraine", "appearances": 1, "best_result": "Quarter-finals"},
        {"name": "Panama", "appearances": 1, "best_result": "Group Stage"},
        {"name": "Jamaica", "appearances": 1, "best_result": "Group Stage"},
        {"name": "Qatar", "appearances": 1, "best_result": "Group Stage"},
        {"name": "Iraq", "appearances": 1, "best_result": "Group Stage"},
        {"name": "United Arab Emirates", "appearances": 1, "best_result": "Group Stage"},
        {"name": "New Zealand", "appearances": 2, "best_result": "Group Stage"},
        {"name": "Czech Republic", "appearances": 9, "best_result": "Runner-up"},
    ]
