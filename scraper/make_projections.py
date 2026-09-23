"""
make_projections.py  (nflverse edition)
=======================================
Pulls REAL weekly player stats from nflverse (free, public) and builds projections.

  python make_projections.py            -> downloads 2024+2025, writes projections.csv
  python make_projections.py --games 12 -> last 12 games instead of 10

Output columns:
  Player, Market, Projection, Floor7, L10_median, L10_mean, Games, Team2025, Matchup_Adj, Final
  Projection : median of last N regular-season games, most recent 5 double-counted
  Floor7     : lowest result in the last 7  (your streak floor)
  Team2025   : team in last 2025 game -- if it differs from the DK game, the role changed. Check it.
  Matchup_Adj: YOU edit (1.10 soft D, 0.90 tough D). Final = Projection * Matchup_Adj
"""
import io
import re
import sys
import urllib.request
import numpy as np
import pandas as pd

SEASONS = [2024, 2025]
N_GAMES = 10
URL = "https://github.com/nflverse/nflverse-data/releases/download/stats_player/stats_player_week_{yr}.csv"
STAT_MAP = {   # engine market -> nflverse column
    "rec_yds": "receiving_yards", "receptions": "receptions", "pass_yds": "passing_yards",
    "rush_yds": "rushing_yards", "pass_cmps": "completions", "pass_att": "attempts", "rush_att": "carries",
}
INVOLVED = {"rec_yds": "targets", "receptions": "targets", "pass_yds": "attempts", "pass_cmps": "attempts",
            "pass_att": "attempts", "rush_yds": "carries", "rush_att": "carries"}

def fetch(yr: int) -> pd.DataFrame:
    req = urllib.request.Request(URL.format(yr=yr), headers={"User-Agent": "Mozilla/5.0"})
    raw = urllib.request.urlopen(req, timeout=120).read()
    df = pd.read_csv(io.BytesIO(raw), low_memory=False)
    df = df[df["season_type"] == "REG"]
    keep = ["player_display_name", "season", "week", "team", "targets"] + list(STAT_MAP.values())
    return df[[c for c in keep if c in df.columns]]

def main():
    n = N_GAMES
    if "--games" in sys.argv:
        n = int(sys.argv[sys.argv.index("--games") + 1])
    frames = []
    for yr in SEASONS:
        print(f"downloading {yr} ...", end=" ", flush=True)
        f = fetch(yr); frames.append(f); print(f"{len(f)} rows")
    d = pd.concat(frames).sort_values(["player_display_name", "season", "week"])

    rows = []
    for player, grp in d.groupby("player_display_name"):
        team25 = grp[grp.season == 2025]["team"].iloc[-1] if (grp.season == 2025).any() else ""
        for market, col in STAT_MAP.items():
            inv = INVOLVED[market]
            g = grp[grp[inv].fillna(0) > 0] if inv in grp else grp   # games he was actually used
            v = g[col].fillna(0).to_numpy(dtype=float)
            if len(v) < 4 or np.mean(v[-n:]) < 1:
                continue
            last = v[-n:]
            proj = float(np.median(np.concatenate([last, last[-5:]])))
            rows.append({"Player": player, "Market": market, "Projection": round(proj, 1),
                         "Floor7": float(np.min(v[-7:])), "L10_median": float(np.median(last)),
                         "L10_mean": round(float(np.mean(last)), 1), "Games": int(len(v)),
                         "Team2025": team25, "Matchup_Adj": 1.00, "Final": round(proj, 1)})
    out = pd.DataFrame(rows).sort_values(["Market", "Projection"], ascending=[True, False])
    out.to_csv("projections.csv", index=False)
    print(f"wrote projections.csv ({len(out)} rows)")
    print(out.groupby("Market").size().to_string())

if __name__ == "__main__":
    main()
