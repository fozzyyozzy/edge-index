"""Shared helpers for the pipeline."""
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
