"""Small committed inputs for the GitHub Actions line capture (no CFBD cache there).

schedule_<season>.csv   FBS-involved games: id, week, kickoff, teams, flags (update_week)
targets_<season>_wk<NN>.csv  per game: ratings margin, QB delta, frozen k/b_qb (project_week)
The capture job recomputes the frozen-model edge against each live DK line:
    edge = k * (ratings_margin - dk_line_margin) + b_qb * qb_delta
"""
from __future__ import annotations

import pandas as pd

from engine.cfb import config
from engine.cfb.lines.capture import LINES, TARGETS


def export_schedule(season: int = config.CURRENT_SEASON) -> str:
    g = pd.read_parquet(config.CLEAN / "games.parquet")
    g = g[(g.season == season) & g.fbs_involved]
    out = g[["game_id", "season", "week", "season_type", "kickoff_utc", "home_team",
             "away_team", "both_fbs", "neutral_site", "completed"]].sort_values("kickoff_utc")
    LINES.mkdir(parents=True, exist_ok=True)
    path = LINES / f"schedule_{season}.csv"
    out.to_csv(path, index=False)
    return str(path)


def export_targets(d: pd.DataFrame, params: dict, season: int, week: int) -> str:
    """d: model frame for the week after margin_model.prep (ratings_margin, bucket, qb_delta)."""
    t = d[["game_id", "season", "week", "bucket", "home_team", "away_team", "ratings_margin",
           "qb_delta"]].copy()
    t["both_fbs"] = True
    t["k"] = t.bucket.map(lambda b: params["coef"][f"k_{b}"])
    t["b_qb"] = params["coef"].get("qb_delta", 0.0)
    TARGETS.mkdir(parents=True, exist_ok=True)
    path = TARGETS / f"targets_{season}_wk{week:02d}.csv"
    t.to_csv(path, index=False)
    return str(path)
