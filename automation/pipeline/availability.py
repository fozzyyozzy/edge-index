"""
availability.py — R6 injury holds. Who is coming back from a missed game, who carries an injury designation, and who is
held by hand this week. grade_legs.py runs it (card.yml runs that first), writes the snapshot to
cards/availability_<season>_w<week>_<slate>.json, and build_card_json.py reads the same snapshot, so the Legs tab and the
card hold the same players for the same reasons.

Sources (nflverse-data GitHub releases, free, no key):
  snap_counts/snap_counts_<season>.csv   per game: player, team, week, offense_snaps (PFR). A player "missed" a game when
                                         his team played and he has no offensive snaps in it. Byes don't count: only
                                         weeks his team actually played are looked at.
  injuries/injuries_<season>.csv         per week: report_status (Out / Doubtful / Questionable; blank until the Friday
                                         report), practice_status (DNP / Limited / Full). One row per player-week, the
                                         latest the report has.
  notes/holds_<season>_w<week>.csv       manual holds: Player,Reason (optional Market column: hold one market only).

Rules (a hold is a hard hold: grade F on the Legs tab, never on a card ticket):
  hold  no offensive snaps in his team's most recent game (snap counts, or a weekly stats row with a target, carry or
        pass attempt): this would be his first game back, and snaps, role and the L10/L15 window all lag
  flag  no offensive snaps in the team's game before that, but played the most recent one
  hold  report status Out, Doubtful or Questionable for this week
  hold  Did Not Participate in this week's latest practice report (a "resting player" rest day is ignored)
  hold  manual hold
  flag  Limited practice this week with no game status yet
  flag  QB change: the team's leading passer (pass attempts) in its most recent game isn't the QB who led most of its
        last 10 games -> every pass-catcher's and passer's receiving/passing legs on that team ("QB change: history from
        a different QB"). The L10/L15 history was built with someone else throwing.
Flags are warnings on the leg (Legs tab and card); they don't change the grade or keep a leg off a ticket.
Only weeks strictly before `week` count for missed games (walk-forward).

  python pipeline/availability.py --season 2026 --week 4 --slate sun      # print the snapshot
"""
import argparse, io, json, os, sys, urllib.request
from datetime import datetime, timezone
import pandas as pd
sys.path.insert(0, os.path.dirname(__file__))
from common import norm_name, P, fetch_season

REL = "https://github.com/nflverse/nflverse-data/releases/download"
STATUS_HOLD = {"Out", "Doubtful", "Questionable"}
DNP = "Did Not Participate In Practice"
LIMITED = "Limited Participation in Practice"

def _get(url, tries=3, wait=10):
    """nflverse CSV; retried, so a brief GitHub blip doesn't leave the card without R6 data (card_qa.py fails on that)"""
    import time
    for i in range(tries):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
            return pd.read_csv(io.BytesIO(urllib.request.urlopen(req, timeout=120).read()), low_memory=False)
        except Exception:
            if i == tries - 1: raise
            time.sleep(wait * (i + 1))

def team_games(snaps, stats, week):
    """{team: {week: [norm_name who played on offense]}} for the team's last two played weeks before `week` (a bye is
    skipped: only weeks the team has rows count). Played = offensive snaps (PFR) OR a weekly stats row with a target,
    carry or pass attempt (nflverse) — the union covers name mismatches between the two (PFR "Kenneth Gainwell")."""
    rows = []
    if snaps is not None:
        s = snaps[(snaps.week < week) & (snaps.game_type == "REG")]
        rows.append(pd.DataFrame(dict(team=s.team, week=s.week, key=s.player.map(norm_name), on=s.offense_snaps.fillna(0) > 0)))
    if stats is not None:
        t = stats[stats.week < week]
        use = sum(t[c].fillna(0) for c in ("targets", "carries", "attempts") if c in t) > 0
        rows.append(pd.DataFrame(dict(team=t.team, week=t.week, key=t.key, on=use)))
    if not rows: return {}
    a = pd.concat(rows); out = {}
    for tm, g in a.groupby("team"):
        for w in sorted(g.week.unique())[-2:]:
            out.setdefault(tm, {})[str(int(w))] = sorted(set(g[(g.week == w) & g.on].key))
    return out

def missed(snap, name, team):
    """(weeks among the team's last two games with no offensive snaps for this player, the team's latest game week);
    ([], None) if unknown"""
    games = snap.get("team_games", {}).get(team or "", {})
    if not games: return [], None
    k = norm_name(name); wks = sorted(int(w) for w in games)
    return [w for w in wks if k not in games[str(w)]], wks[-1]

PASS_MARKETS = {"rec_yds", "receptions", "pass_yds", "pass_att", "pass_cmps"}   # a QB change touches these legs


def qb_changes(stats, season, week, window=10):
    """{team: dict(recent, usual, usual_games, games, week)} for teams whose leading passer in their most recent game
    (by pass attempts) is not the one who led most of their last `window` games. Walk-forward: only games before
    (season, week). stats = weekly player rows (several seasons) with team, season, week, attempts, player_display_name."""
    s = stats[(stats.attempts.fillna(0) > 0) & ((stats.season < season) | ((stats.season == season) & (stats.week < week)))]
    out = {}
    for tm, g in s.groupby("team"):
        lead = g.sort_values("attempts", ascending=False).drop_duplicates(["season", "week"])
        lead = lead.sort_values(["season", "week"]).tail(window)
        if lead.empty: continue
        counts = lead.player_display_name.value_counts()
        recent, usual = lead.player_display_name.iloc[-1], counts.index[0]
        if recent != usual and counts.iloc[0] > len(lead) / 2:       # "most of the window" led by someone else
            last = lead.iloc[-1]
            out[tm] = dict(recent=recent, usual=usual, usual_games=int(counts.iloc[0]), games=int(len(lead)),
                           week=f"{int(last.season)} wk {int(last.week)}")
    return out


def build(season, week, stats=None):
    """players: {norm_name: dict(team, hold=[reasons], flag=[reasons], status, injury, practice, manual)} for everyone
    the injury report or the manual file names; team_games: who played in each team's last two games; plus sources."""
    out, src, games = {}, {}, {}
    def ent(key, tm):
        return out.setdefault(key, dict(team=tm, hold=[], flag=[], status=None, injury=None, practice=None))
    snaps = None
    try:
        snaps = _get(f"{REL}/snap_counts/snap_counts_{season}.csv")
        src["snap_counts"] = f"weeks {int(snaps.week.min())}-{int(snaps.week.max())}"
    except Exception as ex:                                        # no data = no automatic hold, but say so on the card
        src["snap_counts"] = f"unavailable ({type(ex).__name__})"
    try:
        if stats is None: stats = fetch_season(season)
        src["weekly_stats"] = f"weeks {int(stats.week.min())}-{int(stats.week.max())}" if len(stats) else "empty"
    except Exception as ex:
        stats = None; src["weekly_stats"] = f"unavailable ({type(ex).__name__})"
    games = team_games(snaps, stats, week)
    qb = {}
    try:                                   # L10 reaches into last season early in the year
        both = pd.concat([fetch_season(season - 1), stats]) if stats is not None else None
        if both is not None:
            qb = qb_changes(both, season, week)
            src["qb_change"] = f"{len(qb)} team(s): " + ", ".join(sorted(qb)) if qb else "none"
    except Exception as ex:
        src["qb_change"] = f"unavailable ({type(ex).__name__})"
    try:
        inj = _get(f"{REL}/injuries/injuries_{season}.csv")
        inj = inj[(inj.week == week) & (inj.season_type == "REG")]
        for r in inj.itertuples():
            key = norm_name(r.full_name); e = ent(key, r.team)
            hurt = r.report_primary_injury if isinstance(r.report_primary_injury, str) else (
                   r.practice_primary_injury if isinstance(r.practice_primary_injury, str) else None)
            st = r.report_status if isinstance(r.report_status, str) else None
            pr = r.practice_status if isinstance(r.practice_status, str) else None
            e.update(status=st, injury=hurt, practice=pr)
            what = f" ({hurt.lower()})" if hurt else ""
            if st in STATUS_HOLD: e["hold"].append(f"{st.lower()}{what}")
            elif "resting player" in (hurt or "").lower(): pass                  # veteran rest day: not an injury
            elif pr == DNP: e["hold"].append(f"did not practice{what}")
            elif pr == LIMITED: e["flag"].append(f"limited in practice{what}, no game status yet")
        src["injuries"] = f"week {week}: {len(inj)} report rows"
    except Exception as ex:
        src["injuries"] = f"unavailable ({type(ex).__name__})"
    manual = P("notes", f"holds_{season}_w{week}.csv")
    if os.path.exists(manual):
        m = pd.read_csv(manual)
        for r in m.itertuples():
            e = ent(norm_name(r.Player), None)
            mk = getattr(r, "Market", None)
            e.setdefault("manual", []).append(dict(reason=str(r.Reason), market=mk if isinstance(mk, str) and mk else None))
        src["manual"] = os.path.relpath(manual, P()).replace(os.sep, "/")
    # drop players with nothing to say (a Full-practice row and no misses)
    out = {k: v for k, v in out.items() if v["hold"] or v["flag"] or v.get("manual")}
    return dict(season=season, week=week, fetched_at=datetime.now(timezone.utc).isoformat(timespec="minutes"),
                sources=src, team_games=games, qb_change=qb, players=out)

def path(season, week, slate):
    return P("cards", f"availability_{season}_w{week}_{slate}.json")

def load(season, week, slate):
    """the snapshot grade_legs.py wrote; build it (and write it) if there isn't one"""
    f = path(season, week, slate)
    if os.path.exists(f): return json.load(open(f))
    snap = build(season, week); json.dump(snap, open(f, "w"), indent=1); return snap

def reasons(snap, name, market, team=None):
    """(holds, flags) for one leg: manual holds first, then automatic ones. Team must match when both are known (a
    traded player's old-team rows don't hold him)."""
    e = snap["players"].get(norm_name(name)) or {}
    holds = [f"held by hand: {m['reason']}" for m in e.get("manual", []) if m["market"] in (None, market)]
    wks, latest = missed(snap, name, team)
    flags = []
    if latest in wks:                                              # not back yet, or this is the first game back
        holds.append(f"injury: no offensive snaps in wk {', '.join(map(str, wks))}"
                     + (" (the team's last two games)" if len(wks) > 1 else " (the team's last game)"))
    elif wks:                                                      # missed the game before, played the last one
        flags.append(f"injury watch: no offensive snaps in wk {wks[0]}, played wk {latest}")
    if e and (team is None or e["team"] in (None, team)):
        holds += [f"injury: {h}" for h in e["hold"]]
        flags += [f"injury watch: {f}" for f in e["flag"]]
    q = snap.get("qb_change", {}).get(team or "")
    if q and market in PASS_MARKETS:       # a watch (one ticket max, R11), not a hold
        flags.append(f"QB change: history from a different QB ({q['recent']} led the team's last game, {q['week']}; "
                     f"{q['usual']} led {q['usual_games']} of its last {q['games']})")
    return holds, flags

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--season", type=int, required=True); ap.add_argument("--week", type=int, required=True)
    ap.add_argument("--slate", default=None, help="write the snapshot for this slate")
    a = ap.parse_args()
    snap = build(a.season, a.week)
    if a.slate: json.dump(snap, open(path(a.season, a.week, a.slate), "w"), indent=1)
    print(snap["sources"])
    for k, e in sorted(snap["players"].items()):
        print(f"  {k:<26} {e['team'] or '':<4} hold={e['hold'] + [m['reason'] for m in e.get('manual', [])]} flag={e['flag']}")
    print({tm: {w: len(k) for w, k in g.items()} for tm, g in snap["team_games"].items()})
