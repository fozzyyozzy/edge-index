"""Phase 5E: CFB floor card + tickets from a DK snapshot (PAPER ONLY).

    python -m engine.cfb.cards.card --week 7                 # Tue 10 AM ET 'bet' snapshot -> DRAFT
    python -m engine.cfb.cards.card --week 7 --snapshot latest   # testing on another snapshot (DRAFT)
    python -m engine.cfb.cards.card --week 7 --publish       # after Tim's OK: data/cfb/cards/ (logged)
    python -m engine.cfb.weekly --week 8                     # update_week -> project_week -> this draft

Missing targets_<season>_wk<NN>.csv (project_week never ran) are built here from the as-of ratings
for week N (cutoff = the week's first kickoff, so week-N games already played are never used); that
build does NOT write the forward-test log (use engine.cfb.weekly for the full chain).
Late publish (Tim, 2026-10-23): legs and tickets only use games that kick off after the publish time
(--publish-at, default now); excluded games are listed and the card is labeled "published late:
Tuesday prices, Saturday-only games". Prices stay the Tuesday bet snapshot. The edge list keeps every
game at the Tuesday line, as pre-registered.

Drafts go to data/cfb/derived/ (gitignored). Only --publish writes data/cfb/cards/card_<season>_wk<NN>
.json/.md (committed, graded by `forward weekly`). Not on the site or in the newsletter.

Markets and evidence labels (Tim, 2026-10-12):
  SPREAD-CLV      main spread (getting-points side only on the card; the edge list shows both)
  ALT-SHAPE       alt spread rungs, getting points only (pending the ladder-shape bar)
  ML-SHADED       moneyline; |DK spread| > 14 -> p = (p_model + p_novig) / 2
  TEAM-TOTAL      alt team totals: center (DK total +- projected margin) / 2, rho 0.075, team spikes
  PAPER-UNPROVEN  game totals / alt totals (market-anchored: center = DK total); teasers (off for now)
Eligibility: week >= 4, price in [-500, +150], p >= 65%, EV at the posted price >= +2%,
spread rungs getting points only. Per game: floor leg = highest-probability eligible leg; second leg =
best eligible leg from a different market family. Tickets: 3-4 cross-game legs, 2-3 tickets, no leg
repeated and each game on at most one ticket per slate (any market), target >= +200, else
"reduced payout, floors held".
"""
from __future__ import annotations
import argparse
import glob
import hashlib
import itertools
import json
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats

from engine.cfb import config
from engine.cfb.lines.capture import SNAP, TARGETS
from engine.cfb.model import distribution as dist, run as mrun
from engine.cfb.totals import anchored, model as tm
from engine.cfb.totals.team_spikes import pmf as team_pmf

CARDS = config.DATA / "cards"
DRAFTS = config.DATA / "derived"
ET = "America/New_York"
PRICE_LO, PRICE_HI = -500, 150
P_MIN, EV_MIN = 0.65, 0.02
FAMILY = {"SPREAD-CLV": "spread", "ALT-SHAPE": "spread", "ML-SHADED": "moneyline",
          "TEAM-TOTAL": "team_total", "PAPER-UNPROVEN": "total"}


def payout(price):
    price = np.asarray(price, float)
    return np.where(price < 0, 100 / -price, price / 100)


def implied(price):
    price = np.asarray(price, float)
    with np.errstate(divide="ignore", invalid="ignore"):
        return np.where(price < 0, -price / (-price + 100), 100 / (price + 100))


def american(dec):
    return np.where(dec >= 2, (dec - 1) * 100, -100 / (dec - 1))


def sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()[:12] if p.exists() else ""


# ------------------------------------------------------------------ snapshot
def load_snapshot(season: int, week: int, which: str):
    def read(prefix):
        f = SNAP / f"{prefix}_{season}_wk{week:02d}.csv"
        return pd.read_csv(f) if f.exists() else pd.DataFrame()
    main, lad, alt = read("dk_main"), read("dk_ladders"), read("dk_alt_totals")
    if main.empty:
        raise SystemExit(f"no DK main snapshot for {season} wk {week}")
    main["ts"] = pd.to_datetime(main.captured_at_utc, utc=True)
    if which == "tue10":
        et = main.ts.dt.tz_convert(ET)
        bet = main[(main.label == "bet") & (et.dt.weekday == 1) & (et.dt.hour < 18)]   # late-bet rule
        if bet.empty:
            raise SystemExit("no Tuesday 'bet' snapshot before 18:00 ET for this week "
                             "(use --snapshot latest to test on another snapshot)")
        ts = bet.ts.min()
    elif which == "latest":
        ts = main.ts.max()
    else:
        ts = pd.Timestamp(which)
    pick = lambda df, t: df[pd.to_datetime(df.captured_at_utc, utc=True) == t] if len(df) else df  # noqa: E731
    # ladders: from the same snapshot if it has them; for the Tue bet card, otherwise the earliest
    # Tuesday 'bet' snapshot that does (e.g. a main-lines-only capture re-tagged as the bet snapshot)
    lad_ts = ts
    if which == "tue10" and (lad.empty or pick(lad, ts).empty) and len(lad):
        lt = pd.to_datetime(lad.captured_at_utc, utc=True)
        cand = lad[(lad.label == "bet") & (lt.dt.tz_convert(ET).dt.weekday == 1)]
        if len(cand):
            lad_ts = pd.to_datetime(cand.captured_at_utc, utc=True).min()
    LADDER_TS["ts"] = lad_ts
    return ts, pick(main, ts), pick(lad, lad_ts), pick(alt, lad_ts)


LADDER_TS = {"ts": None}


# ------------------------------------------------------------------ pricing
def ensure_targets(season: int, week: int) -> Path:
    """targets_<season>_wk<NN>.csv, built from the week-N as-of ratings if project_week never ran."""
    path = TARGETS / f"targets_{season}_wk{week:02d}.csv"
    if not path.exists():
        from engine.cfb.model import project_week
        print(f"{path.name} missing: building it with project_week (as-of week {week} ratings; "
              "forward log NOT written: run engine.cfb.weekly for that)")
        project_week.main(["--season", str(season), "--week", str(week), "--no-log"])
        if not path.exists():
            raise SystemExit(f"project_week did not write {path}")
    return path


def game_table(main: pd.DataFrame, season: int, week: int) -> pd.DataFrame:
    m = main.dropna(subset=["game_id"]).copy()
    m["game_id"] = m.game_id.astype(int)
    sp = m[(m.market == "spreads")]
    tot = m[(m.market == "totals")]
    h2h = m[(m.market == "h2h")]
    g = sp[sp.is_home == 1][["game_id", "week", "commence_time", "home_team", "away_team", "point", "price"]] \
        .rename(columns={"point": "home_spread", "price": "home_spread_price"})
    g = g.merge(sp[sp.is_home == 0][["game_id", "price"]].rename(columns={"price": "away_spread_price"}), on="game_id")
    g = g.merge(tot[tot.team == "Over"][["game_id", "point", "price"]].rename(columns={"point": "total", "price": "over_price"}),
                on="game_id", how="left")
    g = g.merge(tot[tot.team == "Under"][["game_id", "price"]].rename(columns={"price": "under_price"}), on="game_id", how="left")
    g = g.merge(h2h[h2h.is_home == 1][["game_id", "price"]].rename(columns={"price": "home_ml"}), on="game_id", how="left")
    g = g.merge(h2h[h2h.is_home == 0][["game_id", "price"]].rename(columns={"price": "away_ml"}), on="game_id", how="left")
    t = pd.read_csv(ensure_targets(season, week))
    g = g.merge(t[["game_id", "ratings_margin", "qb_delta", "k", "b_qb", "both_fbs"]], on="game_id", how="left")
    L = -g.home_spread
    g["proj"] = L + g.k * (g.ratings_margin - L) + g.b_qb * g.qb_delta.fillna(0)
    return g[g.week >= 4]


def build_legs(g: pd.DataFrame, lad: pd.DataFrame, alt: pd.DataFrame) -> pd.DataFrame:
    dp = mrun.dist_params(mrun.load_params())
    tp = json.loads(anchored.PARAMS.read_text())
    ts_ = {int(k): v for k, v in tp["team_score_spikes"]["spikes"].items()}
    kt = {int(k): v for k, v in tp["key_totals"].items()}
    rho = tp["rho_margin_total_resid"]
    legs = []
    for r in g.dropna(subset=["proj"]).itertuples():
        absl, tot = abs(r.home_spread), r.total if pd.notna(r.total) else 52.0
        P = dist.pmf([r.proj], [absl], [tot], dp)
        base = {"game_id": int(r.game_id), "game": f"{r.away_team} @ {r.home_team}",
                "kickoff_utc": r.commence_time, "dk_home_spread": r.home_spread, "dk_total": r.total,
                "proj_home_margin": float(r.proj)}

        def spread_leg(side, line, price, label, rung_kind):
            c, push = dist.cover(P, line, side)
            p = float(c[0] / max(1 - push[0], 1e-9)) if line % 1 == 0 else float(c[0])
            team = r.home_team if side == "home" else r.away_team
            legs.append({**base, "market": label, "pick": f"{team} {line:+g}", "side": side,
                         "line": float(line), "price": float(price), "p_model": p, "p_used": p,
                         "rung_kind": rung_kind})
        # main spreads (both sides; card eligibility applies the getting-points rule)
        spread_leg("home", r.home_spread, r.home_spread_price, "SPREAD-CLV", "main")
        spread_leg("away", -r.home_spread, r.away_spread_price, "SPREAD-CLV", "main")
        # alt spreads
        for x in lad[lad.game_id == r.game_id].itertuples():
            side = "home" if x.is_home == 1 else "away"
            spread_leg(side, float(x.rung), x.price, "ALT-SHAPE", "alt")
        # moneylines (shaded when |spread| > 14)
        if pd.notna(r.home_ml) and pd.notna(r.away_ml):
            ph = float((P * (dist.M[None, :] > 0)).sum())
            ih, ia = implied(r.home_ml), implied(r.away_ml)
            nv = float(ih / (ih + ia))
            shade = absl > 14
            for side, pm, pn, price in (("home", ph, nv, r.home_ml), ("away", 1 - ph, 1 - nv, r.away_ml)):
                team = r.home_team if side == "home" else r.away_team
                legs.append({**base, "market": "ML-SHADED", "pick": f"{team} ML", "side": side, "line": None,
                             "price": float(price), "p_model": pm, "p_novig": pn,
                             "p_used": (pm + pn) / 2 if shade else pm, "shaded": bool(shade), "rung_kind": "ml"})
        # game totals: market-anchored (center = DK total)
        st = tm.sigma_t([tp["sigma_t"]["a"], tp["sigma_t"]["c"]], np.array([tot]))
        PT = anchored.pmf_anchored(np.array([tot]), st, kt)
        tot_rows = [("Over", r.total, r.over_price), ("Under", r.total, r.under_price)] if pd.notna(r.total) else []
        a_t = alt[(alt.game_id == r.game_id) & (alt.market == "alternate_totals")] if len(alt) else alt
        tot_rows += [(x.side, x.point, x.price) for x in a_t.itertuples()]
        for side, L, price in tot_rows:
            ov, push = tm.over(PT, float(L))
            pov = float(ov[0] / max(1 - push[0], 1e-9))
            p = pov if side == "Over" else 1 - pov - (0 if float(L) % 1 else 0)
            if side == "Under":
                un = 1 - ov[0] - push[0]
                p = float(un / max(1 - push[0], 1e-9))
            legs.append({**base, "market": "PAPER-UNPROVEN", "pick": f"{side} {float(L):g} (game)", "side": side,
                         "line": float(L), "price": float(price), "p_model": p, "p_used": p,
                         "rung_kind": "total"})
        # team totals (alt team totals ladder)
        a_tt = alt[(alt.game_id == r.game_id) & (alt.market == "alternate_team_totals")] if len(alt) else alt
        if len(a_tt):
            sM = dist.sigma([dp["a"], dp["b"], dp["c"]], np.array([absl]), np.array([tot]))[0]
            sT = st[0]
            for side_name, sign in ((r.home_team, 1), (r.away_team, -1)):
                center = (tot + sign * r.proj) / 2
                sd = np.sqrt((sT ** 2 + sM ** 2 + sign * 2 * rho * sT * sM) / 4)
                PP = team_pmf([center], [sd], ts_)[0]
                pts = np.arange(len(PP))
                for x in a_tt[a_tt.team == side_name].itertuples():
                    over = float(PP[pts > x.point].sum())
                    p = over if x.side == "Over" else 1 - over
                    legs.append({**base, "market": "TEAM-TOTAL", "pick": f"{side_name} {x.side} {x.point:g}",
                                 "side": x.side, "line": float(x.point), "price": float(x.price),
                                 "p_model": p, "p_used": p, "rung_kind": "team_total"})
    L = pd.DataFrame(legs)
    L["ev"] = L.p_used * payout(L.price) - (1 - L.p_used)
    L["family"] = L.market.map(FAMILY)
    getting = (L.family != "spread") | (L.line > 0)
    L["eligible"] = (L.price.between(PRICE_LO, PRICE_HI) & (L.p_used >= P_MIN) & (L.ev >= EV_MIN) & getting)
    return L


# ------------------------------------------------------------------ hooks (display only; no selection change)
KEYS = (3, 7, 10, 14, 17, 21)


def hook_key(line: float):
    """(key, next_line) when a spread leg stops on/half a point short of a key number, else None.
    Team covers if team_margin + line > 0. A x.5 line fails at margin -(line + 0.5); a whole line
    pushes at margin -line. If that margin is +-key, the next rung across it is line + 1 (x.5) or
    line + 0.5 (whole). E.g. +6.5 -> loses by exactly 7 -> +7.5; -7.5 -> wins by exactly 7 -> -6.5."""
    half = abs(line % 1 - 0.5) < 1e-9
    k = -(line + 0.5) if half else -line
    if abs(k) in KEYS:
        return int(abs(k)), line + (1.0 if half else 0.5)
    return None


def add_hooks(rows: pd.DataFrame, L: pd.DataFrame) -> pd.DataFrame:
    """For spread-family rows, attach the next rung across the key (price, p, EV from the priced legs)."""
    rows = rows.copy()
    sp = L[L.family == "spread"]
    out = []
    for r in rows.itertuples():
        h = None
        if r.market in ("SPREAD-CLV", "ALT-SHAPE") and pd.notna(r.line):
            hk = hook_key(float(r.line))
            if hk:
                key, nxt = hk
                z = sp[(sp.game_id == r.game_id) & (sp.side == r.side) & np.isclose(sp.line, nxt)]
                h = {"key": key, "next_rung": nxt, "available": bool(len(z))}
                if len(z):
                    z = z.sort_values("price", ascending=False).iloc[0]
                    h.update({"price": float(z.price), "p": float(z.p_used), "ev": float(z.ev)})
        out.append(h)
    rows["hook"] = out
    return rows


# ------------------------------------------------------------------ late publish
LATE_LABEL = "published late: Tuesday prices, Saturday-only games"


def late_filter(L: pd.DataFrame, publish_at: pd.Timestamp):
    """(legs for the floor card/tickets, excluded games, label). Only games kicking off after the
    publish time; the label is Tim's when every remaining game is a Saturday (ET) game, else it names
    the days actually left."""
    ko = pd.to_datetime(L.kickoff_utc, utc=True)
    keep = ko > publish_at
    gone = (L[~keep].drop_duplicates("game_id")[["game_id", "game", "kickoff_utc"]]
            .sort_values("kickoff_utc").to_dict("records"))
    if not gone:
        return L, [], ""
    kept = ko[keep].dt.tz_convert(ET)
    days = [d for _, d in sorted(set(zip(kept.dt.date, kept.dt.strftime("%a"))))]   # in calendar order
    label = LATE_LABEL if days == ["Sat"] else f"published late: Tuesday prices, games not yet started ({'/'.join(days)})"
    return L[keep], gone, label


# ------------------------------------------------------------------ card + tickets
def floor_legs(L: pd.DataFrame) -> pd.DataFrame:
    e = L[L.eligible].sort_values(["p_used", "ev"], ascending=False)
    floor = e.drop_duplicates("game_id").assign(role="floor")
    second = []
    for gid, f in floor.set_index("game_id").iterrows():
        o = e[(e.game_id == gid) & (e.family != f.family)]
        if len(o):
            second.append(o.iloc[0])
    sec = pd.DataFrame(second).assign(role="second") if second else pd.DataFrame()
    return pd.concat([floor, sec], ignore_index=True)


MAX_ALT_SHAPE = 2       # Tim, 2026-10-12: at most 2 ALT-SHAPE legs per ticket


FOURTH_LEG_MARKETS = ("TEAM-TOTAL", "ML-SHADED")


def tickets(floor: pd.DataFrame, n_tickets=3, sizes=(3, 4), target=200.0, pool_n=16, extra=None):
    """Pool = floor legs + second legs. Rules (Tim, 2026-10-12/13):
      * each GAME appears on at most ONE ticket per slate (any market, any leg); this supersedes the
        earlier floor-star exception, so no leg or game repeats across tickets
      * cross-game only within a ticket; at most MAX_ALT_SHAPE ALT-SHAPE legs per ticket
      * pick the highest joint probability at >= +200
      * Tim, 2026-10-28: if no pool ticket reaches +200, try every rule-legal 3-leg pool base plus a
        4th ELIGIBLE leg from `extra` (any eligible TEAM-TOTAL or ML-SHADED leg, not only the
        floor/second pool) on a game no ticket uses yet; among those reaching +200, the highest joint
        probability. Tickets that already reach +200 from the pool are unchanged. The ALT-SHAPE cap
        is unaffected (the 4th leg is never ALT-SHAPE).
      * only if no rule-legal 4th leg reaches +200: the best ticket, labeled "reduced payout, floors held"."""
    f = floor.sort_values("p_used", ascending=False).head(pool_n).reset_index(drop=True)
    used_games, out = set(), []
    for t in range(n_tickets):
        avail = f[~f.game_id.isin(used_games)]
        if avail.game_id.nunique() < min(sizes):
            break
        best = None
        for k in sizes:
            for combo in itertools.combinations(avail.index, k):
                c = f.loc[list(combo)]
                if c.game_id.nunique() < k or (c.market == "ALT-SHAPE").sum() > MAX_ALT_SHAPE:
                    continue
                dec = float(np.prod(1 + payout(c.price)))
                pj = float(np.prod(c.p_used))
                price = float(american(dec))
                key = (price >= target, pj)
                if best is None or key > best[0]:
                    best = (key, combo, dec, pj, price)
        if best is None:
            break
        _, combo, dec, pj, price = best
        legs = f.loc[list(combo)]
        fourth = None
        if price < target and extra is not None and len(extra):
            # no pool ticket reaches +200: any rule-legal 3-leg pool base + a 4th eligible leg
            x = extra[extra.market.isin(FOURTH_LEG_MARKETS) & ~extra.game_id.isin(used_games)]
            for base in itertools.combinations(avail.index, 3):
                b = f.loc[list(base)]
                if b.game_id.nunique() < 3 or (b.market == "ALT-SHAPE").sum() > MAX_ALT_SHAPE:
                    continue
                db, pb = float(np.prod(1 + payout(b.price))), float(np.prod(b.p_used))
                for r in x[~x.game_id.isin(b.game_id)].itertuples():
                    d4, p4 = db * (1 + float(payout(r.price))), pb * float(r.p_used)
                    if float(american(d4)) >= target and (fourth is None or p4 > fourth[3]):
                        fourth = (base, r.Index, d4, p4)
        if fourth is not None:
            base, idx, dec, pj = fourth
            legs = pd.concat([f.loc[list(base)], extra.loc[[idx]].assign(role="4th leg")], ignore_index=True)
            price = float(american(dec))
        used_games |= set(legs.game_id)
        out.append({"ticket": t + 1,
                    "legs": legs[["game_id", "game", "pick", "market", "role", "price", "p_used"]].to_dict("records"),
                    "price_american": round(price), "p_joint": pj, "ev": pj * dec - 1,
                    "alt_shape_legs": int((legs.market == "ALT-SHAPE").sum()),
                    "label": "Bloom (>= +200)" if price >= target else "reduced payout, floors held"})
    return out


def spread_edges(g: pd.DataFrame, L: pd.DataFrame) -> pd.DataFrame:
    m = L[(L.market == "SPREAD-CLV")].copy()
    m["edge_pts"] = np.where(m.side == "home", m.proj_home_margin + m.dk_home_spread,
                             -(m.proj_home_margin + m.dk_home_spread))
    # ONE bet per game, the model's side: the two sides' edges are exact negatives, so at most one
    # can reach +1.5; the drop_duplicates makes that explicit (and safe if pricing ever changes)
    m = m[m.edge_pts >= 1.5].sort_values("edge_pts", ascending=False).drop_duplicates("game_id")
    return m[["game_id", "game", "pick", "side", "line", "price", "edge_pts", "p_model", "ev",
              "proj_home_margin", "dk_home_spread"]]


def hook_text(h) -> str:
    if not h or not isinstance(h, dict):
        return ""
    if not h.get("available"):
        return f"stops at {h['key']}; {h['next_rung']:+g} not offered"
    return (f"stops at {h['key']}: {h['next_rung']:+g} @ {h['price']:+.0f}, p {100 * h['p']:.1f}%, "
            f"EV {100 * h['ev']:+.1f}%")


def readout(card: dict) -> str:
    lad = card.get("ladder_snapshot_utc")
    lines = [f"# CFB floor card: {card['season']} week {card['week']} ({card['status']})"
             + (f": {card['late_label']}" if card.get("late_label") else ""),
             f"Main lines: {card['snapshot_utc']} ({card['snapshot_et']} ET, label {card['snapshot_label']}"
             + (f", slot {card['snapshot_slot']}, {card['snapshot_lag_min']:.0f} min after the slot time"
                if card.get("snapshot_slot") and card.get("snapshot_lag_min") is not None else "") + "). "
             + (f"Ladders (alt spreads/totals/team totals): {lad}. " if lad and lad != card['snapshot_utc'] else "")
             + f"Generated {card['generated_at_utc']}. PAPER ONLY.",
             (f"Note: {card['snapshot_note']}" if card.get("snapshot_note") else ""), ""]
    if card.get("excluded_started_games"):
        ex = card["excluded_started_games"]
        lines += [f"**{card['late_label']}.** Published {card['published_at_utc']}; {len(ex)} games that kicked "
                  "off before then are left off the floor legs and tickets: "
                  + "; ".join(x["game"] for x in ex) + ". The edge list below still covers every game at "
                  "the Tuesday line (pre-registered).", ""]
    lines.append("## Floor legs (per game: highest-probability eligible leg; + second leg, other market)")
    lines.append("| role | game | pick | market | price | p | EV | hook: next rung across the key |\n"
                 "|---|---|---|---|---|---|---|---|")
    for x in card["floor_legs"]:
        lines.append(f"| {x['role']} | {x['game']} | {x['pick']} | {x['market']} | {x['price']:+.0f} | "
                     f"{100 * x['p_used']:.1f}% | {100 * x['ev']:+.1f}% | {hook_text(x.get('hook'))} |")
    lines.append("\n## Tickets")
    for t in card["tickets"]:
        lines.append(f"**Ticket {t['ticket']}** ({t['label']}): {t['price_american']:+d}, joint p "
                     f"{100 * t['p_joint']:.1f}%, EV {100 * t['ev']:+.1f}%, ALT-SHAPE legs {t['alt_shape_legs']}")
        for x in t["legs"]:
            lines.append(f"- {x['game']}: {x['pick']} ({x['market']}) {x['price']:+.0f}, p {100 * x['p_used']:.1f}%")
    lines.append("\n## Main-spread edges vs this snapshot (edge >= 1.5 pts; strongest signal; one bet per game, the model's side)")
    lines.append("| game | pick | price | edge pts | p cover | EV | hook: next rung across the key |\n"
                 "|---|---|---|---|---|---|---|")
    for x in card["spread_edges"]:
        lines.append(f"| {x['game']} | {x['pick']} | {x['price']:+.0f} | {x['edge_pts']:+.1f} | "
                     f"{100 * x['p_model']:.1f}% | {100 * x['ev']:+.1f}% | {hook_text(x.get('hook'))} |")
    lines.append(f"\nEligible legs: {card['counts']['eligible']} of {card['counts']['priced']} priced "
                 f"(by market: {card['counts']['eligible_by_market']}). Teasers: off until DK prices are filled in.")
    return "\n".join(lines)


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--season", type=int, default=config.CURRENT_SEASON)
    ap.add_argument("--week", type=int, required=True)
    ap.add_argument("--snapshot", default="tue10", help="tue10 (default) | latest | <ISO timestamp>")
    ap.add_argument("--publish", action="store_true", help="write data/cfb/cards (only after Tim's OK)")
    ap.add_argument("--publish-at", help="publish time (ISO; ET if no zone; default now): games kicked "
                                         "off before it are left off the floor card and tickets")
    a = ap.parse_args(argv)
    ts, main_, lad, alt = load_snapshot(a.season, a.week, a.snapshot)
    g = game_table(main_, a.season, a.week)
    L = build_legs(g, lad, alt)
    pub = pd.Timestamp(a.publish_at) if a.publish_at else pd.Timestamp.now(tz="UTC")
    pub = (pub.tz_localize(ET) if pub.tzinfo is None else pub).tz_convert("UTC")
    Lc, excluded, late_label = late_filter(L, pub)
    fl = floor_legs(Lc)
    tk = tickets(fl, extra=Lc[Lc.eligible])
    ed = spread_edges(g, L)                     # edge list: every game at the Tuesday line (pre-registered)
    fl = add_hooks(fl, L)                       # display only: selection above is unchanged
    ed = add_hooks(ed.assign(market="SPREAD-CLV", family="spread"), L)
    label = main_.label.iloc[0]
    status = "PUBLISHED (paper)" if a.publish else ("DRAFT" if a.snapshot == "tue10" else "DRAFT - TEST SNAPSHOT, NOT THE BET-TIME CARD")
    elig = L[L.eligible]
    card = {"season": a.season, "week": a.week, "status": status,
            "snapshot_utc": ts.isoformat(), "snapshot_et": ts.tz_convert(ET).strftime("%a %Y-%m-%d %H:%M"),
            "snapshot_label": label, "generated_at_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            "ladder_snapshot_utc": LADDER_TS["ts"].isoformat() if LADDER_TS["ts"] is not None else None,
            "snapshot_note": (main_.retag_note.dropna().iloc[0] if "retag_note" in main_ and main_.retag_note.notna().any() else ""),
            "snapshot_slot": str(main_.slot.iloc[0]) if "slot" in main_ and main_.slot.notna().any() else "",
            "snapshot_lag_min": float(main_.slot_lag_min.iloc[0]) if "slot_lag_min" in main_ and main_.slot_lag_min.notna().any() else None,
            "published_at_utc": pub.isoformat(timespec="seconds"),
            "late_label": late_label, "excluded_started_games": excluded,
            "params": {"phase3": sha(mrun.PARAMS), "totals": sha(anchored.PARAMS)},
            "rules": {"price": [PRICE_LO, PRICE_HI], "p_min": P_MIN, "ev_min": EV_MIN,
                      "spread_rungs": "getting points only", "ml_shading": "|spread| > 14 -> (p_model + p_novig)/2",
                      "teasers": "off until DK prices are filled in"},
            "counts": {"games": int(g.game_id.nunique()), "priced": int(len(L)), "eligible": int(len(elig)),
                       "eligible_by_market": elig.market.value_counts().to_dict()},
            "floor_legs": fl.drop(columns=["eligible"]).to_dict("records"),
            "tickets": tk, "spread_edges": ed.to_dict("records")}
    out_dir = CARDS if a.publish else DRAFTS
    stem = f"card_{a.season}_wk{a.week:02d}" + ("" if a.publish else "_draft")
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / f"{stem}.json").write_text(json.dumps(card, indent=1, default=str))
    md = readout(card)
    (out_dir / f"{stem}.md").write_text(md, encoding="utf-8")
    print(md)
    print(f"\n-> {out_dir / stem}.json/.md")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
