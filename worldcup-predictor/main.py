#!/usr/bin/env python3
"""
World Cup 2026 Predictor
Elo-based Monte Carlo simulation for the 2026 FIFA World Cup
Supports: --simulate (pre-tournament) and --live (real data from API)
"""

import argparse
import asyncio
import sys
import time
import os

from scrapers import (
    scrape_fifa_rankings,
    scrape_historical_wc_data,
    scrape_wc2026_live,
)
from prediction import (
    build_teams, run_simulation,
    parse_live_data, build_bracket_from_games, run_live_prediction,
)
from output import (
    display_cli, display_live_standings, display_live_bracket,
    display_live_prediction, generate_charts, generate_html_report,
)
from config import SIMULATION_COUNT, LIVE_SIMULATION_COUNT


def print_banner():
    banner = """
+==========================================+
|     WORLD CUP 2026 PREDICTOR             |
|   Elo Rating + Monte Carlo Simulation    |
+==========================================+
"""
    print(banner)


async def main():
    parser = argparse.ArgumentParser(description="World Cup 2026 Champion Predictor")
    parser.add_argument(
        "--live", action="store_true",
        help="Use LIVE data from WC2026 API (real group results + predict remaining knockout)"
    )
    parser.add_argument(
        "--simulate", action="store_true",
        help="Full pre-tournament simulation (default if no --live)"
    )
    parser.add_argument(
        "--no-cache", action="store_true",
        help="Bypass cached data and re-scrape from web"
    )
    parser.add_argument(
        "--simulations", type=int, default=None,
        help="Number of Monte Carlo simulations"
    )
    parser.add_argument(
        "--no-html", action="store_true",
        help="Skip HTML report generation"
    )
    parser.add_argument(
        "--interactive", "-i", action="store_true",
        help="Launch interactive CLI mode with arrow-key menus"
    )
    args = parser.parse_args()

    if args.interactive:
        from interactive import run_interactive
        try:
            await run_interactive()
        except KeyboardInterrupt:
            print("\n\n  [!] Interrupted.")
        return

    print_banner()
    use_cache = not args.no_cache
    is_live = args.live or not args.simulate
    t_start = time.time()

    if is_live:
        await run_live_mode(args, use_cache)
    else:
        await run_simulate_mode(args, use_cache)

    total_time = time.time() - t_start
    print(f"\n  Total time: {total_time:.1f}s")
    print("-" * 46)


async def run_live_mode(args, use_cache):
    print("-" * 46)
    print("  Phase 1: Collecting Live Data")
    print("-" * 46)

    api_data = await scrape_wc2026_live(use_cache=use_cache)
    if not api_data or not api_data.get("teams"):
        print("  [!] Failed to fetch live data. Falling back to simulation mode.")
        await run_simulate_mode(args, use_cache)
        return

    rankings = await scrape_fifa_rankings(use_cache=use_cache)
    history = await scrape_historical_wc_data(use_cache=use_cache)

    print("-" * 46)
    print("  Phase 2: Building Live Models")
    print("-" * 46)

    team_by_name, team_by_id, group_map, games = parse_live_data(api_data, rankings, history)
    bracket = build_bracket_from_games(games)

    print(f"  [v] Parsed {len(team_by_name)} teams, {len(group_map)} groups")

    top5 = sorted(team_by_name.values(), key=lambda t: t.strength, reverse=True)[:5]
    for i, t in enumerate(top5, 1):
        conf = getattr(t, "confederation", "UEFA")
        print(f"      {i}. {t.name:<20} Strength: {t.strength:.0f}  "
              f"({conf})")

    completed = sum(1 for g in games if g.get("type") == "group" and g.get("finished") == "TRUE")
    total_games = sum(1 for g in games if g.get("type") == "group")
    remaining = sum(1 for g in games if g.get("type") != "group" and g.get("finished") != "TRUE")
    print(f"  [v] {completed}/{total_games} group matches played, {remaining} knockout matches remaining to play")

    print("-" * 46)
    print("  Phase 3: Live Standings")
    print("-" * 46)

    display_live_standings(group_map, team_by_name)

    print("-" * 46)
    print("  Phase 4: Knockout Bracket (Results + Predictions)")
    print("-" * 46)

    display_live_bracket(bracket)

    num_sim = args.simulations or LIVE_SIMULATION_COUNT
    print("-" * 46)
    print(f"  Phase 5: Live Monte Carlo Prediction ({num_sim:,} runs)")
    print("-" * 46)

    sim_start = time.time()
    results, team_stats = run_live_prediction(team_by_name, bracket, num_sim)
    sim_time = time.time() - sim_start
    print(f"\n  [v] Simulation complete in {sim_time:.1f}s")

    print("-" * 46)
    print("  Phase 6: Live Prediction Results")
    print("-" * 46)

    display_live_prediction(results, team_by_name, num_sim)

    print("-" * 46)
    print("  Phase 7: Generating Output")
    print("-" * 46)

    charts = generate_charts(results, team_stats)
    print("  [v] Charts generated")

    if not args.no_html:
        generate_html_report(
            results, team_stats, team_by_name, charts,
            is_live=True, group_map=group_map, bracket=bracket,
        )


async def run_simulate_mode(args, use_cache):
    print("-" * 46)
    print("  Phase 1: Collecting Data")
    print("-" * 46)

    rankings = await scrape_fifa_rankings(use_cache=use_cache)
    if not rankings:
        print("  [x] Failed to get FIFA rankings")
        sys.exit(1)

    from scrapers import scrape_qualified_teams
    qualified = await scrape_qualified_teams(use_cache=use_cache)
    if not qualified:
        print("  [x] Failed to get qualified teams")
        sys.exit(1)

    history = await scrape_historical_wc_data(use_cache=use_cache)

    print("-" * 46)
    print("  Phase 2: Building Team Models")
    print("-" * 46)

    teams = build_teams(rankings, qualified, history)
    print(f"  [v] Built {len(teams)} team models")

    top5 = sorted(teams.values(), key=lambda t: t.strength, reverse=True)[:5]
    for i, t in enumerate(top5, 1):
        print(f"      {i}. {t.name:<20} Strength: {t.strength:.0f}  "
              f"(ELO: {t.elo_rating:.0f} + Squad: {t.squad_value:.0f})")

    num_sim = args.simulations or SIMULATION_COUNT
    print("-" * 46)
    print(f"  Phase 3: Monte Carlo Simulation ({num_sim:,} runs)")
    print("-" * 46)

    sim_start = time.time()
    results, team_stats = run_simulation(teams, num_simulations=num_sim)
    sim_time = time.time() - sim_start
    print(f"\n  [v] Simulation complete in {sim_time:.1f}s")

    print("-" * 46)
    print("  Phase 4: Results")
    print("-" * 46)

    display_cli(results, team_stats)

    print("-" * 46)
    print("  Phase 5: Generating Output")
    print("-" * 46)

    charts = generate_charts(results, team_stats)
    print("  [v] Charts generated")

    if not args.no_html:
        generate_html_report(results, team_stats, teams, charts, is_live=False)


if __name__ == "__main__":
    asyncio.run(main())
