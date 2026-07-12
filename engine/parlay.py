"""
Edge Index v2 — Parlay builder. Hard cap: 2-3 legs, always.

Philosophy (this IS the product): a small number of high-conviction
plays beats volume. Parlays are only +EV if every leg is +EV, and
correlation between legs changes the true price — so we model it.

Correlation rules of thumb (applied as haircuts/boosts to the naive
independence probability):
  * Same player, same game, same-direction stats (rec_yds + receptions
    OVER): strongly positive. Books shade for this; treat combined
    prob optimistically but price defensively -> small haircut on EV.
  * Same game, opposing directions (Team A WR over + Team B RB over):
    mildly positive in shootouts, near zero otherwise.
  * Different games: independent.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from itertools import combinations

from engine.core.odds import parlay_prob, parlay_decimal, ev_per_unit, prob_to_american


@dataclass
class Leg:
    player: str
    team: str
    game_id: str
    sport: str
    market: str          # e.g. "rec_yds OVER 62.5"
    odds: float
    model_prob: float
    market_prob: float   # de-vigged
    @property
    def edge(self) -> float:
        return self.model_prob - self.market_prob


CORR_HAIRCUT = {
    "same_player_same_dir": 0.00,   # positively correlated — helps us; books
                                    # already shade these prices, so no bonus
    "same_game": 0.03,              # mild uncertainty penalty
    "independent": 0.00,
}
NEG_CORR_BLOCK = True  # never combine negatively-correlated legs
                       # (e.g. same-game QB pass_yds OVER + WR rec_yds UNDER)


def _relationship(a: Leg, b: Leg) -> str:
    if a.game_id != b.game_id:
        return "independent"
    if a.player == b.player:
        return "same_player_same_dir"
    return "same_game"


def _is_negatively_correlated(a: Leg, b: Leg) -> bool:
    if a.game_id != b.game_id:
        return False
    dir_a, dir_b = a.market.split()[-2], b.market.split()[-2]
    # same-game legs pointing opposite directions on volume stats
    same_team = a.team == b.team
    return same_team and dir_a != dir_b


def build_parlays(legs: list[Leg], min_leg_edge: float = 0.04,
                  min_parlay_ev: float = 0.05, max_results: int = 5) -> list[dict]:
    """
    Returns the top parlays (2 and 3 legs) ranked by EV per unit.
    Every leg must independently clear min_leg_edge — a parlay is never
    a way to launder a bad leg.
    """
    qualified = [l for l in legs if l.edge >= min_leg_edge]
    out = []
    for r in (2, 3):
        for combo in combinations(qualified, r):
            if NEG_CORR_BLOCK and any(
                    _is_negatively_correlated(a, b)
                    for a, b in combinations(combo, 2)):
                continue
            haircut = max((CORR_HAIRCUT[_relationship(a, b)]
                           for a, b in combinations(combo, 2)), default=0.0)
            p = parlay_prob([l.model_prob for l in combo], haircut)
            dec = parlay_decimal([l.odds for l in combo])
            ev = p * (dec - 1) - (1 - p)
            if ev < min_parlay_ev:
                continue
            out.append(dict(
                legs=[f"{l.player} {l.market} ({int(l.odds):+d})" for l in combo],
                n_legs=r,
                combined_prob=round(p, 3),
                payout_american=round(prob_to_american(1 / dec)),
                decimal=round(dec, 2),
                ev_per_unit=round(ev, 3),
            ))
    out.sort(key=lambda d: -d["ev_per_unit"])
    return out[:max_results]


def daily_card(legs: list[Leg], max_singles: int = 3) -> dict:
    """
    The subscriber-facing card: at most `max_singles` straight plays
    (best edges) + at most 2 suggested parlays. Small, defensible, graded.
    """
    singles = sorted([l for l in legs if l.edge >= 0.04],
                     key=lambda l: -l.edge)[:max_singles]
    parlays = build_parlays(legs, max_results=2)
    return {
        "singles": [dict(player=s.player, market=s.market, odds=s.odds,
                         model_prob=round(s.model_prob, 3),
                         edge=round(s.edge, 3),
                         ev=round(ev_per_unit(s.model_prob, s.odds), 3))
                    for s in singles],
        "parlays": parlays,
    }
