"""
Edge Index v2 — Odds math (american odds, de-vig, EV, Kelly).

Every edge calculation in the system flows through here so the math
is consistent between backtests and live pick generation.
"""
from __future__ import annotations
import math
from dataclasses import dataclass


def american_to_decimal(odds: float) -> float:
    odds = float(odds)
    return 1 + (odds / 100.0 if odds > 0 else 100.0 / abs(odds))


def american_to_prob(odds: float) -> float:
    """Implied probability INCLUDING vig."""
    odds = float(odds)
    return 100.0 / (odds + 100.0) if odds > 0 else abs(odds) / (abs(odds) + 100.0)


def prob_to_american(p: float) -> float:
    p = min(max(p, 1e-6), 1 - 1e-6)
    return -100 * p / (1 - p) if p >= 0.5 else 100 * (1 - p) / p


def devig_two_way(odds_a: float, odds_b: float) -> tuple[float, float]:
    """
    Remove vig from a two-way market (over/under) — multiplicative method.
    Returns fair probabilities (p_a, p_b) summing to 1.
    """
    ia, ib = american_to_prob(odds_a), american_to_prob(odds_b)
    total = ia + ib
    return ia / total, ib / total


def ev_per_unit(model_prob: float, odds: float) -> float:
    """Expected profit per 1u staked at the offered odds."""
    dec = american_to_decimal(odds)
    return model_prob * (dec - 1) - (1 - model_prob)


def kelly_fraction(model_prob: float, odds: float, multiplier: float = 0.25) -> float:
    """
    Fractional Kelly stake (default quarter-Kelly — full Kelly is too
    volatile for prop markets where the model prob has estimation error).
    Returns fraction of bankroll; capped at 2%.
    """
    b = american_to_decimal(odds) - 1
    if b <= 0:
        return 0.0
    f = (model_prob * b - (1 - model_prob)) / b
    return max(0.0, min(f * multiplier, 0.02))


def parlay_prob(probs: list[float], correlation_haircut: float = 0.0) -> float:
    """
    Combined probability assuming independence, then shaved by a haircut
    for any residual positive correlation the caller flags.
    """
    p = math.prod(probs)
    return p * (1 - correlation_haircut)


def parlay_decimal(odds_list: list[float]) -> float:
    return math.prod(american_to_decimal(o) for o in odds_list)


@dataclass
class Edge:
    model_prob: float
    market_prob: float          # de-vigged fair prob
    odds: float                 # offered price
    @property
    def edge_pct(self) -> float:
        return self.model_prob - self.market_prob
    @property
    def ev(self) -> float:
        return ev_per_unit(self.model_prob, self.odds)
    @property
    def kelly(self) -> float:
        return kelly_fraction(self.model_prob, self.odds)
