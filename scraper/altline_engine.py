"""
Alt-Line Value Engine
=====================
Input : a DK ladder (threshold, odds) for one player/market + your model projection
Output: model win% at every rung, implied win%, EV, breakeven odds, and the best rung to bet.

How it works
1. Turn each rung's odds into an implied probability.
2. Fit a distribution to the ladder (yards -> lognormal, receptions -> Poisson,
   completions/attempts -> normal). The fit gives the MARKET's median and spread.
3. Shift that distribution so its median = YOUR projection (spread stays market-calibrated).
4. P(over threshold) at every rung vs. the payout -> EV per unit. Best rung = max EV
   above a minimum-probability floor (so you don't chase 8-leg-lottery rungs).
"""
import math
from dataclasses import dataclass
from typing import List, Optional, Tuple

try:
    from scipy.stats import norm, poisson, lognorm
    from scipy.optimize import minimize
except ImportError:
    raise SystemExit("pip install scipy")

YARD_MARKETS  = {"rec_yds", "rush_yds", "pass_yds"}
COUNT_MARKETS = {"receptions", "pass_cmps", "rush_att", "pass_att"}
DEFAULT_SIGMA = {"rec_yds": 0.62, "rush_yds": 0.55, "pass_yds": 0.28}  # lognormal sigma
DEFAULT_SD    = {"pass_cmps": 4.5, "rush_att": 4.0, "pass_att": 5.5}    # normal sd
DK_HOLD       = 0.045   # approx per-side hold on DK ladders, used only for fitting


# ---------- odds helpers ----------
def implied_prob(american: int) -> float:
    return (-american) / (-american + 100) if american < 0 else 100 / (american + 100)

def payout_per_unit(american: int) -> float:
    return 100 / (-american) if american < 0 else american / 100

def breakeven_odds(p: float) -> int:
    """Worst American odds at which betting this rung is still +EV."""
    if p <= 0 or p >= 1:
        return 0
    dec = 1 / p
    return int(round(-100 / (dec - 1))) if dec < 2 else int(round((dec - 1) * 100))


# ---------- distributions ----------
@dataclass
class Dist:
    kind: str          # 'lognormal' | 'poisson' | 'normal'
    center: float      # median (lognormal/normal) or mean (poisson)
    spread: float      # sigma (lognormal), sd (normal), unused for poisson

    def p_over(self, threshold: float) -> float:
        """P(X >= threshold) for 'N+' style rungs."""
        if self.kind == "lognormal":
            return 1 - lognorm.cdf(threshold - 0.5, s=self.spread, scale=self.center)
        if self.kind == "poisson":
            return 1 - poisson.cdf(threshold - 1, mu=self.center)
        if self.kind == "normal":
            return 1 - norm.cdf(threshold - 0.5, loc=self.center, scale=self.spread)
        raise ValueError(self.kind)

    def shifted(self, new_center: float) -> "Dist":
        return Dist(self.kind, new_center, self.spread)


def fit_market_dist(market: str, ladder: List[Tuple[float, int]]) -> Dist:
    """Fit the market-implied distribution from the ladder rungs that have odds."""
    kind = "lognormal" if market in YARD_MARKETS else ("poisson" if market == "receptions" else "normal")
    fair = [(t, max(0.02, min(0.98, implied_prob(o) - DK_HOLD))) for t, o in ladder]

    # initial center = threshold nearest 50%
    center0 = min(fair, key=lambda x: abs(x[1] - 0.5))[0]

    if kind == "poisson" or len(fair) < 3:
        spread0 = DEFAULT_SIGMA.get(market, DEFAULT_SD.get(market, 1.0))
        if kind == "poisson":
            return Dist(kind, center0, 0)
        # single-rung: center only
        return Dist(kind, center0, spread0)

    def loss(params):
        c, s = params
        if c <= 0 or s <= 0:
            return 1e9
        d = Dist(kind, c, s)
        return sum((norm.ppf(d.p_over(t)) - norm.ppf(p)) ** 2 for t, p in fair)

    spread0 = DEFAULT_SIGMA.get(market, DEFAULT_SD.get(market, 1.0))
    res = minimize(loss, [center0, spread0], method="Nelder-Mead")
    c, s = res.x
    return Dist(kind, float(c), float(s))




# ---------- DK ladder model (fit 9/2/2026 from JSN / Shaheed / Evans full ladders) ----------
# hold curve: logit(implied) = HOLD_A + HOLD_B * logit(fair). Max err 1.5pp across 14 rungs.
HOLD_A, HOLD_B = 0.159, 1.135
EST_HOLD_BUMP = 0.045   # extra logit hold on ESTIMATED rungs so unseen deep rungs are priced conservatively
# lognormal sigma scales with the median (low-volume players are far noisier)
def sigma_for_median(median: float, market: str) -> float:
    if market == "rec_yds":
        return float(min(2.2, max(0.45, math.exp(3.170) * median ** -0.812)))
    if market == "rush_yds":
        return float(min(2.0, max(0.40, 0.9 * math.exp(3.170) * median ** -0.812)))
    return DEFAULT_SIGMA.get(market, 0.6)

def dk_implied_from_fair(fair: float) -> float:
    fair = min(0.985, max(0.015, fair))
    lg = math.log(fair / (1 - fair))
    z = HOLD_A + EST_HOLD_BUMP + HOLD_B * lg
    return 1 / (1 + math.exp(-z))

def prob_to_american(p: float) -> int:
    dec = 1 / p
    return int(round(-100 / (dec - 1))) if dec < 2 else int(round((dec - 1) * 100))

DK_RUNGS = {   # rung ladders DK actually posts (from 9/2 pastes)
    "rec_yds":  [15, 25, 40, 50, 60, 70, 80, 90, 100, 110, 120, 130, 140, 150, 160, 170, 180, 190, 200],
    "rush_yds": [10, 15, 20, 25, 30, 40, 50, 60, 70, 80, 90, 100, 110, 120, 130, 140, 150, 160, 170, 180],
    "pass_yds": list(range(150, 441, 10)),
}
DK_MIN_IMPLIED, DK_MAX_IMPLIED = 0.06, 0.925   # DK stops posting rungs outside roughly +1500 / -1200

def estimate_ladder(market: str, main_line: float, main_odds: int,
                    rungs: Optional[List[float]] = None) -> Tuple[List[Tuple[float, int]], Dist]:
    """Given ONLY the main line + odds, rebuild DK's full ladder with estimated odds."""
    fair_main = implied_prob(main_odds) - DK_HOLD
    z = norm.ppf(1 - fair_main)          # P(X >= L) = fair  ->  (L-0.5 - center)/spread = z
    if market in YARD_MARKETS:
        med = main_line
        for _ in range(50):              # fixed point: sigma depends on median
            s = sigma_for_median(med, market)
            med = math.exp(math.log(main_line - 0.5) - z * s)
        dist = Dist("lognormal", med, sigma_for_median(med, market))
    elif market == "receptions":
        mu = main_line
        for _ in range(200):
            mu += (fair_main - Dist("poisson", mu, 0).p_over(main_line)) * 2
        dist = Dist("poisson", mu, 0)
    else:
        sd = DEFAULT_SD.get(market, 4.5)
        dist = Dist("normal", main_line - 0.5 - z * sd, sd)

    if rungs is None:
        base = DK_RUNGS.get(market) or list(range(1, int(main_line * 2.5) + 2))
        rungs = sorted(set(base + [main_line]))
    ladder = []
    for t in rungs:
        if t == main_line:
            ladder.append((t, main_odds)); continue
        est = dk_implied_from_fair(dist.p_over(t))
        if DK_MIN_IMPLIED <= est <= DK_MAX_IMPLIED:
            ladder.append((float(t), prob_to_american(est)))
    return ladder, dist

# ---------- the algorithm ----------
@dataclass
class RungResult:
    threshold: float
    odds: Optional[int]
    p_model: float
    p_implied: Optional[float]
    ev_per_unit: Optional[float]
    breakeven: int

def evaluate(player: str, market: str, ladder: List[Tuple[float, Optional[int]]],
             projection: Optional[float] = None, min_prob: float = 0.55,
             min_ev: float = 0.03) -> dict:
    priced = [(t, o) for t, o in ladder if o is not None]
    if not priced:
        raise ValueError(f"{player} {market}: need odds on at least the main line")

    estimated = False
    if len(priced) < 3:
        # only the main line is priced -> rebuild DK's ladder from the learned hold curve
        main_t, main_o = priced[0]
        rungs = [t for t, _ in ladder] if len(ladder) > 1 else None
        ladder, market_dist = estimate_ladder(market, main_t, main_o, rungs)
        estimated = True
    else:
        market_dist = fit_market_dist(market, priced)
    model_dist  = market_dist.shifted(projection) if projection else market_dist

    rows: List[RungResult] = []
    for t, o in sorted(ladder, key=lambda x: x[0]):
        p = model_dist.p_over(t)
        if o is not None:
            pi = implied_prob(o)
            ev = p * payout_per_unit(o) - (1 - p)
        else:
            pi, ev = None, None
        rows.append(RungResult(t, o, p, pi, ev, breakeven_odds(p)))

    # best rung: highest EV among priced rungs meeting the probability floor
    candidates = [r for r in rows if r.ev_per_unit is not None and r.p_model >= min_prob]
    best = max(candidates, key=lambda r: r.ev_per_unit) if candidates else None
    if best and best.ev_per_unit < min_ev:
        best = None

    return {
        "player": player, "market": market,
        "market_median": market_dist.center, "market_spread": market_dist.spread,
        "projection": projection, "rows": rows, "best": best, "estimated": estimated,
    }


def print_report(res: dict):
    print(f"\n{res['player']}  [{res['market']}]")
    proj = res["projection"]
    print(f"  market median ≈ {res['market_median']:.1f}   "
          f"your projection = {proj if proj else 'none (using market)'}   "
          f"edge = {(proj - res['market_median']) if proj else 0:+.1f}")
    if res.get("estimated"):
        print("  (odds below main line are ESTIMATED from DK's ladder curve)")
    print(f"  {'rung':>6} {'odds':>6} {'model%':>7} {'impl%':>6} {'EV/u':>7} {'breakeven':>10}")
    for r in res["rows"]:
        odds = f"{r.odds:+d}" if r.odds is not None else "  --"
        impl = f"{r.p_implied*100:5.1f}" if r.p_implied is not None else "   --"
        ev   = f"{r.ev_per_unit:+.3f}" if r.ev_per_unit is not None else "     --"
        flag = "  <-- BET" if res["best"] and r.threshold == res["best"].threshold else ""
        print(f"  {r.threshold:>5g}+ {odds:>6} {r.p_model*100:6.1f}% {impl:>6} {ev:>7} {r.breakeven:>+10d}{flag}")
    if res["best"] is None:
        print("  no rung clears the EV/probability floor -> pass")


if __name__ == "__main__":
    # HOLD-OUT TEST: give the engine only JSN's main line, compare estimated ladder to DK's real odds
    real = {80: -127, 70: -193, 60: -310, 50: -532, 40: -1000}
    est, _ = estimate_ladder("rec_yds", 83, -114, rungs=[83, 80, 70, 60, 50, 40])
    print("JSN ladder from main line only  (rung: estimated vs real DK)")
    for t, o in est:
        if t in real: print(f"   {t:>3}+  est {o:>6}   real {real[int(t)]:>6}")
    real = {50: -119, 40: -195, 25: -483, 15: -1200}
    est, _ = estimate_ladder("rec_yds", 51, -114, rungs=[51, 50, 40, 25, 15])
    print("Evans ladder from main line only")
    for t, o in est:
        if t in real: print(f"   {t:>3}+  est {o:>6}   real {real[int(t)]:>6}")

    # Real use: main line only + your projection
    print_report(evaluate("Jaxon Smith-Njigba", "rec_yds", [(83, -114)], projection=92))
    print_report(evaluate("Drake Maye", "pass_cmps", [(18.5, -130)], projection=20.3))
    print_report(evaluate("Davante Adams", "receptions", [(5, -105)], projection=4.0))


# ---------- WIN MODE + PARLAY ----------
MAX_LEG_JUICE = -400   # never lay more than this on a single parlay leg

def pick_win_rung(res: dict, target_prob: float = 0.75,
                  floor7: Optional[float] = None) -> Optional[RungResult]:
    """Tim's rule, hardened:
       - model prob >= target_prob            (it WINS)
       - model prob >  implied prob           (you are not overpaying for it)
       - odds no worse than MAX_LEG_JUICE     (deep rungs stop adding value past ~-400)
       - if a Floor7 (min of last 7 games) is given, rung must be <= Floor7 (the streak holds)
       Among those, take the HIGHEST rung."""
    ok = [r for r in res["rows"]
          if r.odds is not None and r.p_model >= target_prob
          and r.p_implied is not None and r.p_model > r.p_implied
          and r.odds >= MAX_LEG_JUICE
          and (floor7 is None or r.threshold <= floor7)]
    return max(ok, key=lambda r: r.threshold) if ok else None

def disagreement_flag(res: dict, tol: float = 0.25) -> bool:
    """True when your projection is >tol away from the market median -> stale role / injury / REVIEW."""
    p, m = res.get("projection"), res.get("market_median")
    return bool(p and m and abs(p - m) / m > tol)

def parlay(legs: List[RungResult], correlation: float = 0.0) -> dict:
    """legs: chosen rungs. correlation: 0 = independent, 0.2 = mild same-game lift."""
    p = 1.0
    dec = 1.0
    for l in legs:
        p *= l.p_model
        dec *= 1 + payout_per_unit(l.odds)
    p_adj = min(0.99, p * (1 + correlation))          # crude: positive correlation lifts joint hit rate
    ev = p_adj * (dec - 1) - (1 - p_adj)
    return {"p_hit": p_adj, "decimal": dec, "american": prob_to_american(1 / dec),
            "ev_per_unit": ev, "breakeven_p": 1 / dec}

def parlay_report(name: str, legs: List[Tuple[str, RungResult]], correlation=0.0):
    print(f"\nPARLAY: {name}")
    for label, l in legs:
        print(f"   {label:<28} {l.threshold:g}+ {l.odds:+d}   model {l.p_model*100:.1f}%")
    r = parlay([l for _, l in legs], correlation)
    print(f"   -> pays {r['american']:+d} ({r['decimal']:.2f}x)   model hit {r['p_hit']*100:.1f}%   "
          f"breakeven {r['breakeven_p']*100:.1f}%   EV {r['ev_per_unit']:+.3f}/u")
