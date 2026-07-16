import os
from pathlib import Path

BASE_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR / "data"
OUTPUT_DIR = BASE_DIR / "output_data"

os.makedirs(DATA_DIR, exist_ok=True)
os.makedirs(OUTPUT_DIR, exist_ok=True)

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/119.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 Safari/605.1.15",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36",
]

REQUEST_TIMEOUT = 30
RETRIES = 3

INITIAL_ELO = 1500
ELO_K_WORLD_CUP = 60
ELO_K_KNOCKOUT = 80
ELO_K_QUALIFYING = 40
ELO_K_FRIENDLY = 20

SIMULATION_COUNT = 10000
LIVE_SIMULATION_COUNT = 50000

GROUP_SIZE = 4
NUM_GROUPS = 12
TEAMS_TOTAL = 48
KNOCKOUT_TEAMS = 32
BEST_THIRD_PLACE = 8

WC_HISTORY_YEARS = list(range(1930, 2023, 4))
WC_HISTORY_YEARS.remove(1942)
WC_HISTORY_YEARS.remove(1946)

FIFA_RANKINGS_URL = "https://en.wikipedia.org/wiki/FIFA_World_Rankings"
WC_2026_URL = "https://en.wikipedia.org/wiki/2026_FIFA_World_Cup"
WC_2026_QUALIFYING_URL = "https://en.wikipedia.org/wiki/2026_FIFA_World_Cup_qualification"
WC_PERFORMANCE_URL = "https://en.wikipedia.org/wiki/National_team_appearances_in_the_FIFA_World_Cup"

WC2026_API_BASE = "https://wc2026.moothz.win"
WC2026_TEAMS_URL = f"{WC2026_API_BASE}/get/teams"
WC2026_GROUPS_URL = f"{WC2026_API_BASE}/get/groups"
WC2026_GAMES_URL = f"{WC2026_API_BASE}/get/games"

ROUND_NAMES = {
    "group": "Group Stage",
    "round_32": "Round of 32",
    "round_16": "Round of 16",
    "quarter_final": "Quarter-finals",
    "semi_final": "Semi-finals",
    "third_place": "Third Place",
    "final": "Final",
}

CONF_MAP = {
    "Mexico": "CONCACAF", "South Africa": "CAF", "South Korea": "AFC", "Czech Republic": "UEFA",
    "Canada": "CONCACAF", "Bosnia and Herzegovina": "UEFA", "Qatar": "AFC", "Switzerland": "UEFA",
    "Brazil": "CONMEBOL", "Morocco": "CAF", "Haiti": "CONCACAF", "Scotland": "UEFA",
    "United States": "CONCACAF", "Paraguay": "CONMEBOL", "Australia": "AFC", "Turkey": "UEFA",
    "Germany": "UEFA", "Curaçao": "CONCACAF", "Ivory Coast": "CAF", "Ecuador": "CONMEBOL",
    "Netherlands": "UEFA", "Japan": "AFC", "Sweden": "UEFA", "Tunisia": "CAF",
    "Belgium": "UEFA", "Egypt": "CAF", "Iran": "AFC", "New Zealand": "OFC",
    "Spain": "UEFA", "Cape Verde": "CAF", "Saudi Arabia": "AFC", "Uruguay": "CONMEBOL",
    "France": "UEFA", "Senegal": "CAF", "Iraq": "AFC", "Norway": "UEFA",
    "Argentina": "CONMEBOL", "Algeria": "CAF", "Austria": "UEFA", "Jordan": "AFC",
    "Portugal": "UEFA", "DR Congo": "CAF", "Uzbekistan": "AFC", "Colombia": "CONMEBOL",
    "England": "UEFA", "Croatia": "UEFA", "Ghana": "CAF", "Panama": "CONCACAF",
}
