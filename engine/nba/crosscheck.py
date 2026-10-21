"""ESPN backfill vs nba_api (stats.nba.com) cross-check: a one-time local check, not a data source.

    python -m engine.nba.crosscheck      # needs data/nba/raw/nba_api/leaguegamelog_P_<season>.parquet (pulled locally)

Joins every played ESPN player-game to nba_api on (NBA.com id via the crosswalk, game date) and reports exact
agreement for minutes, pts, reb, ast, fg3m, stl, blk, plus rows only one source has. Writes data/nba/crosscheck_summary.json
and data/nba/crosscheck_mismatches.csv.
"""
from __future__ import annotations
import json

import pandas as pd

from engine.nba.crosswalk import DATA, ROOT

STATS = {"minutes": "MIN", "pts": "PTS", "reb": "REB", "ast": "AST", "fg3m": "FG3M", "stl": "STL", "blk": "BLK"}


def main():
    pg = pd.read_parquet(DATA / "player_games.parquet")
    cw = pd.read_csv(DATA / "player_crosswalk.csv", dtype={"espn_id": str})
    nba = pd.concat([pd.read_parquet(p) for p in sorted((DATA / "raw" / "nba_api").glob("leaguegamelog_P_*.parquet"))])
    nba["date"] = pd.to_datetime(nba.GAME_DATE).dt.strftime("%Y-%m-%d")
    e = pg[pg.played].merge(cw[["espn_id", "nba_id"]], on="espn_id", how="left")
    e["nba_id"] = e.nba_id.astype("Int64")
    nba["nba_id"] = nba.PLAYER_ID.astype("Int64")
    m = e.merge(nba, on=["nba_id", "date"], how="outer", indicator=True)
    both = m[m._merge == "both"]
    summary = {"espn_played_rows": int(len(e)), "nba_api_rows": int(len(nba)), "matched_rows": int(len(both)),
               "espn_only": int((m._merge == "left_only").sum()), "nba_api_only": int((m._merge == "right_only").sum()),
               "espn_rows_without_nba_id": int(e.nba_id.isna().sum()),
               "team_mismatch": int((both.team != both.TEAM_ABBREVIATION).sum()), "by_stat": {}, "by_season": {}}
    bad = []
    for ours, theirs in STATS.items():
        d = both[ours] - both[theirs]
        summary["by_stat"][ours] = {"exact": round(float((d == 0).mean()), 5), "within_1": round(float((d.abs() <= 1).mean()), 5),
                                    "mismatches": int((d != 0).sum()), "mean_diff": round(float(d.mean()), 4)}
        bad.append(both.loc[d != 0, ["season", "date", "game_id", "team", "player", "nba_id", ours, theirs]]
                   .assign(stat=ours).rename(columns={ours: "espn", theirs: "nba_api"}))
    for s, g in both.groupby("season"):
        summary["by_season"][s] = {k: round(float((g[k] == g[v]).mean()), 5) for k, v in STATS.items()}
    only_e = m[m._merge == "left_only"]
    only_n = m[m._merge == "right_only"]
    summary["espn_only_examples"] = only_e[["date", "team", "player", "minutes", "pts"]].head(10).to_dict("records")
    summary["nba_api_only_examples"] = only_n[["date", "TEAM_ABBREVIATION", "PLAYER_NAME", "MIN", "PTS"]].head(10).to_dict("records")
    summary["nba_api_only_min_dist"] = only_n.MIN.describe().round(2).to_dict()
    mism = pd.concat(bad)
    mism.to_csv(DATA / "crosscheck_mismatches.csv", index=False)
    (DATA / "crosscheck_summary.json").write_text(json.dumps(summary, indent=2, default=str))
    print(json.dumps(summary, indent=2, default=str))
    print(f"mismatch rows -> {(DATA / 'crosscheck_mismatches.csv').relative_to(ROOT)}")


if __name__ == "__main__":
    main()
