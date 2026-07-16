import io
import os
import base64
from datetime import datetime, timezone, timedelta
from collections import defaultdict

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.text import Text
from rich import box
from jinja2 import Environment, FileSystemLoader

from config import OUTPUT_DIR, BASE_DIR, ROUND_NAMES, CONF_MAP
from models import SimulationResult, TeamStats
from prediction import predict_score


console = Console()


def display_cli(results: list[SimulationResult], team_stats: dict[str, TeamStats]):
    title = Text("World Cup 2026 - Monte Carlo Prediction", style="bold yellow")
    console.print(Panel(title, border_style="yellow"))
    console.print("\n[dim]48 Teams | 12 Groups | 32 Knockout Teams[/dim]\n")

    table = Table(box=box.SIMPLE, header_style="bold cyan")
    table.add_column("#", style="dim", width=3)
    table.add_column("Team", style="white", width=22)
    table.add_column("Win %", style="bold yellow", width=8, justify="right")
    table.add_column("Final %", style="bold", width=8, justify="right")
    table.add_column("SF %", style="bold", width=7, justify="right")
    table.add_column("QF %", style="bold", width=7, justify="right")
    table.add_column("R32 %", style="bold", width=7, justify="right")
    table.add_column("Group %", style="bold", width=7, justify="right")

    for i, r in enumerate(results[:20], 1):
        name = r.team[:20]
        st = team_stats.get(r.team, TeamStats(team=r.team))
        table.add_row(
            str(i), name,
            f"{r.probability:.1f}%",
            f"{st.final_pct:.1f}%",
            f"{st.semi_final_pct:.1f}%",
            f"{st.quarter_final_pct:.1f}%",
            f"{st.round_of_32_pct:.1f}%",
            f"{st.group_stage_pct:.1f}%",
        )

    console.print(table)
    top_team = results[0].team if results else "Unknown"
    top_pct = results[0].probability if results else 0
    console.print(f"\n[bold green]>> Predicted Champion: {top_team}[/bold green] "
                  f"([yellow]{top_pct:.1f}%[/yellow])")
    if len(results) > 1:
        dh = next((r for r in results if r.probability > 1 and r.probability < 5), None)
        if dh:
            console.print(f"[dim]>> Dark Horse: {dh.team} ({dh.probability:.1f}%)[/dim]")


def display_live_standings(group_map: dict, team_by_name: dict):
    title = Text("World Cup 2026 - Live Standings", style="bold green")
    console.print(Panel(title, border_style="green"))
    console.print("[dim]Group Stage - Complete[/dim]\n")

    for letter in sorted(group_map.keys()):
        standings = sorted(group_map[letter], key=lambda x: (-x["pts"], -x["gd"], -x["gs"]))
        table = Table(box=box.SIMPLE, header_style="bold", title=f"Group {letter}", title_style="bold cyan")
        table.add_column("Pos", width=3)
        table.add_column("Team", width=22)
        table.add_column("Pts", width=4, justify="right")
        table.add_column("W", width=3, justify="right")
        table.add_column("D", width=3, justify="right")
        table.add_column("L", width=3, justify="right")
        table.add_column("GF", width=3, justify="right")
        table.add_column("GA", width=3, justify="right")
        table.add_column("GD", width=4, justify="right")

        for i, s in enumerate(standings, 1):
            qual = " [green]Q[/green]" if i <= 2 else ""
            qual = " [yellow]Q3[/yellow]" if i == 3 else qual
            table.add_row(
                str(i),
                f"{s['team']}{qual}",
                str(s["pts"]), str(s["w"]), str(s["d"]), str(s["l"]),
                str(s["gf"]), str(s["ga"]), str(s["gd"]),
            )
        console.print(table)
        console.print("")


def display_live_bracket(bracket: dict):
    title = Text("World Cup 2026 - Knockout Bracket", style="bold green")
    console.print(Panel(title, border_style="green"))

    rounds_display = [
        ("round_32", "Round of 32"),
        ("round_16", "Round of 16"),
        ("quarter_final", "Quarter-finals"),
        ("semi_final", "Semi-finals"),
        ("third_place", "Third Place"),
        ("final", "Final"),
    ]

    for rnd_key, rnd_name in rounds_display:
        matches = bracket.get(rnd_key, [])
        if not matches:
            continue

        table = Table(box=box.SIMPLE, header_style="bold", title=rnd_name, title_style="bold yellow")
        table.add_column("Match", width=6)
        table.add_column("Team A", width=22)
        table.add_column("Score", width=8, justify="center")
        table.add_column("Team B", width=22)
        table.add_column("Winner", width=22)

        for m in matches:
            mid = str(m["match_id"])
            ta = m["team_a"] or "TBD"
            tb = m["team_b"] or "TBD"
            sa = m["score_a"] if m["score_a"] is not None else ""
            sb = m["score_b"] if m["score_b"] is not None else ""
            score = f"{sa}-{sb}" if sa != "" else "? - ?"
            winner = m["winner"] or "[dim]Pending[/dim]"

            ta_style = "[bold]" if m["winner"] == ta else ""
            tb_style = "[bold]" if m["winner"] == tb else ""
            w_style = "[green]" if m["winner"] else "[dim]"

            table.add_row(mid, ta_style + ta, score, tb_style + tb, f"{w_style}{winner}")
        console.print(table)
        console.print("")


def display_live_prediction(results: list[SimulationResult], team_by_name: dict, num_simulations: int = 50000):
    title = Text("World Cup 2026 - Live Knockout Prediction", style="bold yellow")
    console.print(Panel(title, border_style="yellow"))
    console.print(f"\n[dim]Remaining matches simulated {num_simulations:,} times[/dim]\n")

    table = Table(box=box.SIMPLE, header_style="bold cyan")
    table.add_column("#", style="dim", width=3)
    table.add_column("Team", style="white", width=22)
    table.add_column("Champion %", style="bold yellow", width=12, justify="right")
    table.add_column("ELO", width=8, justify="right")

    for i, r in enumerate(results[:15], 1):
        name = r.team[:20]
        elo = ""
        if name in team_by_name:
            elo = str(int(team_by_name[name].strength))
        table.add_row(str(i), name, f"{r.probability:.1f}%", elo)

    console.print(table)
    if results:
        console.print(f"\n[bold green]>> Predicted Champion: {results[0].team}[/bold green] "
                      f"([yellow]{results[0].probability:.1f}%[/yellow])")
    if len(results) > 1:
        dh = next((r for r in results if r.probability > 1 and r.probability < 5), None)
        if dh:
            console.print(f"[dim]>> Dark Horse: {dh.team} ({dh.probability:.1f}%)[/dim]")


def generate_charts(results: list[SimulationResult], team_stats: dict[str, TeamStats]) -> dict[str, str]:
    charts = {}

    fig, ax = plt.subplots(figsize=(12, 7))
    top15 = results[:15]
    teams = [r.team[:12] for r in top15]
    probs = [r.probability for r in top15]
    colors = plt.cm.YlOrRd(np.linspace(0.3, 0.9, len(teams)))
    bars = ax.barh(range(len(teams)), probs, color=colors[::-1])
    ax.set_yticks(range(len(teams)))
    ax.set_yticklabels(teams, fontsize=10)
    ax.set_xlabel("Win Probability (%)", fontsize=11)
    ax.set_title("World Cup 2026 - Top Favorites", fontsize=14, fontweight="bold")
    ax.invert_yaxis()
    for bar, prob in zip(bars, probs):
        ax.text(bar.get_width() + 0.3, bar.get_y() + bar.get_height() / 2,
                f"{prob:.1f}%", va="center", fontsize=9)
    plt.tight_layout()
    charts["top15"] = _fig_to_base64(fig)
    plt.close(fig)

    fig2, ax2 = plt.subplots(figsize=(8, 6))
    conf_data = defaultdict(float)
    for r in results:
        for name in team_stats:
            if name == r.team:
                conf = CONF_MAP.get(name, "UEFA")
                conf_data[conf] += r.probability
                break
    if conf_data:
        labels = list(conf_data.keys())
        values = list(conf_data.values())
        colors = ["#2196F3", "#4CAF50", "#FF9800", "#E91E63", "#9C27B0", "#00BCD4"]
        ax2.pie(values, labels=labels, autopct="%1.1f%%",
                colors=colors[:len(labels)], startangle=90, textprops={"fontsize": 11})
        ax2.set_title("Win Probability by Confederation", fontsize=13, fontweight="bold")
    plt.tight_layout()
    charts["confederation"] = _fig_to_base64(fig2)
    plt.close(fig2)

    top8 = results[:8]
    if top8:
        fig3, ax3 = plt.subplots(figsize=(14, 7))
        stages = ["Group", "R32", "R16", "QF", "SF", "Final", "Win"]
        x = np.arange(len(stages))
        bar_width = 0.1
        for i, team_name in enumerate(top8):
            st = team_stats.get(team_name.team, TeamStats(team=team_name.team))
            vals = [100, 100, 100, 100, 100, 100, st.win_pct] if st.win_pct == 0 else [
                st.group_stage_pct or 100, st.round_of_32_pct or 100,
                st.round_of_16_pct or 100, st.quarter_final_pct or 100,
                st.semi_final_pct or 100, st.final_pct or 100, st.win_pct,
            ]
            ax3.bar(x + i * bar_width, vals, bar_width, label=team_name.team[:10])
        ax3.set_xticks(x + bar_width * 3.5)
        ax3.set_xticklabels(stages, fontsize=10)
        ax3.set_ylabel("Reaching Stage (%)", fontsize=11)
        ax3.set_title("Top 8 Teams - Stage Advancement", fontsize=13, fontweight="bold")
        ax3.legend(fontsize=8, loc="upper left")
        ax3.set_ylim(0, 105)
        plt.tight_layout()
        charts["stage_advancement"] = _fig_to_base64(fig3)
        plt.close(fig3)

    return charts


def _fig_to_base64(fig) -> str:
    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=150, bbox_inches="tight")
    buf.seek(0)
    img_b64 = base64.b64encode(buf.getvalue()).decode("utf-8")
    buf.close()
    return img_b64


def generate_html_report(results, team_stats, teams_info, charts, is_live=False, group_map=None, bracket=None):
    env = Environment(loader=FileSystemLoader(str(BASE_DIR / "templates")))
    template = env.get_template("report.html")

    top20 = []
    conf_data = defaultdict(float)
    for r in results[:20]:
        st = team_stats.get(r.team, TeamStats(team=r.team))
        conf = ""
        for name, t in (teams_info.items() if isinstance(teams_info, dict) else []):
            if name == r.team:
                conf = getattr(t, "confederation", "")
                conf_data[conf] += r.probability
                break
        if not conf:
            conf = CONF_MAP.get(r.team, "")
            conf_data[conf] += r.probability
        top20.append({
            "rank": len(top20) + 1,
            "name": r.team,
            "confederation": conf,
            "win_pct": r.probability,
            "final_pct": getattr(st, "final_pct", 0),
            "semi_pct": getattr(st, "semi_final_pct", 0),
            "quarter_pct": getattr(st, "quarter_final_pct", 0),
            "group_pct": getattr(st, "group_stage_pct", 0),
        })

    conf_stats = [{"name": k, "prob": round(v, 1)} for k, v in
                  sorted(conf_data.items(), key=lambda x: x[1], reverse=True)]

    winner = results[0].team if results else "N/A"
    runner_up = results[1].team if len(results) > 1 else "N/A"

    group_tables = []
    if group_map:
        for letter in sorted(group_map.keys()):
            standings = sorted(group_map[letter], key=lambda x: (-x["pts"], -x["gd"], -x["gs"]))
            group_tables.append({"letter": letter, "standings": standings})

    bracket_rounds = []
    if bracket:
        for rnd_key in ["round_32", "round_16", "quarter_final", "semi_final", "final"]:
            matches = bracket.get(rnd_key, [])
            if matches:
                bracket_rounds.append({
                    "name": ROUND_NAMES.get(rnd_key, rnd_key),
                    "matches": matches,
                })

    html = template.render(
        generated_at=datetime.now().strftime("%Y-%m-%d %H:%M"),
        winner=winner,
        runner_up=runner_up,
        top20=top20,
        conf_stats=conf_stats,
        total_simulations=10000,
        chart_top15=charts.get("top15", ""),
        chart_conf=charts.get("confederation", ""),
        chart_stage=charts.get("stage_advancement", ""),
        is_live=is_live,
        group_tables=group_tables,
        bracket_rounds=bracket_rounds,
    )

    report_path = OUTPUT_DIR / "worldcup_2026_prediction.html"
    with open(report_path, "w", encoding="utf-8") as f:
        f.write(html)

    print(f"\n  [v] HTML Report: {report_path}")
    return str(report_path)


def _parse_local_date(local_date: str):
    try:
        parts = local_date.split()
        if len(parts) != 2:
            return None
        date_part, time_part = parts
        month, day, year = date_part.split("/")
        hour, minute = time_part.split(":")
        return datetime(int(year), int(month), int(day), int(hour), int(minute))
    except (ValueError, IndexError):
        return None


def display_upcoming_matches(games: list, team_by_name: dict):
    tz_wib = timezone(timedelta(hours=7))
    now_utc = datetime.now(timezone.utc)
    today_start = now_utc.replace(hour=0, minute=0, second=0, microsecond=0)
    cutoff = today_start + timedelta(days=2)

    upcoming = []
    for g in games:
        if g.get("finished") == "TRUE":
            continue
        ld = g.get("local_date", "")
        if not ld:
            continue
        dt_venue = _parse_local_date(ld)
        if dt_venue is None:
            continue
        date_str = g.get("date", "")
        try:
            match_utc = datetime.fromisoformat(date_str.replace("Z", "+00:00")) if date_str else None
        except (ValueError, TypeError):
            match_utc = None
        ref_dt = match_utc if match_utc else dt_venue
        if not (today_start <= ref_dt <= cutoff):
            continue
        upcoming.append((ref_dt, dt_venue, match_utc, g))

    if not upcoming:
        console.print("\n[bold yellow]No upcoming matches in the next 2 days.[/bold yellow]")
        return

    upcoming.sort(key=lambda x: x[0])

    title = Text("Upcoming Matches — Next 2 Days", style="bold cyan")
    console.print(Panel(title, border_style="cyan"))
    console.print(f"[dim]WIB (UTC+7) • {len(upcoming)} matches[/dim]\n")

    table = Table(box=box.SIMPLE, header_style="bold")
    table.add_column("Date", width=12)
    table.add_column("WIB", width=11, justify="right")
    table.add_column("Round", width=16)
    table.add_column("Match", width=44)
    table.add_column("Score", width=8, justify="center")
    table.add_column("Conf.", width=8, justify="right")

    for ref_dt, dt_venue, match_utc, g in upcoming:
        wib_dt = (match_utc if match_utc else dt_venue).astimezone(tz_wib)
        date_part = wib_dt.strftime("%d/%m/%Y")
        time_part = wib_dt.strftime("%H:%M WIB")

        rnd = g.get("type", "group")
        round_label = ROUND_NAMES.get(rnd, rnd.replace("_", " ").title())

        home = g.get("home_team_name_en", "?")
        away = g.get("away_team_name_en", "?")

        home_team = team_by_name.get(home)
        away_team = team_by_name.get(away)
        if home_team and away_team:
            ha, aa, conf = predict_score(home_team.strength, away_team.strength)
            prediction = f"{ha}–{aa}"
        else:
            prediction = "[dim]?–?[/dim]"
            conf = 0.0

        conf_str = f"[green]{conf}%[/green]" if conf >= 60 else (
            f"[yellow]{conf}%[/yellow]" if conf >= 40 else f"[red]{conf}%[/red]")

        table.add_row(
            date_part, time_part, round_label,
            f"{home} vs {away}",
            prediction, conf_str,
        )

    console.print(table)
