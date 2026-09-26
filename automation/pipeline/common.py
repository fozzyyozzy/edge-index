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
