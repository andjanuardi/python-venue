import math
import random
from collections import defaultdict
from datetime import datetime

from config import (
    INITIAL_ELO, ELO_K_WORLD_CUP, ELO_K_KNOCKOUT, NUM_GROUPS,
    GROUP_SIZE, TEAMS_TOTAL, KNOCKOUT_TEAMS, BEST_THIRD_PLACE,
    SIMULATION_COUNT, LIVE_SIMULATION_COUNT, ROUND_NAMES,
    CONF_MAP,
)
from models import Team, GroupInfo, MatchInGroup, SimulationResult, TeamStats


def _normalize_name(name: str) -> str:
    return name.strip().lower()


def expected_score(rating_a: float, rating_b: float) -> float:
    return 1.0 / (1.0 + math.pow(10, (rating_b - rating_a) / 400.0))


def match_probabilities(rating_a: float, rating_b: float) -> tuple[float, float, float]:
    diff = abs(rating_a - rating_b)
    if diff < 50:
        draw_p = 0.28
    elif diff < 150:
        draw_p = 0.22
    else:
        draw_p = 0.15
    exp_a = expected_score(rating_a, rating_b)
    win_a = (1 - draw_p) * exp_a
    win_b = (1 - draw_p) * (1 - exp_a)
    return win_a, draw_p, win_b


def simulate_knockout_match(rating_a: float, rating_b: float) -> str:
    exp_a = expected_score(rating_a, rating_b)
    return "A" if random.random() < exp_a else "B"


def predict_score(rating_a: float, rating_b: float) -> tuple[int, int, float]:
    exp_a = expected_score(rating_a, rating_b)
    total_goals = 2.5
    raw_a = total_goals * exp_a
    raw_b = total_goals * (1 - exp_a)
    goals_a = max(0, round(raw_a))
    goals_b = max(0, round(raw_b))
    if goals_a == goals_b:
        if raw_a > raw_b:
            goals_a += 1
        elif raw_b > raw_a:
            goals_b += 1
    confidence = round(max(exp_a, 1 - exp_a) * 100, 1)
    return goals_a, goals_b, confidence


def elo_update(rating_a: float, rating_b: float, result: float, k: float = ELO_K_WORLD_CUP) -> tuple[float, float]:
    exp_a = expected_score(rating_a, rating_b)
    new_a = rating_a + k * (result - exp_a)
    new_b = rating_b + k * ((1 - result) - (1 - exp_a))
    return new_a, new_b


TEAM_ID_MAP = {}
_API_TEAMS_LIST = []


def parse_live_data(api_data: dict, rankings: list[dict], history: list[dict]) -> dict:
    global TEAM_ID_MAP, _API_TEAMS_LIST

    teams_api = api_data.get("teams", [])
    groups_api = api_data.get("groups", [])
    games_api = api_data.get("games", [])

    rank_map = {}
    for r in rankings:
        name_clean = _normalize_name(r["name"])
        rank_map[name_clean] = r

    hist_map = {}
    for h in history:
        name_clean = _normalize_name(h["name"])
        hist_map[name_clean] = h

    team_by_id = {}
    team_by_name = {}
    TEAM_ID_MAP = {}
    _API_TEAMS_LIST = teams_api

    for t in teams_api:
        api_name = t["name_en"]
        key = _normalize_name(api_name)
        rd = rank_map.get(key, {})
        hd = hist_map.get(key, {})

        fifa_rank = rd.get("rank", 999) if rd else 999
        fifa_pts = rd.get("points", 0) if rd else 0

        hist_bonus = 0
        if hd:
            best = hd.get("best_result", "")
            apps = hd.get("appearances", 0)
            if "Champion" in best:
                hist_bonus = 200 + apps * 5
            elif "Runner-up" in best:
                hist_bonus = 150 + apps * 5
            elif "Third" in best or "Fourth" in best:
                hist_bonus = 100 + apps * 5
            elif "Quarter" in best:
                hist_bonus = 60 + apps * 5
            elif "Round of 16" in best or "Second" in best:
                hist_bonus = 30 + apps * 3
            else:
                hist_bonus = 10 + apps * 2

        elo_base = 2000 - fifa_rank * 10 if fifa_rank < 100 else 1000
        elo_base = max(1000, min(2200, elo_base))
        elo_rating = elo_base + hist_bonus * 0.5

        conf = CONF_MAP.get(api_name, "UEFA")
        team = Team(
            name=api_name,
            confederation=conf,
            fifa_rank=fifa_rank,
            fifa_points=fifa_pts,
            elo_rating=round(elo_rating, 1),
            historical_weight=round(hist_bonus, 1),
        )
        team.strength = round(elo_rating + _squad_value(api_name, fifa_rank) * 0.3, 1)

        team_id = t.get("id", api_name)
        team_by_id[team_id] = team
        team_by_name[api_name] = team
        TEAM_ID_MAP[str(team_id)] = api_name

    group_map = {}
    for g in groups_api:
        letter = g["name"]
        group_map[letter] = []
        for entry in g["teams"]:
            tid = str(entry["team_id"])
            team_name = TEAM_ID_MAP.get(tid, f"Team_{tid}")
            group_map[letter].append({
                "team": team_name,
                "pts": int(entry["pts"]),
                "w": int(entry["w"]),
                "d": int(entry["d"]),
                "l": int(entry["l"]),
                "gf": int(entry["gf"]),
                "ga": int(entry["ga"]),
                "gd": int(entry["gd"]),
                "gs": int(entry["gf"]),
            })

    _update_elo_from_results(team_by_name, games_api)
    return team_by_name, team_by_id, group_map, games_api


def _squad_value(name: str, fifa_rank: int) -> float:
    base_values = {
        "England": 1500, "France": 1400, "Brazil": 1300, "Portugal": 1200,
        "Spain": 1150, "Germany": 1100, "Netherlands": 1000, "Italy": 950,
        "Argentina": 1200, "Belgium": 900, "Uruguay": 700, "Croatia": 650,
        "USA": 600,
    }
    if name in base_values:
        return base_values[name]
    rank_factor = max(0, 100 - fifa_rank) / 100
    return round(200 + rank_factor * 600, 1)


def _update_elo_from_results(team_by_name: dict, games: list):
    for game in games:
        rnd = game.get("type", "")
        if rnd != "group":
            continue
        ta_id = str(game.get("home_team_id", ""))
        tb_id = str(game.get("away_team_id", ""))
        hs = game.get("home_score")
        als = game.get("away_score")
        finished = game.get("finished") == "TRUE"

        if not finished or hs is None or als is None:
            continue
        if hs in ("null", "NULL", "") or als in ("null", "NULL", ""):
            continue

        sa = int(hs)
        sb = int(als)
        ta = TEAM_ID_MAP.get(ta_id, "")
        tb = TEAM_ID_MAP.get(tb_id, "")

        if not ta or not tb:
            continue
        if ta not in team_by_name or tb not in team_by_name:
            continue

        team_a = team_by_name[ta]
        team_b = team_by_name[tb]

        if sa > sb:
            result = 1.0
        elif sb > sa:
            result = 0.0
        else:
            result = 0.5

        ra = team_a.strength
        rb = team_b.strength
        new_a, new_b = elo_update(ra, rb, result, ELO_K_WORLD_CUP)
        team_a.strength = round(new_a, 1)
        team_b.strength = round(new_b, 1)


import re as _re

ROUND_TYPE_MAP = {
    "r32": "round_32", "r16": "round_16", "qf": "quarter_final",
    "sf": "semi_final", "third": "third_place", "final": "final",
}

ROUND_ORDER = ["r32", "r16", "qf", "sf", "third", "final"]


def _parse_parent_ids(label: str) -> list[int]:
    ids = []
    for m in _re.finditer(r"(?:Winner|Loser) Match (\d+)", label):
        ids.append(int(m.group(1)))
    return ids


def build_bracket_from_games(games: list) -> dict:
    bracket = {}

    for rnd in ROUND_ORDER:
        rnd_key = ROUND_TYPE_MAP[rnd]
        matches = [g for g in games if g.get("type") == rnd]
        matches.sort(key=lambda x: int(x.get("id", 0)))
        bracket[rnd_key] = []

        for m in matches:
            match_id = int(m.get("id", 0))
            ta = m.get("home_team_name_en") or ""
            tb = m.get("away_team_name_en") or ""

            finished = m.get("finished") == "TRUE"
            hs = m.get("home_score")
            als = m.get("away_score")

            sa = None
            sb = None
            if finished and hs is not None and str(hs).strip() not in ("null", "NULL", "") \
               and als is not None and str(als).strip() not in ("null", "NULL", ""):
                sa = int(hs)
                sb = int(als)

            parents = _parse_parent_ids(m.get("home_team_label", "")) \
                      + _parse_parent_ids(m.get("away_team_label", ""))

            bracket[rnd_key].append({
                "match_id": match_id,
                "team_a": ta,
                "team_b": tb,
                "score_a": sa,
                "score_b": sb,
                "winner": "",
                "parents": parents,
            })

    for rnd_idx, rnd_key in enumerate([ROUND_TYPE_MAP[r] for r in ROUND_ORDER]):
        next_keys = [ROUND_TYPE_MAP[r] for r in ROUND_ORDER[rnd_idx + 1:]]
        for match in bracket[rnd_key]:
            if match["winner"] or match["score_a"] is None:
                continue
            if match["score_a"] == match["score_b"]:
                for nrk in next_keys:
                    for nm in bracket.get(nrk, []):
                        for tm in [match["team_a"], match["team_b"]]:
                            if nm["team_a"] == tm or nm["team_b"] == tm:
                                match["winner"] = tm
                                break
                        if match["winner"]:
                            break
                    if match["winner"]:
                        break
            else:
                match["winner"] = match["team_a"] if match["score_a"] > match["score_b"] else match["team_b"]

    return bracket


def run_live_prediction(
    team_by_name: dict,
    bracket: dict,
    num_simulations: int = LIVE_SIMULATION_COUNT,
    progress_callback=None,
) -> tuple[list[SimulationResult], dict[str, TeamStats]]:

    wins = defaultdict(int)
    team_stats = {name: TeamStats(team=name) for name in team_by_name}

    rounds_order = ["round_32", "round_16", "quarter_final", "semi_final", "third_place", "final"]
    rounds_data = {r: bracket.get(r, []) for r in rounds_order}

    for sim in range(num_simulations):
        live_winner = _simulate_one_bracket(rounds_data, team_by_name)

        if live_winner:
            wins[live_winner] += 1
            if live_winner in team_stats:
                team_stats[live_winner].win_pct += 1

        if progress_callback:
            progress_callback(sim + 1)

    results = []
    for name, count in wins.items():
        results.append(SimulationResult(
            team=name,
            wins=count,
            probability=round(count / num_simulations * 100, 2),
            best_rank=1,
        ))

    for name, stats in team_stats.items():
        stats.win_pct = round(stats.win_pct / num_simulations * 100, 1)

    results.sort(key=lambda r: r.probability, reverse=True)
    return results, team_stats


def _simulate_one_bracket(rounds_data: dict, team_by_name: dict) -> str | None:
    winners_by_id = {}

    for rnd_key in ["round_32", "round_16", "quarter_final", "semi_final", "third_place", "final"]:
        for match in rounds_data.get(rnd_key, []):
            mid = match["match_id"]

            if match["winner"]:
                winners_by_id[mid] = match["winner"]
                continue

            ta = match["team_a"]
            tb = match["team_b"]
            parents = match.get("parents", [])

            if not ta and parents:
                ta = winners_by_id.get(parents[0], "")
            if not tb and len(parents) > 1:
                tb = winners_by_id.get(parents[1], "")
            elif not tb and parents:
                tb = winners_by_id.get(parents[0], "")

            if ta and tb:
                ra = team_by_name[ta].strength if ta in team_by_name else INITIAL_ELO
                rb = team_by_name[tb].strength if tb in team_by_name else INITIAL_ELO
                w = ta if simulate_knockout_match(ra, rb) == "A" else tb
                winners_by_id[mid] = w
            elif ta and not tb:
                winners_by_id[mid] = ta
            elif tb and not ta:
                winners_by_id[mid] = tb
            else:
                winners_by_id[mid] = ""

    for m in rounds_data.get("final", []):
        if m["match_id"] in winners_by_id and winners_by_id[m["match_id"]]:
            return winners_by_id[m["match_id"]]
    return None


def build_teams(rankings: list[dict], qualified: list[dict], history: list[dict]) -> dict[str, Team]:
    rank_map = {_normalize_name(r["name"]): r for r in rankings}
    hist_map = {_normalize_name(h["name"]): h for h in history}
    teams = {}

    qualified_with_rank = []
    for q in qualified:
        key = _normalize_name(q["name"])
        rd = rank_map.get(key)
        qualified_with_rank.append((q, rd["rank"] if rd else 999))
    qualified_with_rank.sort(key=lambda x: x[1])
    qualified = [q for q, _ in qualified_with_rank[:TEAMS_TOTAL]]

    for q in qualified:
        name = q["name"]
        conf = q["confederation"]
        key = _normalize_name(name)
        rank_data = rank_map.get(key, None)
        hist_data = hist_map.get(key, None)

        fifa_rank = rank_data["rank"] if rank_data else 999
        fifa_pts = rank_data["points"] if rank_data else 0.0

        hist_bonus = 0
        if hist_data:
            best = hist_data.get("best_result", "")
            apps = hist_data.get("appearances", 0)
            if "Champion" in best:
                hist_bonus = 200 + apps * 5
            elif "Runner-up" in best:
                hist_bonus = 150 + apps * 5
            elif "Third" in best or "Fourth" in best:
                hist_bonus = 100 + apps * 5
            elif "Quarter" in best:
                hist_bonus = 60 + apps * 5
            elif "Round of 16" in best or "Second" in best:
                hist_bonus = 30 + apps * 3
            else:
                hist_bonus = 10 + apps * 2

        elo_base = 2000 - fifa_rank * 10 if fifa_rank < 100 else 1000
        elo_base = max(1000, min(2200, elo_base))
        elo_rating = elo_base + hist_bonus * 0.5
        team = Team(
            name=name,
            confederation=conf,
            fifa_rank=fifa_rank,
            fifa_points=fifa_pts,
            elo_rating=round(elo_rating, 1),
            historical_weight=round(hist_bonus, 1),
        )
        teams[name] = team

    _add_squad_value_bonus(teams)
    for t in teams.values():
        t.strength = round(t.elo_rating + t.squad_value * 0.3, 1)
    return teams


def _add_squad_value_bonus(teams: dict[str, Team]):
    base_values = {
        "England": 1500, "France": 1400, "Brazil": 1300, "Portugal": 1200,
        "Spain": 1150, "Germany": 1100, "Netherlands": 1000, "Italy": 950,
        "Argentina": 1200, "Belgium": 900, "Uruguay": 700, "Croatia": 650,
        "USA": 600,
    }
    for name, team in teams.items():
        if name in base_values:
            team.squad_value = base_values[name]
        else:
            rank_factor = max(0, 100 - team.fifa_rank) / 100
            team.squad_value = round(200 + rank_factor * 600, 1)


def simulate_group_draw(teams: dict[str, Team]) -> list[GroupInfo]:
    sorted_teams = sorted(teams.values(), key=lambda t: t.fifa_rank)
    pots = [[], [], [], []]
    for i, t in enumerate(sorted_teams):
        pots[i // 12].append(t)

    hosts = [t for t in pots[0] if t.name in ("USA", "Canada", "Mexico")]
    for h in hosts:
        pots[0].remove(h)
    for h in reversed(hosts):
        pots[0].insert(0, h)

    groups = {chr(65 + i): [] for i in range(12)}

    for pot_idx, pot in enumerate(pots):
        random.shuffle(pot)
        unplaced = list(pot)
        for team in list(unplaced):
            for g_idx in range(12):
                letter = chr(65 + g_idx)
                uefa_count = sum(1 for t in groups[letter] if t.confederation == "UEFA")
                same_conf = team.confederation in [t.confederation for t in groups[letter]]
                if team.confederation == "UEFA" and uefa_count >= 2:
                    same_conf = True
                if not same_conf and len(groups[letter]) == pot_idx:
                    groups[letter].append(team)
                    unplaced.remove(team)
                    break
        for team in unplaced:
            for g_idx in range(12):
                letter = chr(65 + g_idx)
                if len(groups[letter]) == pot_idx:
                    groups[letter].append(team)
                    break

    return [GroupInfo(letter=l, teams=[t.name for t in teams_list])
            for l, teams_list in groups.items()]


def simulate_group_stage(groups: list[GroupInfo], teams: dict[str, Team]) -> tuple[dict[str, list[dict]], list[str]]:
    all_standings = {}
    for group in groups:
        standings = {t: {"team": t, "pts": 0, "gd": 0, "gs": 0, "ga": 0, "gf": 0, "gp": 0} for t in group.teams}
        for i in range(len(group.teams)):
            for j in range(i + 1, len(group.teams)):
                ta, tb = group.teams[i], group.teams[j]
                ra = teams[ta].strength if ta in teams else INITIAL_ELO
                rb = teams[tb].strength if tb in teams else INITIAL_ELO
                win_a, draw_p, win_b = match_probabilities(ra, rb)
                r = random.random()
                if r < win_a:
                    standings[ta]["pts"] += 3
                    standings[ta]["gs"] += 1
                    standings[ta]["gf"] += 1
                    standings[tb]["ga"] += 1
                elif r < win_a + draw_p:
                    standings[ta]["pts"] += 1
                    standings[tb]["pts"] += 1
                else:
                    standings[tb]["pts"] += 3
                    standings[tb]["gs"] += 1
                    standings[tb]["gf"] += 1
                    standings[ta]["ga"] += 1
                standings[ta]["gp"] += 1
                standings[tb]["gp"] += 1

        sorted_standings = sorted(standings.values(), key=lambda x: (x["pts"], x["gd"], x["gs"]), reverse=True)
        for i, s in enumerate(sorted_standings):
            s["position"] = i + 1
        all_standings[group.letter] = sorted_standings

    advancing = []
    third_place_teams = []
    for letter, standings in all_standings.items():
        advancing.extend([s["team"] for s in standings[:2]])
        third_place_teams.append({"group": letter, **standings[2]})
    third_place_teams.sort(key=lambda x: (x["pts"], x["gd"], x["gs"]), reverse=True)
    for t in third_place_teams[:BEST_THIRD_PLACE]:
        advancing.append(t["team"])

    return all_standings, advancing


def build_knockout_bracket(groups: list[GroupInfo], standings: dict[str, list[dict]], advancing: list[str]) -> list[tuple[str, str]]:
    group_winners = {}
    group_runners = {}
    for g in groups:
        st = standings[g.letter]
        group_winners[g.letter] = st[0]["team"]
        group_runners[g.letter] = st[1]["team"]

    third_advancing = [t for t in advancing if t not in group_winners.values() and t not in group_runners.values()]
    winners_list = [group_winners[chr(65 + i)] for i in range(12)]
    runners_list = [group_runners[chr(65 + i)] for i in range(12)]

    third_pts_gd = {}
    for g in groups:
        st = standings[g.letter]
        t3 = st[2]
        third_pts_gd[g.letter] = {"pts": t3["pts"], "gd": t3["gd"], "team": t3["team"]}

    sorted_third = sorted(
        [(g, d) for g, d in third_pts_gd.items() if d["team"] in third_advancing],
        key=lambda x: (x[1]["pts"], x[1]["gd"]),
        reverse=True,
    )

    bracket = []
    for i, (g_letter, _) in enumerate(sorted_third):
        if i < 12:
            w_letter = chr(65 + i)
            bracket.append((group_winners[w_letter], third_pts_gd[g_letter]["team"]))

    remaining_winners = [group_winners[chr(65 + i)] for i in range(8, 12)]
    random.shuffle(runners_list)

    for i, w in enumerate(remaining_winners):
        if i < len(runners_list):
            bracket.append((w, runners_list[i]))

    used_runners = set()
    for match in bracket:
        if match[1] in runners_list:
            used_runners.add(match[1])
    for match in bracket:
        if match[0] in runners_list:
            used_runners.add(match[0])

    unmatched = [r for r in runners_list if r not in used_runners]
    for i in range(0, len(unmatched) - 1, 2):
        if i + 1 < len(unmatched):
            bracket.append((unmatched[i], unmatched[i + 1]))

    return bracket


def simulate_knockout_stage(bracket: list[tuple[str, str]], teams: dict[str, Team]) -> str:
    round_matches = list(bracket)
    while len(round_matches) > 1:
        next_round = []
        for match in round_matches:
            ta, tb = match
            ra = teams[ta].strength if ta in teams else INITIAL_ELO
            rb = teams[tb].strength if tb in teams else INITIAL_ELO
            winner = simulate_knockout_match(ra, rb)
            next_round.append(ta if winner == "A" else tb)
        round_matches = [(next_round[i], next_round[i + 1]) for i in range(0, len(next_round), 2)]

    ta, tb = round_matches[0]
    ra = teams[ta].strength if ta in teams else INITIAL_ELO
    rb = teams[tb].strength if tb in teams else INITIAL_ELO
    return ta if simulate_knockout_match(ra, rb) == "A" else tb


def run_simulation(teams: dict[str, Team], num_simulations: int = SIMULATION_COUNT, progress_callback=None) -> tuple[list[SimulationResult], dict[str, TeamStats]]:
    wins = defaultdict(int)
    team_stats = {name: TeamStats(team=name) for name in teams}

    for sim in range(num_simulations):
        groups = simulate_group_draw(teams)
        standings, advancing = simulate_group_stage(groups, teams)

        for name in teams:
            if name in advancing:
                team_stats[name].group_stage_pct += 1
                team_stats[name].round_of_32_pct += 1

        bracket = build_knockout_bracket(groups, standings, advancing)
        winner = simulate_knockout_stage(bracket, teams)
        wins[winner] += 1

        if winner in team_stats:
            team_stats[winner].win_pct += 1

        if progress_callback:
            progress_callback(sim + 1)

        for name in teams:
            if name == winner:
                team_stats[name].final_pct += 1
                team_stats[name].semi_final_pct += 1
                team_stats[name].quarter_final_pct += 1
                team_stats[name].round_of_16_pct += 1

    results = []
    for name, count in wins.items():
        results.append(SimulationResult(
            team=name,
            wins=count,
            probability=round(count / num_simulations * 100, 2),
            best_rank=1,
        ))

    for name, stats in team_stats.items():
        stats.group_stage_pct = round(stats.group_stage_pct / num_simulations * 100, 1)
        stats.round_of_32_pct = round(stats.round_of_32_pct / num_simulations * 100, 1)
        stats.round_of_16_pct = round(stats.round_of_16_pct / num_simulations * 100, 1)
        stats.quarter_final_pct = round(stats.quarter_final_pct / num_simulations * 100, 1)
        stats.semi_final_pct = round(stats.semi_final_pct / num_simulations * 100, 1)
        stats.final_pct = round(stats.final_pct / num_simulations * 100, 1)
        stats.win_pct = round(stats.win_pct / num_simulations * 100, 1)

    results.sort(key=lambda r: r.probability, reverse=True)
    return results, team_stats
