"""
Interactive CLI mode for World Cup 2026 Predictor
Arrow-key menus via questionary, Rich Progress bars for each phase.
"""

import asyncio
import time

from rich.console import Console
from rich.progress import (
    Progress, SpinnerColumn, BarColumn, TextColumn,
    TaskProgressColumn, TimeElapsedColumn, TimeRemainingColumn,
)
from rich.panel import Panel
from rich.text import Text
from rich import box

import questionary
from questionary import Choice

from scrapers import (
    scrape_fifa_rankings, scrape_historical_wc_data,
    scrape_wc2026_live, scrape_qualified_teams,
)
from prediction import (
    build_teams, run_simulation,
    parse_live_data, build_bracket_from_games, run_live_prediction,
)
from output import (
    display_cli, display_live_standings, display_live_bracket,
    display_live_prediction, generate_charts, generate_html_report,
    display_upcoming_matches,
)
from config import SIMULATION_COUNT, LIVE_SIMULATION_COUNT

console = Console()


class Settings:
    def __init__(self):
        self.live_sim_count = LIVE_SIMULATION_COUNT
        self.full_sim_count = SIMULATION_COUNT
        self.generate_html = True

    def display(self):
        console.print(Panel(
            f"[bold]Settings[/bold]\n\n"
            f"  [cyan]Live Simulations[/cyan]    : {self.live_sim_count:,}\n"
            f"  [cyan]Full Simulations[/cyan]    : {self.full_sim_count:,}\n"
            f"  [cyan]Generate HTML[/cyan]       : {'Yes' if self.generate_html else 'No'}",
            title="⚙️  Configuration", border_style="cyan"
        ))


settings = Settings()


async def show_results_and_wait(title: str, content_fn):
    console.print()
    content_fn()
    console.print()
    await questionary.press_any_key_to_continue(
        "Press any key to return to menu..."
    ).ask_async()


async def do_live_prediction():
    with Progress(
        SpinnerColumn(),
        TextColumn("[bold]{task.description}"),
        console=console,
        transient=True,
    ) as progress:
        fetch_task = progress.add_task("Fetching live data...", total=None)
        api_data = await scrape_wc2026_live(use_cache=False)
        if not api_data or not api_data.get("teams"):
            progress.update(fetch_task, description="[red]Failed to fetch live data[/red]")
            return
        progress.update(fetch_task, description="[green]✓ Live data fetched[/green]")

        rank_task = progress.add_task("Fetching FIFA rankings...", total=None)
        rankings = await scrape_fifa_rankings(use_cache=True)
        progress.update(rank_task, description="[green]✓ Rankings loaded[/green]")

        hist_task = progress.add_task("Fetching World Cup history...", total=None)
        history = await scrape_historical_wc_data(use_cache=True)
        progress.update(hist_task, description="[green]✓ History loaded[/green]")

        parse_task = progress.add_task("Building team models...", total=None)
        team_by_name, team_by_id, group_map, games = parse_live_data(api_data, rankings, history)
        bracket = build_bracket_from_games(games)
        progress.update(parse_task, description=f"[green]✓ {len(team_by_name)} teams built[/green]")

    console.print()
    completed = sum(1 for g in games if g.get("type") == "group" and g.get("finished") == "TRUE")
    total_games = sum(1 for g in games if g.get("type") == "group")
    remaining = sum(1 for g in games if g.get("type") != "group" and g.get("finished") != "TRUE")
    console.print(f"[dim]{completed}/{total_games} group matches played, {remaining} knockout remaining[/dim]\n")

    display_live_standings(group_map, team_by_name)
    display_live_bracket(bracket)

    num_sim = settings.live_sim_count
    console.print(f"\n[bold]Running {num_sim:,} Monte Carlo simulations...[/bold]")

    sim_start = time.time()
    results, team_stats = run_live_prediction(
        team_by_name, bracket, num_sim,
        progress_callback=_make_progress_callback("Simulating knockout...", num_sim),
    )
    sim_time = time.time() - sim_start
    console.print(f"[dim]Simulation complete in {sim_time:.1f}s[/dim]\n")

    display_live_prediction(results, team_by_name, num_sim)

    if settings.generate_html:
        charts = generate_charts(results, team_stats)
        generate_html_report(
            results, team_stats, team_by_name, charts,
            is_live=True, group_map=group_map, bracket=bracket,
        )
        console.print("[green]✓ HTML report generated[/green]")

    await questionary.press_any_key_to_continue("\nPress any key to return to menu...").ask_async()


async def do_upcoming_matches():
    with Progress(
        SpinnerColumn(),
        TextColumn("[bold]{task.description}"),
        console=console,
        transient=True,
    ) as progress:
        fetch_task = progress.add_task("Fetching live data...", total=None)
        api_data = await scrape_wc2026_live(use_cache=False)
        if not api_data or not api_data.get("teams"):
            progress.update(fetch_task, description="[yellow]Live API failed, using cached data...[/yellow]")
            api_data = await scrape_wc2026_live(use_cache=True)
        if not api_data or not api_data.get("teams"):
            progress.update(fetch_task, description="[red]No data available[/red]")
            return
        progress.update(fetch_task, description="[green]✓ Data loaded[/green]")

        rank_task = progress.add_task("Fetching FIFA rankings...", total=None)
        rankings = await scrape_fifa_rankings(use_cache=True)
        progress.update(rank_task, description="[green]✓ Rankings loaded[/green]")

        hist_task = progress.add_task("Fetching World Cup history...", total=None)
        history = await scrape_historical_wc_data(use_cache=True)
        progress.update(hist_task, description="[green]✓ History loaded[/green]")

        parse_task = progress.add_task("Building team models...", total=None)
        team_by_name, team_by_id, _, games = parse_live_data(api_data, rankings, history)
        progress.update(parse_task, description=f"[green]✓ {len(team_by_name)} teams[/green]")

    console.clear()
    display_upcoming_matches(games, team_by_name)

    await questionary.press_any_key_to_continue("\nPress any key to return to menu...").ask_async()


async def do_full_simulation():
    with Progress(
        SpinnerColumn(),
        TextColumn("[bold]{task.description}"),
        console=console,
        transient=True,
    ) as progress:
        fetch_task = progress.add_task("Fetching data...", total=None)
        rankings = await scrape_fifa_rankings(use_cache=True)
        qualified = await scrape_qualified_teams(use_cache=True)
        history = await scrape_historical_wc_data(use_cache=True)
        progress.update(fetch_task, description="[green]✓ Data loaded[/green]")

        build_task = progress.add_task("Building team models...", total=None)
        teams = build_teams(rankings, qualified, history)
        progress.update(build_task, description=f"[green]✓ {len(teams)} teams built[/green]")

    num_sim = settings.full_sim_count
    console.print(f"\n[bold]Running {num_sim:,} full tournament simulations...[/bold]")

    sim_start = time.time()
    results, team_stats = run_simulation(
        teams, num_simulations=num_sim,
        progress_callback=_make_progress_callback("Simulating tournaments...", num_sim),
    )
    sim_time = time.time() - sim_start
    console.print(f"[dim]Complete in {sim_time:.1f}s[/dim]\n")

    display_cli(results, team_stats)

    if settings.generate_html:
        charts = generate_charts(results, team_stats)
        generate_html_report(results, team_stats, teams, charts, is_live=False)
        console.print("[green]✓ HTML report generated[/green]")

    await questionary.press_any_key_to_continue("\nPress any key to return to menu...").ask_async()


def _make_progress_callback(description: str, total: int):
    progress = Progress(
        TextColumn("[bold]{task.description}"),
        BarColumn(),
        TaskProgressColumn(),
        TimeElapsedColumn(),
        TimeRemainingColumn(),
        console=console,
    )
    progress.start()
    task = progress.add_task(description, total=total)

    def callback(current: int):
        progress.update(task, completed=current)
        if current >= total:
            progress.stop()

    return callback


async def do_settings():
    while True:
        console.clear()
        settings.display()
        console.print()

        choice = await questionary.select(
            "Choose a setting to change:",
            choices=[
                Choice("Live Simulation Count", "live"),
                Choice("Full Simulation Count", "full"),
                Choice(f"Generate HTML Report: {'Yes' if settings.generate_html else 'No'}", "html"),
                Choice("Back to Main Menu", "back"),
            ],
        ).ask_async()

        if choice == "back":
            break
        elif choice == "live":
            val = await questionary.text(
                "Live simulation count:",
                default=str(settings.live_sim_count),
                validate=lambda x: x.isdigit() and int(x) > 0,
            ).ask_async()
            if val:
                settings.live_sim_count = int(val)
        elif choice == "full":
            val = await questionary.text(
                "Full simulation count:",
                default=str(settings.full_sim_count),
                validate=lambda x: x.isdigit() and int(x) > 0,
            ).ask_async()
            if val:
                settings.full_sim_count = int(val)
        elif choice == "html":
            settings.generate_html = not settings.generate_html


async def run_interactive():
    while True:
        console.clear()
        banner = """
╔══════════════════════════════════════════╗
║      WORLD CUP 2026 PREDICTOR            ║
║   Elo Rating + Monte Carlo Simulation    ║
╚══════════════════════════════════════════╝
"""
        console.print(banner, style="bold green")
        console.print("[dim]Navigate with ↑↓ arrows, press Enter to select[/dim]\n")

        choice = await questionary.select(
            "Main Menu:",
            choices=[
                Choice("🏆  Live Prediction (real data + remaining knockout)", "live"),
                Choice("📅  Upcoming Matches (next 2 days — with score prediction)", "upcoming"),
                Choice("🔮  Full Tournament Simulation", "full"),
                Choice("⚙️  Settings", "settings"),
                Choice("❌  Exit", "exit"),
            ],
            qmark="›",
            pointer="❯",
        ).ask_async()

        if choice == "exit" or choice is None:
            console.print("\n[bold]Goodbye![/bold]")
            break
        elif choice == "live":
            await do_live_prediction()
        elif choice == "upcoming":
            await do_upcoming_matches()
        elif choice == "full":
            await do_full_simulation()
        elif choice == "settings":
            await do_settings()
