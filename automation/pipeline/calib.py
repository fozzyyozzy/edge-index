"""
calib.py — SHADOW ONLY, not live. A calibrated hit probability for every board rung, from features known before
kickoff, fit with a regularized logistic regression; plus the "role down" flag. Used by the "calib" shadow card and by
calib_study.py. The live card, Legs board, record and newsletter never read anything here.

Features for a rung on week N's board (all from data that existed before that slate's first kickoff):
  - logit of DK's no-vig probability at the board price (the board's stored novig_pct; prices are only pulled for
    games that haven't started)
  - logit of the add-one L10 and L15 clear rates at the rung, recomputed here from game logs with week < N
  - market and position (one-hot), opp_d_rank and own_vol_rank (/32), spread, game total, team implied total
    (missing -> a neutral value plus a missing indicator)
  - role trend from the same nflverse sources usage_<season>_w<N>.json is built from (that file only keeps season
    averages): snap share, targets and carries in the last 2 games vs the prior 4, current season, week < N
  - flags on the board row: injury watch, QB change
Label: the rung cleared in the box score (voids excluded). Boards are taken at their last version generated before the
slate's first kickoff (git history; see pregame_board), so a post-game regrade can't leak into training.

  python pipeline/calib.py --fit --season 2026 --week 8     # model for week 8 cards, trained on weeks 3..7
"""
import argparse, json, math, os, subprocess, sys
import numpy as np
import pandas as pd
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import P, COL, norm_name, fetch_season, read_csv_source, implied, frac_count
from floors import INV, SLATE_DAYS, schedule

MARKETS = ["rec_yds", "receptions", "rush_yds", "rush_att", "pass_yds", "pass_att", "pass_cmps"]
POSITIONS = ["WR", "TE", "RB", "QB"]
FIRST_WEEK = 3                         # the first week with Legs boards
LAMBDA = 1.0                           # L2 penalty on standardized coefficients (intercept unpenalized)
GRADE_CUTS = [(.85, "A+"), (.80, "A"), (.75, "A-"), (.68, "B"), (.60, "C")]
ROLE_METRICS = {"rec_yds": ("snap", "tgt"), "receptions": ("snap", "tgt"), "rush_yds": ("snap", "car"),
                "rush_att": ("snap", "car"), "pass_yds": ("snap",), "pass_att": ("snap",), "pass_cmps": ("snap",)}
ROLE_DOWN = 0.25                       # set from calib_study's threshold table (see MODEL_CHANGELOG / study report)


def logit(p):
    p = min(max(float(p), 0.01), 0.99); return math.log(p / (1 - p))


def grade_of(p):
    return next((g for cut, g in GRADE_CUTS if p >= cut), "D")


# ── pregame boards ──────────────────────────────────────────────────────────────────────────────────────────────────
def first_kickoff(season, week, slate):
    sch = schedule(season, week); sch = sch[sch.weekday.isin(SLATE_DAYS[slate])]
    ts = [pd.Timestamp(f"{g.gameday}T{g.gametime}").tz_localize("America/New_York").tz_convert("UTC")
          for g in sch.itertuples() if isinstance(g.gametime, str)]
    return min(ts) if ts else None


def pregame_board(season, week, slate, versions=None):
    """The slate's Legs board as last generated BEFORE its first kickoff: the working file if it qualifies, else the
    newest git version that does. versions = [(label, doc)] newest first (tests); default = working file, then git log.
    Returns (doc, source) or (None, reason)."""
    ko = first_kickoff(season, week, slate)
    if ko is None: return None, "no kickoff in the schedule"
    rel = f"automation/cards/legs_{season}_w{week}_{slate}.json"
    def git_versions():
        f = P("cards", f"legs_{season}_w{week}_{slate}.json")
        if os.path.exists(f): yield "working file", json.load(open(f, encoding="utf-8"))
        root = os.path.dirname(os.path.dirname(P("cards")))
        try:
            shas = subprocess.check_output(["git", "-C", root, "log", "--format=%H", "--", rel], text=True,
                                           stderr=subprocess.DEVNULL).split()
        except Exception:
            return
        for sha in shas:
            try:
                yield sha[:8], json.loads(subprocess.check_output(["git", "-C", root, "show", f"{sha}:{rel}"],
                                                                  stderr=subprocess.DEVNULL).decode("utf-8"))
            except Exception:
                continue
    for label, doc in (versions if versions is not None else git_versions()):
        gen = pd.Timestamp(doc.get("meta", {}).get("generated", "2100-01-01T00:00+00:00"))
        if gen.tzinfo is None: gen = gen.tz_localize("UTC")
        if gen < ko: return doc, label
    return None, "no version generated before kickoff"


# ── features ────────────────────────────────────────────────────────────────────────────────────────────────────────
class Data:
    """game logs and snap shares for one season, cut at a week (walk-forward)"""
    def __init__(self, season, stats=None, snaps=None):
        self.season = season
        self.w = stats if stats is not None else pd.concat([fetch_season(y) for y in (season - 2, season - 1, season)])
        if snaps is None:
            try:
                s = read_csv_source("nflverse snap counts", season=season)
                s = s[s.game_type == "REG"]
                snaps = pd.DataFrame(dict(key=s.player.map(norm_name), week=s.week, snap=s.offense_pct.fillna(0)))
            except Exception:
                snaps = pd.DataFrame(columns=["key", "week", "snap"])
        self.snaps = snaps

    def before(self, week):
        w = self.w
        return w[(w.season < self.season) | ((w.season == self.season) & (w.week < week))]


def clear_counts(log, rung):
    """(h10, n10, h15, n15) at the rung from a game log (oldest first)"""
    v = np.asarray(log, dtype=float); a, b = v[-10:], v[-15:]
    return int((a >= rung).sum()), len(a), int((b >= rung).sum()), len(b)


def role_trend(data, key, market, week):
    """{metric: (prior mean, [last two])} for this market's role metrics: his last 2 games vs the up-to-4 before them,
    current season, week < N; {} with fewer than 4 games (2 + at least 2 prior)"""
    cur = data.w[(data.w.season == data.season) & (data.w.week < week) & (data.w.key == key)].sort_values("week")
    if len(cur) < 4: return {}
    last6 = cur.tail(6)
    out = {}
    snaps = data.snaps[data.snaps.key == key].groupby("week").snap.max() if len(data.snaps) else pd.Series(dtype=float)
    for m in ROLE_METRICS[market]:
        if m == "snap": vals = [float(snaps.get(wk, np.nan)) for wk in last6.week]
        elif m == "tgt": vals = list(last6.targets.fillna(0).astype(float))
        else: vals = list(last6.carries.fillna(0).astype(float))
        if any(np.isnan(vals)): continue
        out[m] = (float(np.mean(vals[:-2])), vals[-2:])
    return out


def role_down(trend, threshold=ROLE_DOWN):
    """True when, for any role metric with a real prior role, BOTH of the last two games are below the prior-4 average
    by more than `threshold` (relative)"""
    return bool(role_down_metrics(trend, threshold))


ROLE_FLOOR = {"snap": 0.20, "tgt": 2.0, "car": 2.0}      # a prior role worth losing
ROLE_NAMES = {"snap": "snap share", "tgt": "targets", "car": "carries"}


def role_down_metrics(trend, threshold=ROLE_DOWN):
    """the metrics that fired, in ROLE_METRICS order"""
    return [m for m, (prior, last2) in trend.items()
            if prior >= ROLE_FLOOR[m] and all(x < prior * (1 - threshold) for x in last2)]


def role_reason(trend, threshold=ROLE_DOWN):
    """'role down: carries 20→12→8' (prior average → each of the last two games); None when it doesn't fire"""
    fired = role_down_metrics(trend, threshold)
    if not fired: return None
    fmt = lambda m, x: f"{100 * x:.0f}%" if m == "snap" else f"{x:.0f}"
    return "role down: " + ", ".join(f"{ROLE_NAMES[m]} " + "→".join(fmt(m, x) for x in [trend[m][0]] + list(trend[m][1]))
                                     for m in fired)


def annotate_roles(players, data, week, threshold=ROLE_DOWN):
    """Sets role_trend / role_down / role_reason on every board row (held rows too), from games before `week` only.
    grade_legs.py calls it for the live board; the live card (from Week 9, 2026) holds role_down rows (R13)."""
    for p in players:
        t = role_trend(data, norm_name(p["player"]), p["market"], week)
        p["role_trend"] = {k: [round(v[0], 3), [round(x, 3) for x in v[1]]] for k, v in t.items()} or None
        p["role_reason"] = role_reason(t, threshold)
        p["role_down"] = bool(p["role_reason"])
    return players


FEATS = (["novig", "l10", "l15"] + [f"m_{m}" for m in MARKETS[1:]] + [f"pos_{p}" for p in POSITIONS[1:]] + ["pos_other"]
         + ["oppd_rank", "oppd_na", "vol_rank", "vol_na", "spread", "spread_na", "game_total", "gt_na", "team_total", "tt_na",
            "snap_delta", "tgt_logratio", "car_logratio", "role_na", "inj_watch", "qb_change"])


def rung_features(row, rung, log, trend):
    """feature dict for one rung of a board row; None when the rung has no market price or the player has no log"""
    if rung.get("novig_pct") is None or not len(log): return None
    h10, n10, h15, n15 = clear_counts(log, rung["rung"])
    f = dict(novig=logit(rung["novig_pct"] / 100), l10=logit((h10 + 1) / (n10 + 2)), l15=logit((h15 + 1) / (n15 + 2)))
    for m in MARKETS[1:]: f[f"m_{m}"] = float(row["market"] == m)
    pos = row.get("pos")
    for p in POSITIONS[1:]: f[f"pos_{p}"] = float(pos == p)
    f["pos_other"] = float(pos not in POSITIONS)
    def num(k, default, scale=1.0):
        v = row.get(k)
        ok = v is not None and not (isinstance(v, float) and math.isnan(v))
        return (float(v) / scale if ok else default), (0.0 if ok else 1.0)
    f["oppd_rank"], f["oppd_na"] = num("opp_d_rank", 0.5, 32)
    f["vol_rank"], f["vol_na"] = num("own_vol_rank", 0.5, 32)
    f["spread"], f["spread_na"] = num("spread", 0.0)
    f["game_total"], f["gt_na"] = num("game_total", 44.0)
    f["team_total"], f["tt_na"] = num("team_total", 22.0)
    if trend:
        s = trend.get("snap"); t = trend.get("tgt"); c = trend.get("car")
        f["snap_delta"] = (np.mean(s[1]) - s[0]) if s else 0.0
        f["tgt_logratio"] = math.log((np.mean(t[1]) + 0.5) / (t[0] + 0.5)) if t else 0.0
        f["car_logratio"] = math.log((np.mean(c[1]) + 0.5) / (c[0] + 0.5)) if c else 0.0
        f["role_na"] = 0.0
    else:
        f.update(snap_delta=0.0, tgt_logratio=0.0, car_logratio=0.0, role_na=1.0)
    flags = row.get("injury") or []
    f["inj_watch"] = float(any(str(x).startswith("injury watch") for x in flags))
    f["qb_change"] = float(any(str(x).startswith("QB change") for x in flags))
    return f


def board_rows(doc, data, week, with_labels=None):
    """[(row, rung, features, trend)] for every priced rung of every non-held row on a board; with_labels = {(key,
    market): actual} adds 'y' (1 hit / 0 miss; voids dropped)"""
    out = []
    before = data.before(week)
    for p in doc["players"]:
        if p.get("held"): continue
        key = norm_name(p["player"]); m = p["market"]
        g = before[(before.key == key) & (before[INV[m]].fillna(0) > 0)].sort_values(["season", "week"])
        log = g[COL[m]].fillna(0).to_numpy()
        trend = role_trend(data, key, m, week)
        for r in p["rungs"]:
            f = rung_features(p, r, log, trend)
            if f is None: continue
            item = dict(row=p, rung=r, f=f, trend=trend, week=week)
            if with_labels is not None:
                a = with_labels.get((key, m))
                if a is None or (isinstance(a, float) and math.isnan(a)): continue
                item["y"] = float(a >= r["rung"])
            out.append(item)
    return out


# ── model ───────────────────────────────────────────────────────────────────────────────────────────────────────────
def fit(X, y, lam=LAMBDA, cols=None):
    """L2-regularized logistic regression on standardized columns. Returns a JSON-able model dict."""
    from scipy.optimize import minimize
    X = np.asarray(X, dtype=float); y = np.asarray(y, dtype=float)
    mu = X.mean(0); sd = X.std(0); sd[sd < 1e-9] = 1.0
    Z = (X - mu) / sd; Z1 = np.hstack([np.ones((len(Z), 1)), Z])
    def loss(b):
        z = Z1 @ b; p = 1 / (1 + np.exp(-z))
        ll = -np.sum(y * np.log(np.clip(p, 1e-9, 1)) + (1 - y) * np.log(np.clip(1 - p, 1e-9, 1)))
        g = Z1.T @ (p - y)
        pen = 0.5 * lam * np.sum(b[1:] ** 2); g[1:] += lam * b[1:]
        return ll + pen, g
    b = minimize(loss, np.zeros(Z1.shape[1]), jac=True, method="L-BFGS-B").x
    return dict(cols=list(cols) if cols is not None else None, mu=mu.tolist(), sd=sd.tolist(), b=b.tolist(), lam=lam, n=int(len(y)))


def predict(model, X):
    X = np.asarray(X, dtype=float)
    Z = (X - np.asarray(model["mu"])) / np.asarray(model["sd"])
    z = model["b"][0] + Z @ np.asarray(model["b"][1:])
    return 1 / (1 + np.exp(-z))


def matrix(items, cols):
    return np.array([[it["f"][c] for c in cols] for it in items], dtype=float)


def labels_for(data, week):
    """{(key, market): box-score stat} for one week (the label source; never a feature)"""
    w = data.w[(data.w.season == data.season) & (data.w.week == week)]
    return {(k, m): v for m, c in COL.items() for k, v in zip(w.key, w[c])}


def training_items(season, weeks, data):
    """labelled items from every slate's pregame board for the given weeks; also returns {(week, slate): source}"""
    items, sources = [], {}
    for wk in weeks:
        act = labels_for(data, wk)
        for sl in ("tnf", "sun", "mnf"):
            if not os.path.exists(P("cards", f"legs_{season}_w{wk}_{sl}.json")): continue
            doc, src = pregame_board(season, wk, sl)
            sources[(wk, sl)] = src
            if doc is None: continue
            for it in board_rows(doc, data, wk, act):
                it["slate"] = sl; items.append(it)
    return items, sources


def fit_for_week(season, week, data=None):
    """the model used for week `week` cards: trained on weeks FIRST_WEEK..week-1 (pregame boards only)"""
    data = data or Data(season)
    items, sources = training_items(season, range(FIRST_WEEK, week), data)
    m = fit(matrix(items, FEATS), [it["y"] for it in items], cols=FEATS)
    m.update(season=season, for_week=week, trained_on=f"weeks {FIRST_WEEK}-{week - 1}",
             sources={f"w{k[0]} {k[1]}": v for k, v in sources.items()}, role_down=ROLE_DOWN)
    return m


def model_path(season, week):
    return P("models", f"calib_{season}_w{week}.json")


# ── scoring a board (the "calib" shadow card) ───────────────────────────────────────────────────────────────────────
def score_board(doc, season, week, model=None, data=None):
    """A copy of a Legs board with every priced rung's prob / grade / edge replaced by the calibrated model's, and each
    row's role_down flag set. Raises FileNotFoundError when the week has no fitted model."""
    import copy
    model = model or json.load(open(model_path(season, week), encoding="utf-8"))
    data = data or Data(season)
    d = copy.deepcopy(doc)
    items = board_rows(d, data, week)
    if items:
        probs = predict(model, matrix(items, model["cols"]))
        for it, p in zip(items, probs):
            r = it["rung"]; p = float(p)
            r.update(prob=round(p, 4), grade=grade_of(p), edge_pts=round(100 * (p - implied(r["est_odds"])), 1),
                     reasons=[f"calibrated {100 * p:.1f}%"], calib=True)
            it["row"]["role_down"] = role_down(it["trend"], model.get("role_down", ROLE_DOWN))
            it["row"]["role_trend"] = {k: [round(v[0], 3), [round(x, 3) for x in v[1]]] for k, v in it["trend"].items()}
    for p in d["players"]:                                   # rungs the model couldn't score can't be used by calib
        if p.get("held"): continue
        for r in p["rungs"]:
            if not r.get("calib"): r["grade"] = "F"; r.setdefault("reasons", []).append("no calibrated probability")
    return d


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--season", type=int, required=True); ap.add_argument("--week", type=int, required=True)
    ap.add_argument("--fit", action="store_true", help="fit and save the model for this week's cards")
    a = ap.parse_args()
    if a.fit:
        m = fit_for_week(a.season, a.week)
        json.dump(m, open(model_path(a.season, a.week), "w"), indent=1)
        print(f"wrote {model_path(a.season, a.week)}: n={m['n']}, {m['trained_on']}")


if __name__ == "__main__":
    main()
