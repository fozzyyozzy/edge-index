"""Shared helpers for the pipeline."""
import os
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))   # the automation/ folder
def P(*parts):
    """path under automation/, created if needed"""
    p = os.path.join(ROOT, *parts); os.makedirs(os.path.dirname(p) if os.path.splitext(p)[1] else p, exist_ok=True); return p
import io, re, urllib.request
import pandas as pd

COL = {"rec_yds": "receiving_yards", "receptions": "receptions", "pass_yds": "passing_yards", "rush_yds": "rushing_yards",
       "pass_cmps": "completions", "pass_att": "attempts", "rush_att": "carries"}
_SUFFIX = re.compile(r"\s+(jr\.?|sr\.?|ii|iii|iv)$", re.I)
_ALIAS = {"cameron ward": "cam ward", "d.j. moore": "dj moore"}

def norm_name(s):
    s = _SUFFIX.sub("", str(s).strip()).lower()
    return _ALIAS.get(s, s)

def fetch_season(yr):
    url = f"https://github.com/nflverse/nflverse-data/releases/download/stats_player/stats_player_week_{yr}.csv"
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    w = pd.read_csv(io.BytesIO(urllib.request.urlopen(req, timeout=120).read()), low_memory=False)
    w = w[(w.season_type == "REG") & w.player_display_name.notna()].copy()
    w["key"] = w.player_display_name.map(norm_name)
    return w

def fetch_week(yr, wk):
    w = fetch_season(yr)
    return w[w.week == wk]

def pay(o): return 100 / -o if o < 0 else o / 100


def load_real_ladders(path):
    """ladders CSV -> {(norm_name, market): [(rung, odds), ...]} or {} if missing."""
    import os
    if not path or not os.path.exists(path): return {}
    df = pd.read_csv(path); out = {}
    for r in df.itertuples():
        out.setdefault((norm_name(r.Player), r.Market), []).append((float(r.Rung), int(r.Odds)))
    return {k: sorted(v) for k, v in out.items()}


def prices_pulled(season, week, slate):
    """When this slate's prices were pulled (UTC ISO, minutes). fetch_lines.py records it in lines/pulled_<season>_w<week>_<slate>.txt;
    without that file, fall back to the ladders/main-line CSV mtime (only right in the job that fetched them —
    a git checkout or pull resets mtimes)."""
    from datetime import datetime, timezone
    for rec in (P("lines", f"pulled_{season}_w{week}_{slate}.txt"), P("lines", f"pulled_{season}_w{week}.txt")):
        if os.path.exists(rec):                  # per-slate file first: a later pull for another slate moves the week file
            return open(rec).read().strip()
    for f in (P("lines", f"ladders_{season}_w{week}.csv"), P("lines", f"dk_{season}_w{week}_{slate}.csv")):
        if os.path.exists(f):
            return datetime.fromtimestamp(os.path.getmtime(f), timezone.utc).isoformat(timespec="minutes")
    return None


def tag_rank(series, team, defense=False):
    """Matchup tag + rank of 32. SOFT = the 8 most yards allowed (defense) / most attempts (own volume), TOUGH = the 8 fewest,
    neutral = the middle 16 ("AVG" on the site).
    Rank, defense: 1 = fewest yards allowed (toughest) ... 32 = most — the Matchups tab's convention.
    Rank, volume:  1 = most attempts."""
    r = series.rank(ascending=False); x = r.get(team)
    if x is None or pd.isna(x): return "?", None
    x = int(round(x)); tag = "SOFT" if x <= 8 else "TOUGH" if x >= 25 else "neutral"
    return tag, (len(series) + 1 - x) if defense else x


# ── per-leg probability: shrunk clear rate, blended toward DK's no-vig price ───────────────────────────────────────
# Start from the add-one clear rate (hits+1)/(games+2) over L10 and over L15 and take the lower window; then blend toward
# DK's no-vig implied probability, counting the market as MARKET_GAMES extra games; cap at PROB_CAP. One implementation,
# used by floors.py, grade_legs.py and build_card_json.py (the site's slip uses the rung's `prob` from grade_legs).
MARKET_GAMES = 10
PROB_CAP = 0.90
# DK alt ladders come one-sided (Over only), so no-vig uses the hold DK charges on the same player's standard two-way
# market (lines/twoway_<season>_w<week>.csv from fetch_lines.py): p_novig = p_implied / (1 + hold). Missing that
# player/market: the slate's median hold for the market; no two-way data at all: an assumed DEFAULT_HOLD.
# Main-line hold is a floor for alt rungs, which often carry more — so this errs toward crediting the market too little.
DEFAULT_HOLD = 0.045

def implied(o):
    return -o / (-o + 100) if o < 0 else 100 / (o + 100)

def fair_american(p):
    """probability -> fair American odds, no vig"""
    p = min(max(p, 0.01), 0.99)
    return int(round(-100 * p / (1 - p))) if p >= 0.5 else int(round(100 * (1 - p) / p))

def load_holds(season, week):
    """{(norm_name, market): hold} from the week's two-way file, plus {("*", market): median hold}; {} if none."""
    path = P("lines", f"twoway_{season}_w{week}.csv")
    if not os.path.exists(path): return {}
    tw = pd.read_csv(path).dropna(subset=["Over", "Under"])
    tw["hold"] = [implied(o) + implied(u) - 1 for o, u in zip(tw.Over, tw.Under)]
    tw = tw[(tw.hold > -0.01) & (tw.hold < 0.25)]                        # drop garbage quotes
    out = {(norm_name(r.Player), r.Market): float(r.hold) for r in tw.itertuples()}
    out.update({("*", m): float(g.hold.median()) for m, g in tw.groupby("Market")})
    return out

def novig(odds, name, market, holds):
    """(no-vig probability, source) for a one-sided DK price."""
    key = (norm_name(name), market)
    if key in holds: h, src = holds[key], "two-way"
    elif ("*", market) in holds: h, src = holds[("*", market)], "market median"
    else: h, src = DEFAULT_HOLD, "assumed"
    return implied(odds) / (1 + h), src

def leg_prob(values, rung, p_market=None):
    """values = the player's game log (oldest first). Returns the blended, capped probability of clearing `rung`."""
    import numpy as np
    v = np.asarray(values, dtype=float)
    wins = []
    for n in (10, 15):
        w = v[-n:]; h = int((w >= rung).sum()); g = len(w)
        wins.append(((h + 1) / (g + 2), h, g))
    _, h, g = min(wins)                                                  # the lower (more cautious) window
    p = (h + 1 + MARKET_GAMES * p_market) / (g + 2 + MARKET_GAMES) if p_market is not None else (h + 1) / (g + 2)
    return min(p, PROB_CAP)

def price_fields(values, rung, odds, name, market, holds):
    """prob, fair price and edge for one rung at DK's price; edge = our probability minus DK's implied (vig included)."""
    p_mkt, src = novig(odds, name, market, holds)
    p = leg_prob(values, rung, p_mkt)
    return dict(prob=round(p, 4), novig_pct=round(100 * p_mkt, 1), novig_source=src, fair_odds=fair_american(p),
                edge_pts=round(100 * (p - implied(odds)), 1))
