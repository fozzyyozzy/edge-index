"""Phase 5E: CFB floor card + tickets from a DK snapshot (PAPER ONLY).

    python -m engine.cfb.cards.card --week 7                 # Tue 10 AM ET 'bet' snapshot -> DRAFT
    python -m engine.cfb.cards.card --week 7 --snapshot latest   # testing on another snapshot (DRAFT)
    python -m engine.cfb.cards.card --week 7 --publish       # after Tim's OK: data/cfb/cards/ (logged)

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
        bet = main[(main.label == "bet") & (et.dt.weekday == 1)]
        if bet.empty:
            raise SystemExit("no Tuesday 10 AM 'bet' snapshot yet for this week "
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
    t = pd.read_csv(TARGETS / f"targets_{season}_wk{week:02d}.csv")
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


def tickets(floor: pd.DataFrame, n_tickets=3, sizes=(3, 4), target=200.0, pool_n=16):
    """Pool = floor legs + second legs. Rules (Tim, 2026-10-12/13):
      * each GAME appears on at most ONE ticket per slate (any market, any leg); this supersedes the
        earlier floor-star exception, so no leg or game repeats across tickets
      * cross-game only within a ticket; at most MAX_ALT_SHAPE ALT-SHAPE legs per ticket
      * pick the highest joint probability at >= +200; if no combination reaches +200 under the
        rules, take the best one and label it "reduced payout, floors held"."""
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
        used_games |= set(f.loc[list(combo)].game_id)
        out.append({"ticket": t + 1,
                    "legs": f.loc[list(combo)][["game_id", "game", "pick", "market", "role", "price", "p_used"]].to_dict("records"),
                    "price_american": round(price), "p_joint": pj, "ev": pj * dec - 1,
                    "alt_shape_legs": int((f.loc[list(combo)].market == "ALT-SHAPE").sum()),
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


def readout(card: dict) -> str:
    lad = card.get("ladder_snapshot_utc")
    lines = [f"# CFB floor card: {card['season']} week {card['week']} ({card['status']})",
             f"Main lines: {card['snapshot_utc']} ({card['snapshot_et']} ET, label {card['snapshot_label']}). "
             + (f"Ladders (alt spreads/totals/team totals): {lad}. " if lad and lad != card['snapshot_utc'] else "")
             + f"Generated {card['generated_at_utc']}. PAPER ONLY.",
             (f"Note: {card['snapshot_note']}" if card.get("snapshot_note") else ""), ""]
    lines.append("## Floor legs (per game: highest-probability eligible leg; + second leg, other market)")
    lines.append("| role | game | pick | market | price | p | EV |\n|---|---|---|---|---|---|---|")
    for x in card["floor_legs"]:
        lines.append(f"| {x['role']} | {x['game']} | {x['pick']} | {x['market']} | {x['price']:+.0f} | "
                     f"{100 * x['p_used']:.1f}% | {100 * x['ev']:+.1f}% |")
    lines.append("\n## Tickets")
    for t in card["tickets"]:
        lines.append(f"**Ticket {t['ticket']}** ({t['label']}): {t['price_american']:+d}, joint p "
                     f"{100 * t['p_joint']:.1f}%, EV {100 * t['ev']:+.1f}%, ALT-SHAPE legs {t['alt_shape_legs']}")
        for x in t["legs"]:
            lines.append(f"- {x['game']}: {x['pick']} ({x['market']}) {x['price']:+.0f}, p {100 * x['p_used']:.1f}%")
    lines.append("\n## Main-spread edges vs this snapshot (edge >= 1.5 pts; strongest signal; one bet per game, the model's side)")
    lines.append("| game | pick | price | edge pts | p cover | EV |\n|---|---|---|---|---|---|")
    for x in card["spread_edges"]:
        lines.append(f"| {x['game']} | {x['pick']} | {x['price']:+.0f} | {x['edge_pts']:+.1f} | "
                     f"{100 * x['p_model']:.1f}% | {100 * x['ev']:+.1f}% |")
    lines.append(f"\nEligible legs: {card['counts']['eligible']} of {card['counts']['priced']} priced "
                 f"(by market: {card['counts']['eligible_by_market']}). Teasers: off until DK prices are filled in.")
    return "\n".join(lines)


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--season", type=int, default=config.CURRENT_SEASON)
    ap.add_argument("--week", type=int, required=True)
    ap.add_argument("--snapshot", default="tue10", help="tue10 (default) | latest | <ISO timestamp>")
    ap.add_argument("--publish", action="store_true", help="write data/cfb/cards (only after Tim's OK)")
    a = ap.parse_args(argv)
    ts, main_, lad, alt = load_snapshot(a.season, a.week, a.snapshot)
    g = game_table(main_, a.season, a.week)
    L = build_legs(g, lad, alt)
    fl = floor_legs(L)
    tk = tickets(fl)
    ed = spread_edges(g, L)
    label = main_.label.iloc[0]
    status = "PUBLISHED (paper)" if a.publish else ("DRAFT" if a.snapshot == "tue10" else "DRAFT - TEST SNAPSHOT, NOT THE BET-TIME CARD")
    elig = L[L.eligible]
    card = {"season": a.season, "week": a.week, "status": status,
            "snapshot_utc": ts.isoformat(), "snapshot_et": ts.tz_convert(ET).strftime("%a %Y-%m-%d %H:%M"),
            "snapshot_label": label, "generated_at_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            "ladder_snapshot_utc": LADDER_TS["ts"].isoformat() if LADDER_TS["ts"] is not None else None,
            "snapshot_note": (main_.retag_note.dropna().iloc[0] if "retag_note" in main_ and main_.retag_note.notna().any() else ""),
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
