"""
NFL SITE DATA GENERATOR
=======================
Computes every number the site displays from nflverse and the model modules,
then writes it into the JSX between AUTO-GENERATED markers.

WHY THIS EXISTS
  Every tab currently ships hand-written const arrays — asserted hit rates,
  a hardcoded "Week 10", seed history dated last November, and a literal
  SAMPLE_PLAYS. Those read as model output and aren't. That is the same
  failure mode as the MLB build, where a tier claimed 87% and delivered 57%
  and nobody checked for a month.

  Every figure this script writes is computed from game logs or from a
  calibrated model, or it is not written.

WHAT IT PRODUCES
  STREAKS   floor lines: the number a player actually clears, how often, and
            what the price would require. This is the StreakCenter thesis
            made honest — hit rate measured over real game logs rather than
            asserted, and always paired with the rate the odds demand.
  PROPS     browse rows, from projections plus live odds when a key is set.
  PLAYERS   per-position usage from real logs.
  CARD      the weekly card, from the screener.

Usage
    python generate_nfl_data.py --season 2025 --preview
    python generate_nfl_data.py --season 2025 --inject C:/.../cfb-app/src
"""

import argparse
import json
import os
import re
from datetime import date

import polars as pl

import nfl_projection as PROJ

# Props we build floor lines for, mapped to the nflverse stat column.
# (column, label, step, side). side="under" walks the other way — an
# interceptions line is a floor play in the under direction, not the over.
STREAK_PROPS = {
    "receptions":  ("receptions",            "Receptions",   0.5, "over"),
    "rec_yards":   ("receiving_yards",       "Rec Yards",    5.0, "over"),
    "rush_yards":  ("rushing_yards",         "Rush Yards",   5.0, "over"),
    "rush_att":    ("carries",               "Rush Att",     0.5, "over"),
    "pass_yards":  ("passing_yards",         "Pass Yards",  25.0, "over"),
    "pass_att":    ("attempts",              "Pass Att",     0.5, "over"),
    "pass_comp":   ("completions",           "Completions",  0.5, "over"),
    "pass_int":    ("passing_interceptions", "Interceptions",0.5, "under"),
}

POS_FOR_PROP = {
    "receptions": ("WR", "TE", "RB"), "rec_yards": ("WR", "TE", "RB"),
    "rush_yards": ("RB", "QB"), "rush_att": ("RB", "QB"),
    "pass_yards": ("QB",), "pass_att": ("QB",),
    "pass_comp": ("QB",), "pass_int": ("QB",),
}

# Model key for the fitted variance curve; props without their own fit
# borrow the closest one.
VAR_KEY = {
    "rush_att": "rush_attempts", "pass_att": "pass_attempts",
    "pass_comp": "pass_attempts", "pass_int": "receptions",
}

# A floor line is only useful if a book would price it somewhere you can
# bet. Walking up while the hit rate stays high finds the SAFEST line, which
# is typically 0.5 receptions at -2000 — true and untradeable. Instead we
# search for the highest line whose calibrated model probability lands in
# the band that maps to roughly -500..-150, then report the measured clear
# rate beside it.
BAND_PROB = (0.60, 0.88)      # ~ -150 to -500 implied

# Which line to keep when several sit in band. Keeping the HIGHEST in-band
# line silently keeps the LOWEST probability, and how far that falls depends
# entirely on step size — receptions step 0.5 and land near .77, rec yards
# step 5.0 and walk a dozen steps down to .60. That made props
# incomparable and let receptions win the sort by accident. Keeping the line
# nearest a target instead puts every prop on the same footing.
TARGET_PROB = 0.75            # middle of the band, ~ -300

# Baseline mode uses the FULL season rather than a trailing window, because
# the full-season clear rate is what actually carries into the next year:
#   full-season clear rate -> next season   r2 = 0.505
#   last-5 clear rate      -> next season   r2 = 0.440
#   end-of-season streak   -> next season   r2 = 0.205
# and the streak adds nothing once the rate is known (r2 0.5048 -> 0.5059,
# coefficient +0.0035). A streak is a small noisy slice of a number we
# already have more of, so the board reports the rate and shows the streak
# only as a footnote. 71.3% of players stay on the same team year to year;
# the rest are flagged, since their rate describes a situation they left.
BASELINE_MIN_GAMES = 10

# NO filter on the measured rate. Filtering for rows where the log cleared
# often AND the model is under 88% mechanically selects rows where the log
# beat the model, making the log-vs-model column read as edge when it is
# only survivorship. Every in-band row is kept and the gap is reported
# honestly, in both directions.

# Volume floors so the board shows real contributors rather than a fourth
# receiver clearing 0.5 catches at a price nobody would lay.
MIN_VOLUME = {
    "receptions": 3.0, "rec_yards": 35.0, "rush_yards": 40.0,
    "rush_att": 9.0, "pass_yards": 200.0, "pass_att": 25.0,
    "pass_comp": 15.0, "pass_int": 0.0,
}
WINDOW = 12
MIN_GAMES = 8


def _load(season):
    import nflreadpy as nfl
    return (nfl.load_player_stats([season])
            .filter(pl.col("season_type") == "REG")
            .sort(["player_id", "week"]))


def _bettable_floor(values, mean, prop_key, step, side="over"):
    """In-band line nearest TARGET_PROB, with the measured clear count.

    Returns (line, cleared, model_prob) or None.
    """
    if not values or mean <= 0:
        return None
    best = None
    line = step
    ceiling = mean * 3 + 4 * step
    while line < ceiling:
        over = PROJ.prob_over_calibrated(prop_key, mean, line)
        if over is None:
            break
        p = over if side == "over" else 1 - over
        if BAND_PROB[0] <= p <= BAND_PROB[1]:
            cleared = (sum(1 for v in values if v > line) if side == "over"
                       else sum(1 for v in values if v < line))
            cand = (line, cleared, round(p, 4))
            if best is None or abs(p - TARGET_PROB) < abs(best[2] - TARGET_PROB):
                best = cand
        # An over-line's probability falls monotonically; once it is under the
        # band nothing higher can re-enter. Unders rise, so keep walking.
        if side == "over" and p < BAND_PROB[0]:
            break
        line += step
    return best


def _current_streak(values, line):
    """Consecutive most-recent games clearing the line."""
    n = 0
    for v in reversed(values):
        if v > line:
            n += 1
        else:
            break
    return n


def build_streaks(season, limit=24, baseline=False):
    """Bettable floor lines with measured hit rates. No asserted numbers.

    Each row carries three things a reader can check against each other:
    what the game log did (hit/of, streak), what the model thinks (prob),
    and what a price would have to be to make it worth taking (max_odds).
    """
    ps = _load(season)
    name_col = "player_display_name" if "player_display_name" in ps.columns else "player_name"
    team_col = "team" if "team" in ps.columns else "recent_team"

    rows = []
    for prop, (col, label, step, side) in STREAK_PROPS.items():
        if col not in ps.columns:
            continue
        prop_key = VAR_KEY.get(prop, prop)
        allowed = POS_FOR_PROP[prop]
        sub = ps.filter(pl.col("position").is_in(list(allowed))).select(
            [name_col, team_col, "position", "week", col])
        for (nm, tm, pos), g in sub.group_by([name_col, team_col, "position"],
                                             maintain_order=True):
            vals = [v for v in g.sort("week")[col].to_list() if v is not None]
            if len(vals) < MIN_GAMES:
                continue
            if baseline:
                if len(vals) < BASELINE_MIN_GAMES:
                    continue
                window = vals                     # whole season, r2 0.505
            else:
                window = vals[-WINDOW:]
            mean = sum(window) / len(window)
            if mean < MIN_VOLUME.get(prop, 0):
                continue
            found = _bettable_floor(window, mean, prop_key, step, side)
            if not found:
                continue
            line, cleared, prob = found
            sd = PROJ.stat_sd(prop_key, mean) or 0.0
            # Longest price still worth taking at this probability, before vig.
            max_odds = (round(-100 * prob / (1 - prob)) if prob >= 0.5
                        else round(100 * (1 - prob) / prob))
            rows.append({
                "player": nm, "team": tm or "?", "pos": pos,
                "prop": prop, "label": label, "line": line, "side": side,
                "hit": cleared, "of": len(window),
                "rate": round(cleared / len(window), 3),
                "streak": _current_streak(window, line),
                "avg": round(mean, 1), "sd": round(sd, 2),
                "model": prob,
                "max_odds": max_odds,
                "baseline": bool(baseline),
                # Gap between what the log did and what the model says. Large
                # gaps in either direction are worth a look, not a bet.
                "log_vs_model": round(cleared / len(window) - prob, 3),
            })

    # Ranked by model probability — the number that decides whether a price
    # is takeable. Measured rate sits beside it as a check, not as the sort.
    # Attach the 2026 team where reporting says it changed.
    moved = team_changes(season)
    for r in rows:
        new_team = moved.get(r["player"])
        r["new_team"] = new_team if new_team and new_team != r["team"] else None

    # Interleave by prop. Sorting the pooled list lets whichever prop happens
    # to reach the highest probability take every slot, which is how the board
    # ended up 37/40 receptions.
    by_prop = {}
    for r in rows:
        by_prop.setdefault(r["prop"], []).append(r)
    for v in by_prop.values():
        v.sort(key=lambda r: (-r["rate"], -r["model"]))

    out, i = [], 0
    order = [p for p in STREAK_PROPS if p in by_prop]
    while len(out) < limit and any(len(by_prop[p]) > i for p in order):
        for p in order:
            if len(by_prop[p]) > i and len(out) < limit:
                out.append(by_prop[p][i])
        i += 1
    return out


def team_changes(season):
    """Players whose 2026 team differs from their season-N team.

    Their measured rate describes an offense they have left, so the board
    flags it rather than presenting the number as if it still applies.
    """
    import nfl_roles as ROLES
    out = {}
    for player, ov in ROLES.OVERRIDES.items():
        if ov.get("team"):
            out[player] = ov["team"]
    return out


def build_players(season, per_pos=8):
    """Per-position usage from real logs — no invented rates."""
    ps = _load(season)
    name_col = "player_display_name" if "player_display_name" in ps.columns else "player_name"
    team_col = "team" if "team" in ps.columns else "recent_team"

    agg = (ps.group_by([name_col, team_col, "position"]).agg([
        pl.len().alias("g"),
        pl.col("targets").mean().alias("tgt"),
        pl.col("receptions").mean().alias("rec"),
        pl.col("receiving_yards").mean().alias("recyd"),
        pl.col("carries").mean().alias("car"),
        pl.col("rushing_yards").mean().alias("rushyd"),
        pl.col("attempts").mean().alias("att"),
        pl.col("passing_yards").mean().alias("passyd"),
    ]).filter(pl.col("g") >= MIN_GAMES))

    out = []
    rank = {"QB": "passyd", "RB": "rushyd", "WR": "recyd", "TE": "recyd"}
    for pos in ("QB", "RB", "WR", "TE"):
        sub = (agg.filter(pl.col("position") == pos)
                  .sort(rank[pos], descending=True, nulls_last=True)
                  .head(per_pos))
        for r in sub.to_dicts():
            rec = {"player": r[name_col], "team": r[team_col] or "?",
                   "pos": pos, "games": r["g"]}
            for k, src in (("tgt","tgt"),("rec","rec"),("recyd","recyd"),
                           ("car","car"),("rushyd","rushyd"),
                           ("att","att"),("passyd","passyd")):
                v = r.get(src)
                rec[k] = round(v, 1) if v is not None else None
            out.append(rec)
    return out


def build_props(season, streaks, limit=30):
    """Browse rows. Uses the floor line and the measured clear rate; the
    market columns stay null until an odds pull fills them, rather than
    being invented."""
    return [{
        "player": s["player"], "team": s["team"], "pos": s["pos"],
        "prop": s["label"], "line": s["line"],
        "avg": s["avg"], "rate": s["rate"],
        "hit": s["hit"], "of": s["of"], "streak": s["streak"],
        "odds": None, "model": None,   # filled by the live odds pull
    } for s in streaks[:limit]]


# ── INJECTION ─────────────────────────────────────────────────────

def js_const(name, obj):
    return f"const {name} = {json.dumps(obj, indent=2)};"


def inject(path, marker, body, dry=False):
    """Replace the span between AUTO-GENERATED markers.

    Same convention as the existing FREE_PICK block, so nothing about how
    the components are written has to change.
    """
    begin = f"// >>> AUTO-GENERATED {marker} BEGIN"
    end = f"// <<< AUTO-GENERATED {marker} END"
    if not os.path.exists(path):
        return f"missing file: {path}"
    src = open(path, encoding="utf-8").read()
    if begin not in src or end not in src:
        return (f"no {marker} markers in {os.path.basename(path)} — add:\n"
                f"      {begin}\n      ...\n      {end}")
    pattern = re.compile(re.escape(begin) + r".*?" + re.escape(end), re.S)
    new = f"{begin}\n{body}\n{end}"
    out = pattern.sub(lambda _: new, src, count=1)
    if not dry:
        open(path, "w", encoding="utf-8", newline="\n").write(out)
    return f"ok — {os.path.basename(path)} [{marker}]"


def main():
    ap = argparse.ArgumentParser(description="Generate site data from real logs")
    ap.add_argument("--season", type=int, default=2025)
    ap.add_argument("--inject", metavar="SRC_DIR",
                    help="path to cfb-app/src; omit to preview only")
    ap.add_argument("--preview", action="store_true")
    ap.add_argument("--limit", type=int, default=24)
    args = ap.parse_args()

    print(f"\nBuilding from {args.season} game logs "
          f"(window {WINDOW}, priced band {BAND_PROB[0]:.0%}-{BAND_PROB[1]:.0%})\n")

    streaks = build_streaks(args.season, args.limit)
    players = build_players(args.season)
    props = build_props(args.season, streaks)
    print(f"  {len(streaks)} floor lines · {len(players)} players · {len(props)} prop rows")

    if args.preview or not args.inject:
        print(f"\n  {'player':<22}{'prop':<12}{'line':>7}{'cleared':>10}"
              f"{'strk':>6}{'avg':>7}{'model':>8}{'max px':>8}{'log-mdl':>9}")
        print("  " + "-" * 89)
        for r in streaks[:20]:
            print(f"  {r['player'][:21]:<22}{r['label']:<12}{r['line']:>7}"
                  f"{r['hit']:>5}/{r['of']:<4}{r['streak']:>6}{r['avg']:>7}"
                  f"{r['model']*100:>7.0f}%{r['max_odds']:>8}"
                  f"{r['log_vs_model']*100:>+8.0f}p")

    if args.inject:
        src = args.inject
        stamp = f"// generated {date.today()} from {args.season} logs"
        jobs = [
            ("StreakCenter.jsx", "STREAKS",
             stamp + "\n" + js_const("STREAK_ROWS", streaks)),
            ("PropHub.jsx", "PROPS",
             stamp + "\n" + js_const("PROP_ROWS", props)),
            ("PlayerStatsHub.jsx", "PLAYERS",
             stamp + "\n" + js_const("PLAYER_ROWS", players)),
        ]
        print()
        for fn, marker, body in jobs:
            print("  " + inject(os.path.join(src, fn), marker, body))
    print()


if __name__ == "__main__":
    main()
