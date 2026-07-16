from pydantic import BaseModel
from typing import Optional


class Team(BaseModel):
    name: str
    confederation: str
    fifa_rank: int = 999
    fifa_points: float = 0.0
    elo_rating: float = 1500.0
    historical_weight: float = 0.0
    recent_form_weight: float = 0.0
    squad_value: float = 0.0
    strength: float = 1500.0


class GroupInfo(BaseModel):
    letter: str
    teams: list[str]


class MatchInGroup(BaseModel):
    team_a: str
    team_b: str
    score_a: Optional[int] = None
    score_b: Optional[int] = None


class GroupStageResult(BaseModel):
    letter: str
    standings: list[dict]  # [{team, pts, gd, gs}]


class KnockoutMatch(BaseModel):
    round_name: str
    team_a: str
    team_b: str
    winner: Optional[str] = None


class SimulationResult(BaseModel):
    team: str
    wins: int
    probability: float
    best_rank: int = 0


class TeamStats(BaseModel):
    team: str
    group_stage_pct: float = 0.0
    round_of_32_pct: float = 0.0
    round_of_16_pct: float = 0.0
    quarter_final_pct: float = 0.0
    semi_final_pct: float = 0.0
    final_pct: float = 0.0
    win_pct: float = 0.0
