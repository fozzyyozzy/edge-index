"""
Edge Index v2 — NFL props projection engine.

Design principles (fixes for the v1 leakage problem):
  * Projections use ONLY games strictly before the target week.
  * No tiering off "hit rate vs the line" — the model outputs a
    probability distribution, and edge is measured against the
    DE-VIGGED market price, never against our own reconstruction.
  * Shrinkage toward position mean so small samples don't scream.

Projection = exponentially-weighted player baseline
           x opponent-defense multiplier (out-of-sample, shrunk)
           -> Normal distribution -> P(over line).
"""
from __future__ import annotations
import math
import sqlite3
from dataclasses import dataclass

import numpy as np
import pandas as pd

PROPS = {
    # prop_type: (stat column, is_count_stat, minimum usable games)
    "pass_yds":   ("pass_yds", False, 4),
    "pass_att":   ("pass_att", True, 4),
    "rush_yds":   ("rush_yds", False, 5),
    "rec_yds":    ("rec_yds", False, 5),
    "receptions": ("receptions", True, 5),
}
DECAY = 0.85          # per-game exponential decay weight
SHRINK_K = 6.0        # games of "pseudo-sample" pulling toward position mean
DEF_SHRINK_K = 8.0    # games pulling defense factor toward 1.0
STD_FLOOR_FRAC = 0.45 # floor on sigma as fraction of mean (props are noisy)


@dataclass
class Projection:
    player_id: int
    player: str
    position: str
    prop_type: str
    mean: float
    std: float
    n_games: int
    def prob_over(self, line: float) -> float:
        if self.std <= 0:
            return 0.5
        z = (line + 0.0001 - self.mean) / self.std
        return 1.0 - _norm_cdf(z)


def _norm_cdf(z: float) -> float:
    return 0.5 * (1 + math.erf(z / math.sqrt(2)))


class PropsEngine:
    """Fit on training games (all games strictly before the target week)."""

    def __init__(self, train: pd.DataFrame):
        """train: game_logs rows joined to players (name/position)."""
        self.train = train
        self._pos_mean = {}
        self._pos_std = {}
        self._def_factor = {}
        for prop, (col, _cnt, _min) in PROPS.items():
            active = train[train[col].notna() & (train[col] > 0)]
            for pos, grp in active.groupby("position"):
                self._pos_mean[(prop, pos)] = grp[col].mean()
                self._pos_std[(prop, pos)] = grp[col].std()
            # defense factor: stat allowed per opponent vs league avg
            lg = active[col].mean()
            if lg and lg > 0:
                per_def = active.groupby("opponent")[col].agg(["mean", "count"])
                for team, row in per_def.iterrows():
                    raw = row["mean"] / lg
                    w = row["count"] / (row["count"] + DEF_SHRINK_K)
                    self._def_factor[(prop, team)] = 1.0 + (raw - 1.0) * w

    def project(self, player_id: int, prop_type: str, opponent: str,
                asof_hist: pd.DataFrame | None = None) -> Projection | None:
        col, is_count, min_games = PROPS[prop_type]
        hist = asof_hist if asof_hist is not None else \
            self.train[self.train.player_id == player_id]
        vals = hist.sort_values(["season", "week"])[col].dropna()
        vals = vals[vals >= 0]
        # drop leading zeros (inactive/pre-role games) but keep in-role zeros
        vals = vals.iloc[max(0, _first_active(vals)):]
        if len(vals) < min_games:
            return None
        pos = hist.iloc[-1]["position"]
        name = hist.iloc[-1]["name"]

        w = np.array([DECAY ** i for i in range(len(vals) - 1, -1, -1)])
        w /= w.sum()
        mu = float(np.dot(w, vals))
        var = float(np.dot(w, (vals - mu) ** 2))
        sd = math.sqrt(max(var, 1e-6))

        # shrink toward position mean
        n_eff = 1.0 / float(np.sum(w ** 2))          # effective sample size
        pm = self._pos_mean.get((prop_type, pos), mu)
        ps = self._pos_std.get((prop_type, pos), sd)
        a = n_eff / (n_eff + SHRINK_K)
        mu = a * mu + (1 - a) * pm
        sd = max(a * sd + (1 - a) * (ps if not np.isnan(ps) else sd),
                 STD_FLOOR_FRAC * mu)

        # opponent adjustment
        mu *= self._def_factor.get((prop_type, opponent), 1.0)
        return Projection(player_id, name, pos, prop_type, mu, sd, len(vals))


def _first_active(vals: pd.Series) -> int:
    arr = vals.values
    for i, v in enumerate(arr):
        if v > 0:
            return i
    return len(arr)


def load_game_logs(db_path: str) -> pd.DataFrame:
    con = sqlite3.connect(db_path)
    df = pd.read_sql(
        """SELECT gl.*, p.name, p.position
           FROM game_logs gl JOIN players p ON p.id = gl.player_id""", con)
    con.close()
    return df


def load_real_lines(db_path: str, season: int | None = None) -> pd.DataFrame:
    """Real book lines only (source='actual_<book>'), both sides, core markets."""
    con = sqlite3.connect(db_path)
    q = """SELECT player_id, season, week, prop_type, direction, line, odds,
                  REPLACE(source,'actual_','') AS book
           FROM prop_lines WHERE source LIKE 'actual_%'
             AND prop_type IN ({})""".format(
        ",".join(f"'{p}'" for p in PROPS))
    if season:
        q += f" AND season={season}"
    df = pd.read_sql(q, con)
    con.close()
    return df
