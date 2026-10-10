"""Phase 1 data-quality checks over data/cfb/clean -> docs/cfb/PHASE1_REPORT.md.

    python -m engine.cfb.validate

Writes the generated section between the AUTO markers in the report (the
hand-written sections around it are preserved). Exit 1 if a hard check
(primary-key duplicates, spread sign convention) fails.
"""
from __future__ import annotations
import re
import sys
from datetime import datetime

import numpy as np
import pandas as pd

from engine.cfb import config
from engine.cfb.cfbd_client import calls_by_dataset, calls_used

BEGIN, END = "<!-- AUTO:BEGIN -->", "<!-- AUTO:END -->"
FULL_SEASONS = [s for s in config.SEASONS if s < config.CURRENT_SEASON]
MIN_PLAYS = 100


def load(name: str) -> pd.DataFrame:
    p = config.CLEAN / f"{name}.parquet"
    return pd.read_parquet(p) if p.exists() else pd.DataFrame()


def md(df: pd.DataFrame, floatfmt: str = "{:.1f}") -> str:
    if df.empty:
        return "_(none)_\n"
    df = df.copy()
    for c in df.columns:
        if df[c].dtype.kind == "f":
            df[c] = df[c].map(lambda v: "" if pd.isna(v) else floatfmt.format(v))
    cols = [str(c) for c in df.columns]
    out = ["| " + " | ".join(cols) + " |", "|" + "---|" * len(cols)]
    out += ["| " + " | ".join(str(v) for v in r) + " |" for r in df.itertuples(index=False)]
    return "\n".join(out) + "\n"


class Report:
    def __init__(self):
        self.parts: list[str] = []
        self.fails: list[str] = []
        self.warns: list[str] = []

    def h(self, t):
        self.parts.append(f"\n### {t}\n")

    def p(self, t):
        self.parts.append(t + "\n")

    def fail(self, t):
        self.fails.append(t)

    def warn(self, t):
        self.warns.append(t)


def main(argv=None) -> int:
    R = Report()
    games, plays, lines = load("games"), load("plays"), load("lines")
    gts, ts, bench, venues = (load("game_team_stats"), load("team_season"),
                              load("benchmarks"), load("venues"))
    if games.empty:
        print("no clean tables; run python -m engine.cfb.build_tables first")
        return 1
    done = games[games.completed == True]  # noqa: E712
    fbs_done = done[done.fbs_involved]
    # PBP is only pulled for weeks that are over (see pull.completed_weeks)
    wkey = ["season", "season_type", "week"]
    cutoff = pd.Timestamp.now(tz="UTC") - pd.Timedelta(hours=config.WEEK_DONE_HOURS)
    wk_over = (games.groupby(wkey).kickoff_utc.max() <= cutoff).rename("week_over")
    fbs_pbp = fbs_done.join(wk_over, on=wkey)
    in_progress = int((~fbs_pbp.week_over).sum())
    fbs_pbp = fbs_pbp[fbs_pbp.week_over]

    # 1. games per season
    R.h("1. Games per season")
    t = games.groupby("season").agg(
        total=("game_id", "size"), completed=("completed", "sum"),
        fbs_involved=("fbs_involved", "sum"), both_fbs=("both_fbs", "sum"),
        fbs_vs_fcs=("fbs_vs_fcs", "sum"), bowls=("is_bowl", "sum"),
        cfp=("is_cfp", "sum"), neutral=("neutral_site", "sum")).reset_index()
    R.p(md(t))
    for r in t.itertuples():
        # brief said ~750-900; FBS grew to 134-136 teams by 2023-25, so 950
        if r.season in FULL_SEASONS and not 750 <= r.fbs_involved <= 950:
            R.warn(f"{r.season}: {r.fbs_involved} FBS-involved games (expected 750-950)")

    # 2. PBP coverage + truncation
    R.h("2. Play-by-play coverage and truncation checks")
    ppg = plays.groupby("game_id").agg(n_plays=("play_id", "size"),
                                       max_period=("period", "max"),
                                       n_scrimmage=("is_scrimmage", "sum"))
    fd = fbs_pbp.join(ppg, on="game_id")
    R.p(f"Scope: completed FBS-involved games in weeks that are over "
        f"({in_progress} completed games in the in-progress week excluded; "
        f"update_week.py picks them up).\n")
    cov = fd.groupby("season").agg(
        completed_fbs_games=("game_id", "size"),
        with_plays=("n_plays", lambda s: s.notna().sum()),
        median_plays=("n_plays", "median"), p05_plays=("n_plays", lambda s: s.quantile(.05)),
        under_100=("n_plays", lambda s: (s < MIN_PLAYS).sum())).reset_index()
    cov["pct_with_plays"] = 100 * cov.with_plays / cov.completed_fbs_games
    R.p(md(cov))
    for r in cov.itertuples():
        if r.pct_with_plays < 98:
            R.warn(f"{r.season}: only {r.pct_with_plays:.1f}% of completed FBS games have PBP")
    short = fd[fd.n_plays < MIN_PLAYS][["game_id", "season", "week", "home_team",
                                         "away_team", "n_plays", "max_period"]]
    R.p(f"Games with < {MIN_PLAYS} plays: {len(short)}")
    if len(short):
        R.p(md(short.sort_values("n_plays").head(20)))
    missing = fd[fd.n_plays.isna() & fd.both_fbs][["game_id", "season", "week",
                                                    "season_type", "home_team", "away_team"]]
    R.p(f"Completed FBS-vs-FBS games with NO plays: {len(missing)}")
    if len(missing):
        R.p(md(missing.head(20)))

    # truncation: per (season, type, week) response, rows vs games covered,
    # suspicious round row counts, games cut off before the 4th quarter, and
    # scrimmage plays vs CFBD's own advanced-stats play counts.
    # A capped response would show a round row count, drop FBS games from the
    # end of the week, or cut many games off before Q4 in the same week.
    wk = plays.groupby(wkey).agg(rows=("play_id", "size"),
                                 games_in_response=("game_id", "nunique")).reset_index()
    fw = fd.groupby(wkey).agg(fbs_games=("game_id", "size"),
                              fbs_with_plays=("n_plays", lambda s: s.notna().sum()),
                              fbs_plays_per_game=("n_plays", "mean"),
                              fbs_before_q4=("max_period", lambda s: (s < 4).sum())
                              ).reset_index()
    wk = wk.merge(fw, on=wkey, how="left")
    wk["fbs_missing"] = wk.fbs_games - wk.fbs_with_plays
    wk["round_count"] = wk.rows.map(lambda n: n % 1000 == 0 or n in (2500, 5000, 7500))
    flag = wk[(wk.round_count) | (wk.fbs_missing > 0) | (wk.fbs_before_q4 > 1)
              | (wk.fbs_plays_per_game < 150)]
    R.p(f"Per-week /plays responses checked: {len(wk)}; row counts range "
        f"{wk.rows.min():,}-{wk.rows.max():,} (none round: "
        f"{not wk.round_count.any()}); FBS plays/game per week ranges "
        f"{wk.fbs_plays_per_game.min():.0f}-{wk.fbs_plays_per_game.max():.0f}. "
        f"Flagged weeks (round count, any FBS game missing, >1 FBS game ending "
        f"before Q4, or <150 FBS plays/game):")
    R.p(md(flag) if len(flag) else "_none_\n")
    if wk.round_count.any():
        R.fail("a /plays response has a round-number row count (possible cap)")
    if (wk.fbs_missing > 0).any():
        R.warn("a /plays week is missing FBS games (possible truncation)")
    cutq4 = fd[fd.max_period < 4][["game_id", "season", "week", "home_team",
                                    "away_team", "n_plays", "max_period"]]
    R.p(f"FBS-involved games whose PBP ends before Q4 (weather-shortened or "
        f"CFBD feed gap): {len(cutq4)}")
    if len(cutq4):
        R.p(md(cutq4))
    if len(gts) and "adv_offense_plays" in gts:
        ours = plays[plays.is_scrimmage].groupby(["game_id", "offense"]).size() \
            .rename("our_scrimmage")
        cmp_ = gts.dropna(subset=["adv_offense_plays"]).join(
            ours, on=["game_id", "team"], how="inner")
        ratio = cmp_.our_scrimmage / cmp_.adv_offense_plays
        R.p(f"Our scrimmage plays / CFBD advanced offense plays per team-game "
            f"(n={len(cmp_):,}): median {ratio.median():.3f}, "
            f"p05 {ratio.quantile(.05):.3f}, p95 {ratio.quantile(.95):.3f}. "
            f"Team-games below 0.8: {(ratio < .8).sum()}")
        if (ratio < .8).mean() > .01:
            R.warn(f"{(ratio < .8).mean():.1%} of team-games have <80% of CFBD's play count")

    if "is_duplicate" in plays:
        fbs_sc = plays[plays.game_id.isin(fd.game_id) & plays.is_scrimmage]
        dd = fbs_sc[fbs_sc.is_duplicate]
        R.p(f"Duplicate scrimmage plays in the CFBD feed (same game, clock, down, "
            f"distance, spot, text; new play_id), FBS-involved games: {len(dd):,} of "
            f"{len(fbs_sc):,} ({100 * len(dd) / max(len(fbs_sc), 1):.2f}%) in "
            f"{dd.game_id.nunique()} games. Kept, flagged `is_duplicate`.")

    # 3. PPA coverage
    R.h("3. PPA coverage (scrimmage plays)")
    sc = plays[plays.is_scrimmage]
    pc = sc.groupby("season").agg(scrimmage=("play_id", "size"),
                                  with_ppa=("ppa", lambda s: s.notna().sum())).reset_index()
    pc["pct_ppa"] = 100 * pc.with_ppa / pc.scrimmage
    R.p(md(pc))
    for r in pc.itertuples():
        if r.pct_ppa < 95:
            R.warn(f"{r.season}: PPA on only {r.pct_ppa:.1f}% of scrimmage plays")
    groups = plays.groupby(["play_type_group", "play_type"]).size().rename("n").reset_index()
    R.p("<details><summary>play_type -> play_type_group mapping</summary>\n\n"
        + md(groups.sort_values(["play_type_group", "n"], ascending=[True, False]))
        + "\n</details>")

    # 4. lines coverage
    R.h("4. Lines coverage (completed FBS-involved games)")
    ld = lines[lines.game_id.isin(fbs_done.game_id)]
    n_games = fbs_done.groupby("season").size().rename("games")
    has_close = ld.dropna(subset=["spread"]).groupby("season").game_id.nunique()
    has_open = ld.dropna(subset=["spread_open"]).groupby("season").game_id.nunique()
    lc = pd.concat([n_games, has_close.rename("close"), has_open.rename("open")],
                   axis=1).fillna(0).reset_index().rename(columns={"index": "season"})
    lc["pct_close"] = 100 * lc.close / lc.games
    lc["pct_open"] = 100 * lc.open / lc.games
    R.p(md(lc[["season", "games", "pct_close", "pct_open"]]))
    R.p("**Season x provider: % of completed FBS-involved games with a close / open spread**\n")
    pv = ld.groupby(["season", "provider"]).agg(
        close=("spread", lambda s: s.notna().sum()),
        open=("spread_open", lambda s: s.notna().sum())).reset_index()
    pv = pv.join(n_games, on="season")
    pv["cell"] = pv.apply(lambda r: f"{100 * r.close / r.games:.0f} / "
                                    f"{100 * r.open / r.games:.0f}", axis=1)
    grid = pv.pivot(index="provider", columns="season", values="cell").fillna("-")
    order = pv.groupby("provider").close.sum().sort_values(ascending=False).index
    R.p(md(grid.loc[order].reset_index()))
    dk = pv[pv.provider == "DraftKings"].set_index("season")
    for s in config.SEASONS:
        if s not in dk.index:
            R.warn(f"DraftKings absent in {s}")

    # sign convention: parse formatted_spread "Team -X" vs home-perspective spread
    def sign_ok(r):
        m = re.match(r"^(.*?)\s+([-+]?\d+(?:\.\d+)?)$", str(r.formatted_spread or ""))
        if not m or pd.isna(r.spread):
            return np.nan
        team, num = m.group(1).strip(), float(m.group(2))
        if team == r.home_team:
            return float(np.isclose(r.spread, num))
        if team == r.away_team:
            return float(np.isclose(r.spread, -num))
        return np.nan
    chk = lines.apply(sign_ok, axis=1)
    n_chk, n_bad = chk.notna().sum(), (chk == 0).sum()
    R.p(f"Sign convention (spread is home-perspective, negative = home favored): "
        f"{n_chk:,} rows parseable from formatted_spread, {n_bad} disagree.")
    if n_chk and n_bad / n_chk > 0.005:
        R.fail(f"spread sign convention: {n_bad}/{n_chk} rows disagree with formatted_spread")
    fav = done.dropna(subset=["consensus_close_spread"]).sort_values("consensus_close_spread")
    if len(fav):
        r = fav.iloc[0]
        R.p(f"Example: {r.season} wk{r.week} {r.away_team} @ {r.home_team}: consensus "
            f"{r.consensus_close_spread:+.1f} (home favored), final "
            f"{r.home_points}-{r.away_points}.")

    # 5. final score vs PBP
    R.h("5. Final scores vs PBP (random 25 completed games)")
    def score_check(gdf):
        sp_ = plays[plays.game_id.isin(gdf.game_id)][
            ["game_id", "offense", "offense_score", "defense_score"]]
        home = gdf.set_index("game_id").home_team
        is_home = sp_.offense.values == home.reindex(sp_.game_id).values
        sp_ = sp_.assign(home_score=np.where(is_home, sp_.offense_score, sp_.defense_score),
                         away_score=np.where(is_home, sp_.defense_score, sp_.offense_score))
        pbp = sp_.groupby("game_id")[["home_score", "away_score"]].max()
        m = gdf.set_index("game_id")[["season", "home_team", "away_team",
                                      "home_points", "away_points"]].join(pbp)
        m["match"] = (m.home_points == m.home_score) & (m.away_points == m.away_score)
        return m
    with_pbp = fd.dropna(subset=["n_plays"])
    m = score_check(with_pbp.sample(min(25, len(with_pbp)), random_state=7))
    R.p(f"Matches: {m.match.sum()}/{len(m)}. PBP score = highest running score in the "
        f"plays (CFBD play scores are post-play).")
    if (~m.match).any():
        R.p(md(m[~m.match].reset_index()))
        R.warn(f"{(~m.match).sum()}/{len(m)} sampled games: PBP score != final")
    full = score_check(with_pbp)
    R.p(f"All completed FBS-involved games with PBP: {(~full.match).sum()} of {len(full)} "
        f"({100 * (~full.match).mean():.1f}%) disagree with the final score.")

    # 6. spread sanity
    R.h("6. Spread sanity (completed FBS-vs-FBS, consensus close)")
    def ats(df, col):
        d = df.dropna(subset=[col, "margin_home"])
        d = d[d[col] != 0]
        res = d.margin_home + d[col]          # >0 home covers
        fav_home = d[col] < 0
        fav_cov = np.where(fav_home, res > 0, res < 0)
        push = res == 0
        return pd.Series({"games": len(d),
                          "fav_cover_pct": 100 * fav_cov[~push].mean() if len(d) else np.nan,
                          "avg_ats_miss": res.abs().mean()})
    bf = done[done.both_fbs]
    s6 = bf.groupby("season").apply(lambda d: ats(d, "consensus_close_spread")).reset_index()
    R.p(md(s6))
    dkl = lines[lines.provider == "DraftKings"][["game_id", "spread"]].rename(
        columns={"spread": "dk_spread"})
    s6dk = bf.merge(dkl, on="game_id").groupby("season").apply(
        lambda d: ats(d, "dk_spread")).reset_index()
    R.p("DraftKings close only:\n\n" + md(s6dk))
    for r in s6.itertuples():
        if r.games and not (45 <= r.fav_cover_pct <= 55 and 10 <= r.avg_ats_miss <= 14):
            R.warn(f"{r.season}: spread sanity off (fav cover {r.fav_cover_pct:.1f}%, "
                   f"miss {r.avg_ats_miss:.1f})")

    # 7. duplicates + join integrity
    R.h("7. Primary keys and joins")
    keys = {"games": (games, ["game_id"]), "lines": (lines, ["game_id", "provider"]),
            "plays": (plays, ["play_id"]), "game_team_stats": (gts, ["game_id", "team"]),
            "team_season": (ts, ["season", "team_id"]),
            "benchmarks": (bench, ["season", "team"]), "venues": (venues, ["venue_id"])}
    rows = []
    for name, (df, k) in keys.items():
        d = int(df.duplicated(k).sum()) if len(df) else 0
        rows.append({"table": name, "rows": len(df), "key": "+".join(k), "duplicates": d})
        if d:
            R.fail(f"{name}: {d} duplicate keys on {k}")
    R.p(md(pd.DataFrame(rows)))
    joins = {
        "plays.offense_id null": int(plays.offense_id.isna().sum()),
        "plays.defense_id null": int(plays.defense_id.isna().sum()),
        "benchmarks.team_id null (name not in games)": int(bench.team_id.isna().sum()),
        "team_season talent null": int(ts.talent.isna().sum()),
        "team_season recruiting null": int(ts.recruiting_rank.isna().sum()),
        "team_season returning null": int(ts.ret_pct_ppa.isna().sum()),
        "team_season coach null": int(ts.coach_id.isna().sum()) if "coach_id" in ts else "n/a",
        "games kickoff_local_hour null (tz unknown or TBD)":
            int(games.kickoff_local_hour.isna().sum()),
        "lines game_id not in games": int((~lines.game_id.isin(games.game_id)).sum()),
    }
    R.p(md(pd.DataFrame({"check": list(joins), "count": list(joins.values())})))
    unmatched = bench[bench.team_id.isna()][["season", "team"]]
    if len(unmatched):
        R.p("Benchmark names not matched to a team_id: "
            + ", ".join(sorted(set(unmatched.team)))[:600])

    # 8. API calls
    R.h("8. API calls (ledger)")
    by = calls_by_dataset()
    R.p(md(pd.DataFrame({"dataset": list(by), "calls": list(by.values())})))
    R.p(f"Total: {calls_used()} / cap {config.CALL_CAP}")

    head = [f"_Generated by `python -m engine.cfb.validate` at "
            f"{datetime.now():%Y-%m-%d %H:%M}._\n",
            "**Hard-check failures:** " + ("; ".join(R.fails) if R.fails else "none") + "  ",
            "**Warnings:** " + ("" if R.warns else "none")]
    head += [f"- {w}" for w in R.warns]
    auto = "\n".join(head) + "\n" + "".join(R.parts)

    config.REPORT.parent.mkdir(parents=True, exist_ok=True)
    text = config.REPORT.read_text(encoding="utf-8") if config.REPORT.exists() else ""
    block = f"{BEGIN}\n{auto}\n{END}"
    if BEGIN in text and END in text:
        text = text[:text.index(BEGIN)] + block + text[text.index(END) + len(END):]
    else:
        text = (text or "# CFB Phase 1 Report\n\n## Validation results\n\n") + block + "\n"
    config.REPORT.write_text(text, encoding="utf-8")

    print(f"fails: {R.fails or 'none'}")
    for w in R.warns:
        print("warn:", w)
    print(f"report -> {config.REPORT.relative_to(config.ROOT)}")
    return 1 if R.fails else 0


if __name__ == "__main__":
    sys.exit(main())
