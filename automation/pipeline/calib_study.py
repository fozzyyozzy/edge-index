"""
calib_study.py — SHADOW ONLY research report: does a calibrated model of board rungs beat DK's no-vig price?

  python pipeline/calib_study.py --season 2026 --weeks 3-8 --retro 4-8 --out receipts/calibration_study_2026.md

1. Dataset: every priced rung on every slate's PREGAME Legs board (calib.pregame_board: last version generated before the
   slate's first kickoff), features from calib.rung_features (week < N data only), label = cleared in the box score
   (no stat row = void, dropped).
2. Leave-one-week-out: for each week, fit on every other week and score that week. Model vs two DK baselines: DK's no-vig
   probability as is, and DK-only logistic (logit no-vig refit LOWO, so DK gets the same recalibration chance).
   Also walk-forward (train on weeks < N only) - the version a live card could actually have used.
3. Reliability, hit rate by calib grade, coefficients (fit on all labelled weeks), L2 sensitivity, role-down thresholds.
4. Retro (--retro): each slate's inputs at its card's publish commit (git), rebuilt offline with build_card_json --shadow
   for m20 / m40e0 / m40em1 / pfirst / calib (calib with that week's leave-that-week-out model), and the live card as it
   was published; every card scored the same way (all legs clear = win at the card's estimated payout).
"""
import argparse, json, math, os, shutil, subprocess, sys, tempfile
import numpy as np
import pandas as pd
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import calib
from calib import FEATS, Data, fit, predict, matrix, training_items, grade_of, role_down, first_kickoff
from common import P, COL, norm_name
from price_check import table

RETRO_SLUGS = ["legacy", "m20", "m40e0", "m40em1", "pfirst_norole", "pfirst", "pfirst_dog", "calib"]
INPUTS = ["floors/floors_{s}_w{w}_{sl}.csv", "cards/legs_{s}_w{w}_{sl}.json", "cards/availability_{s}_w{w}_{sl}.json",
          "lines/ladders_{s}_w{w}.csv", "lines/dk_{s}_w{w}_{sl}.csv", "lines/pulled_{s}_w{w}_{sl}.txt",
          "lines/pulled_{s}_w{w}.txt", "notes/notes_{s}_w{w}.md", "lines/twoway_{s}_w{w}.csv", "cards/card_{s}_w{w}_{sl}.json"]
LAMBDAS = [0.1, 1.0, 10.0, 100.0]
THRESHOLDS = [0.15, 0.20, 0.25, 0.30, 0.40, 0.50]


def logloss(y, p):
    p = np.clip(np.asarray(p, float), 1e-6, 1 - 1e-6); y = np.asarray(y, float)
    return float(-np.mean(y * np.log(p) + (1 - y) * np.log(1 - p)))


def brier(y, p):
    return float(np.mean((np.asarray(p, float) - np.asarray(y, float)) ** 2))


def lowo(items, weeks, lam=calib.LAMBDA, walk_forward=False, feats=FEATS):
    """per-item out-of-week predictions: (model, dk raw, dk refit). walk_forward: train on earlier weeks only"""
    pm, praw, pdk = np.full(len(items), np.nan), np.full(len(items), np.nan), np.full(len(items), np.nan)
    wk = np.array([it["week"] for it in items]); y = np.array([it["y"] for it in items])
    X = matrix(items, feats); Xd = matrix(items, ["novig"])
    for w in weeks:
        te = wk == w; tr = (wk < w) if walk_forward else (wk != w)
        if not te.any() or tr.sum() < 200: continue
        pm[te] = predict(fit(X[tr], y[tr], lam, feats), X[te])
        pdk[te] = predict(fit(Xd[tr], y[tr], lam, ["novig"]), Xd[te])
    praw[:] = [it["rung"]["novig_pct"] / 100 for it in items]
    return pm, praw, pdk


def metrics_rows(items, pm, praw, pdk, weeks):
    wk = np.array([it["week"] for it in items]); y = np.array([it["y"] for it in items])
    rows = []
    for w in list(weeks) + ["pooled"]:
        m = (~np.isnan(pm)) & ((wk == w) if w != "pooled" else True)
        if not m.any(): continue
        rows.append(dict(week=w, rungs=int(m.sum()), hit=f"{100 * y[m].mean():.1f}%",
                         ll_model=round(logloss(y[m], pm[m]), 4), ll_dk_refit=round(logloss(y[m], pdk[m]), 4),
                         ll_dk_raw=round(logloss(y[m], praw[m]), 4), brier_model=round(brier(y[m], pm[m]), 4),
                         brier_dk_refit=round(brier(y[m], pdk[m]), 4), brier_dk_raw=round(brier(y[m], praw[m]), 4),
                         model_better=("yes" if logloss(y[m], pm[m]) < logloss(y[m], pdk[m]) else "NO")))
    return rows


def bootstrap_week_diff(items, pm, pdk, n=2000, seed=7):
    """pooled log-loss difference (model - DK refit), and a 90% interval from resampling WEEKS (the honest unit)"""
    wk = np.array([it["week"] for it in items]); y = np.array([it["y"] for it in items])
    ok = ~np.isnan(pm); ws = sorted(set(wk[ok]))
    per = {w: (np.sum(-(y * np.log(np.clip(pm, 1e-6, 1)) + (1 - y) * np.log(np.clip(1 - pm, 1e-6, 1)))[ok & (wk == w)]),
               np.sum(-(y * np.log(np.clip(pdk, 1e-6, 1)) + (1 - y) * np.log(np.clip(1 - pdk, 1e-6, 1)))[ok & (wk == w)]),
               int((ok & (wk == w)).sum())) for w in ws}
    rng = np.random.default_rng(seed); diffs = []
    for _ in range(n):
        s = rng.choice(ws, len(ws)); a = sum(per[w][0] for w in s); b = sum(per[w][1] for w in s); c = sum(per[w][2] for w in s)
        diffs.append((a - b) / c)
    tot = (sum(v[0] for v in per.values()) - sum(v[1] for v in per.values())) / sum(v[2] for v in per.values())
    return tot, float(np.percentile(diffs, 5)), float(np.percentile(diffs, 95))


def reliability(y, p, label):
    bins = [0, .5, .6, .7, .75, .8, .85, .9, 1.01]; rows = []
    y = np.asarray(y); p = np.asarray(p)
    for lo, hi in zip(bins, bins[1:]):
        m = (p >= lo) & (p < hi)
        if m.sum(): rows.append(dict(source=label, bin=f"{lo:.2f}-{min(hi, 1):.2f}", n=int(m.sum()),
                                     predicted=f"{100 * p[m].mean():.1f}%", actual=f"{100 * y[m].mean():.1f}%"))
    return rows


def grade_rows(y, pm, praw):
    g = np.array([grade_of(p) for p in pm]); rows = []
    for gr in ["A+", "A", "A-", "B", "C", "D"]:
        m = g == gr
        if m.sum(): rows.append(dict(grade=gr, n=int(m.sum()), model=f"{100 * pm[m].mean():.1f}%",
                                     dk_novig=f"{100 * praw[m].mean():.1f}%", hit=f"{100 * y[m].mean():.1f}%"))
    return rows


def role_rows(items, pm):
    """for each threshold: how often role-down fires (player/markets with a trend), and its rungs vs model and DK"""
    y = np.array([it["y"] for it in items]); dk = np.array([it["rung"]["novig_pct"] / 100 for it in items])
    pm_ok = ~np.isnan(pm)
    with_trend = [i for i, it in enumerate(items) if it["trend"]]
    pms = {(it["week"], it["slate"], it["row"]["player"], it["row"]["market"]) for it in (items[i] for i in with_trend)}
    rows = []
    for t in THRESHOLDS:
        fired = np.array([bool(it["trend"]) and role_down(it["trend"], t) for it in items]) & pm_ok
        keys = {(it["week"], it["slate"], it["row"]["player"], it["row"]["market"]) for it, f in zip(items, fired) if f}
        n = int(fired.sum())
        rows.append(dict(threshold=f"{int(100 * t)}%", player_markets=f"{len(keys)}/{len(pms)} ({100 * len(keys) / max(len(pms), 1):.1f}%)",
                         rungs=n, hit=f"{100 * y[fired].mean():.1f}%" if n else "-",
                         model=f"{100 * pm[fired].mean():.1f}%" if n else "-", dk=f"{100 * dk[fired].mean():.1f}%" if n else "-",
                         shortfall_vs_model=round(100 * (pm[fired].mean() - y[fired].mean()), 1) if n else None,
                         shortfall_vs_dk=round(100 * (dk[fired].mean() - y[fired].mean()), 1) if n else None,
                         se=round(100 * math.sqrt(max(y[fired].mean() * (1 - y[fired].mean()), 1e-9) / n), 1) if n else None))
    return rows


def coef_rows(model):
    return sorted([dict(feature=c, coef_per_sd=round(b, 3), mean=round(mu, 3), sd=round(sd, 3))
                   for c, b, mu, sd in zip(model["cols"], model["b"][1:], model["mu"], model["sd"])],
                  key=lambda r: -abs(r["coef_per_sd"])) + [dict(feature="(intercept)", coef_per_sd=round(model["b"][0], 3))]


# ── retro ───────────────────────────────────────────────────────────────────────────────────────────────────────────
def repo_root():
    return os.path.dirname(os.path.dirname(P("cards")))


def publish_commit(season, week, slate):
    """the commit that last set the card's tickets before kickoff: newest commit touching the card file whose subject is
    not an odds refresh (refreshes only move prices), committed before the slate's first kickoff"""
    rel = f"automation/cards/card_{season}_w{week}_{slate}.json"; ko = first_kickoff(season, week, slate)
    out = subprocess.check_output(["git", "-C", repo_root(), "log", "--format=%H|%cI|%s", "--", rel], text=True)
    for line in out.splitlines():
        sha, at, subj = line.split("|", 2)
        if "odds refresh" in subj: continue
        if ko is None or pd.Timestamp(at) < ko: return sha, at, subj
    return None


def git_file(sha, rel):
    try: return subprocess.check_output(["git", "-C", repo_root(), "show", f"{sha}:{rel}"], stderr=subprocess.DEVNULL)
    except subprocess.CalledProcessError: return None


def score_card(card, act):
    """[(result, units)] per ticket: every leg clears = WIN at the card's estimated payout, any miss = LOSS, else VOID"""
    out = []
    for t in card["tickets"]:
        hits = []
        for l in t["legs"]:
            v = act.get((norm_name(l["player"]), l["market"]))
            hits.append(None if v is None or (isinstance(v, float) and math.isnan(v)) else v >= l["rung"])
        if any(h is False for h in hits): out.append(("LOSS", -1.0))
        elif all(h is True for h in hits): out.append(("WIN", round(t["est_payout"] - 1, 2)))
        else: out.append(("VOID", 0.0))
    return out


def retro_slate(season, week, slate, models, act, data=None):
    """{slug: card} rebuilt from the publish commit's files (live = the committed card itself)"""
    pc = publish_commit(season, week, slate)
    if pc is None: return None, None
    sha = pc[0]; fmt = dict(s=season, w=week, sl=slate)
    tmp = tempfile.mkdtemp(prefix="calib_retro_")
    try:
        for x in INPUTS:
            raw = git_file(sha, "automation/" + x.format(**fmt))
            if raw is None: continue
            dst = os.path.join(tmp, x.format(**fmt)); os.makedirs(os.path.dirname(dst), exist_ok=True)
            open(dst, "wb").write(raw)
        legs = os.path.join(tmp, "cards", f"legs_{season}_w{week}_{slate}.json")
        if data is not None and os.path.exists(legs):   # role-down flags (R13) the board would have carried: weeks < N
            d = json.load(open(legs, encoding="utf-8"))
            calib.annotate_roles(d["players"], data, week)
            json.dump(d, open(legs, "w", encoding="utf-8"))
        os.makedirs(os.path.join(tmp, "models"), exist_ok=True)
        json.dump(models[week], open(os.path.join(tmp, "models", f"calib_{season}_w{week}.json"), "w"))
        cards = {}
        live = os.path.join(tmp, "cards", f"card_{season}_w{week}_{slate}.json")
        if os.path.exists(live): cards["live"] = json.load(open(live, encoding="utf-8"))
        env = dict(os.environ, EDGE_ROOT=tmp, PYTHONIOENCODING="utf-8")
        pipe = os.path.dirname(os.path.abspath(__file__))
        for slug in RETRO_SLUGS:
            r = subprocess.run([sys.executable, os.path.join(pipe, "build_card_json.py"), "--season", str(season), "--week",
                                str(week), "--slate", slate, "--shadow", slug], env=env, capture_output=True, text=True)
            f = os.path.join(tmp, "cards", "shadow", f"card_{season}_w{week}_{slate}_{slug}.json")
            cards[slug] = json.load(open(f, encoding="utf-8")) if r.returncode == 0 and os.path.exists(f) else None
            if r.returncode: print(f"  w{week} {slate} {slug} failed: {r.stderr.strip().splitlines()[-1:]}", file=sys.stderr)
        return pc, cards
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def retro(season, weeks, items, data):
    """per slate x variant records + the role-down fires on calib cards"""
    labelled = sorted({it["week"] for it in items})
    models = {}
    for w in weeks:                                   # leave-that-week-out (the request); w8 = weeks 3-7 = walk-forward
        tr = [it for it in items if it["week"] != w]
        models[w] = fit(matrix(tr, FEATS), [it["y"] for it in tr], cols=FEATS)
        models[w].update(trained_on="all labelled weeks except %d (%s)" % (w, ",".join(str(x) for x in labelled if x != w)),
                         role_down=calib.ROLE_DOWN)
    rows, tickets = [], []
    for w in weeks:
        act = calib.labels_for(data, w)
        for sl in ("tnf", "sun", "mnf"):
            if not os.path.exists(P("cards", f"card_{season}_w{w}_{sl}.json")): continue
            legs = P("cards", f"legs_{season}_w{w}_{sl}.json")
            if not (os.path.exists(legs) and any(p.get("settled") for p in json.load(open(legs, encoding="utf-8"))["players"])):
                continue                                  # not played yet: nothing to grade
            pc, cards = retro_slate(season, w, sl, models, act, data)
            if not cards: continue
            for slug in ["live"] + RETRO_SLUGS:
                c = cards.get(slug)
                if c is None: rows.append(dict(slate=f"w{w} {sl}", variant=slug, tickets="failed")); continue
                sc = score_card(c, act)
                rows.append(dict(slate=f"w{w} {sl}", variant=slug, commit=pc[0][:8], tickets=len(sc),
                                 W=sum(r == "WIN" for r, _ in sc), L=sum(r == "LOSS" for r, _ in sc),
                                 V=sum(r == "VOID" for r, _ in sc), units=round(sum(u for _, u in sc), 2),
                                 role_down_cands=sum(bool(x.get("role_down")) for x in c.get("candidates", [])) if slug == "calib" else None))
                for t, (res, u) in zip(c["tickets"], sc):
                    tickets.append(dict(slate=f"w{w} {sl}", variant=slug, ticket=t["name"], result=res, units=u,
                                        payout=f"{t['est_american']:+d}", model=t.get("model_hit"),
                                        legs=" / ".join(f"{l['player']} {l['rung']:g}+ {l['market']} ({l['odds_est']:+d})" for l in t["legs"])))
    return rows, tickets


def summary(rows):
    acc = {}
    for r in rows:
        if r.get("tickets") == "failed": continue
        a = acc.setdefault(r["variant"], dict(variant=r["variant"], slates=0, tickets=0, W=0, L=0, V=0, units=0.0, no_ticket=0))
        a["slates"] += 1; a["tickets"] += r["tickets"]; a["W"] += r["W"]; a["L"] += r["L"]; a["V"] += r["V"]
        a["units"] = round(a["units"] + r["units"], 2); a["no_ticket"] += r["tickets"] == 0
    for a in acc.values():
        a["record"] = f"{a['W']}-{a['L']}" + (f"-{a['V']}" if a["V"] else "")
        a["roi"] = f"{100 * a['units'] / max(a['W'] + a['L'], 1):+.1f}%"
    return list(acc.values())


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--season", type=int, required=True); ap.add_argument("--weeks", default="3-8")
    ap.add_argument("--retro", default=None, help="weeks to retro-build, e.g. 4-8"); ap.add_argument("--out", default=None)
    a = ap.parse_args()
    lo, hi = map(int, a.weeks.split("-")); weeks = list(range(lo, hi + 1))
    data = Data(a.season)
    items, sources = training_items(a.season, weeks, data)
    lw = sorted({it["week"] for it in items}); y = np.array([it["y"] for it in items])
    pm, praw, pdk = lowo(items, lw)
    wm, _, wdk = lowo(items, lw, walk_forward=True)
    d, d5, d95 = bootstrap_week_diff(items, pm, pdk)
    beats = d < 0
    md = ["# Calibration study, %d (SHADOW ONLY, not live)" % a.season, "",
          "Research report: nothing here changes the live card, the Legs board, the record or the newsletter.", "",
          "## Verdict", ""]
    full = fit(matrix(items, FEATS), y, cols=FEATS)
    m_ll, dk_ll = logloss(y, pm), logloss(y, pdk)
    md += [("**calib does NOT beat the DK-only baseline.** " if not beats else "**calib beats the DK-only baseline, narrowly.** ")
           + f"Leave-one-week-out pooled log loss {m_ll:.4f} (model) vs {dk_ll:.4f} (DK no-vig, refit) vs "
             f"{logloss(y, praw):.4f} (DK no-vig, raw); difference {d:+.4f} per rung, 90% week-bootstrap interval "
             f"[{d5:+.4f}, {d95:+.4f}]. Brier {brier(y, pm):.4f} vs {brier(y, pdk):.4f} (refit) vs {brier(y, praw):.4f} (raw).", ""]
    wok = ~np.isnan(wm)
    md += [f"Walk-forward (train on earlier weeks only, the version a live card could have used; weeks "
           f"{', '.join(str(w) for w in sorted({it['week'] for it, k in zip(items, wok) if k}))}): log loss "
           f"{logloss(y[wok], wm[wok]):.4f} model vs {logloss(y[wok], wdk[wok]):.4f} DK refit vs {logloss(y[wok], praw[wok]):.4f} DK raw.", ""]
    md += ["## Data", "",
           f"{len(items)} settled, priced rungs from the pregame Legs boards, weeks {lw[0]}-{lw[-1]} (week 1-2 have no boards; "
           "week 8 has TNF only so far). Base hit rate %.1f%%. Voids (no box-score row) dropped. Held rows have no price "
           "on the board and aren't in the data." % (100 * y.mean()), "",
           "Board version used per slate (last generated before the slate's first kickoff; 'working file' = the current "
           "file qualifies; a sha = an older git version, because the current file was regenerated after kickoff):", "",
           table([dict(slate=f"w{k[0]} {k[1]}", source=v) for k, v in sorted(sources.items())], ["slate", "source"]),
           "Role trend needs 4+ current-season games (last 2 vs up to 4 before); %.0f%% of rungs have none (mostly weeks 3-4) "
           "and get a missing indicator." % (100 * np.mean([it["f"]["role_na"] for it in items])), "",
           "## Model vs DK, leave-one-week-out", "",
           table(metrics_rows(items, pm, praw, pdk, lw), ["week", "rungs", "hit", "ll_model", "ll_dk_refit", "ll_dk_raw",
                                                           "brier_model", "brier_dk_refit", "brier_dk_raw", "model_better"]),
           "L2 sensitivity (pooled LOWO log loss; the model uses lambda = %g):" % calib.LAMBDA, ""]
    sens = []
    for lam in LAMBDAS:
        p1, _, p2 = lowo(items, lw, lam)
        sens.append(dict(lam=lam, ll_model=round(logloss(y, p1), 4), ll_dk_refit=round(logloss(y, p2), 4)))
    abl = []
    for name, fs in [("DK only", ["novig"]), ("DK + L10/L15", ["novig", "l10", "l15"]),
                     ("DK + market/position", ["novig"] + [c for c in FEATS if c.startswith(("m_", "pos_"))]),
                     ("DK + role trend + flags", ["novig", "snap_delta", "tgt_logratio", "car_logratio", "role_na", "inj_watch", "qb_change"]),
                     ("full model", FEATS)]:
        p1, _, _ = lowo(items, lw, feats=fs)
        abl.append(dict(features=name, ll=round(logloss(y, p1), 4), brier=round(brier(y, p1), 4)))
    md += [table(sens, ["lam", "ll_model", "ll_dk_refit"]),
           "Feature groups added to DK alone (pooled LOWO; diagnostic only, not used to pick the model):", "",
           table(abl, ["features", "ll", "brier"]),
           "## Reliability (pooled, out-of-week)", "",
           table(reliability(y, pm, "model") + reliability(y, pdk, "DK refit") + reliability(y, praw, "DK raw"),
                 ["source", "bin", "n", "predicted", "actual"]),
           "## Hit rate by calib grade (out-of-week)", "",
           "A+ >= .85, A >= .80, A- >= .75, B >= .68, C >= .60, D below.", "",
           table(grade_rows(y, pm, praw), ["grade", "n", "model", "dk_novig", "hit"]),
           "## Coefficients (fit on every labelled week; per standard deviation of the feature)", "",
           table(coef_rows(full), ["feature", "coef_per_sd", "mean", "sd"]),
           "## Role down: threshold study (out-of-week model predictions)", "",
           "Fires when, for snap share or the market's volume (targets / carries), BOTH of the last two games are below the "
           "prior-games average by more than the threshold (relative; prior role at least 20% snaps / 2 per game). "
           "shortfall = model minus actual on the flagged rungs (positive = they hit less than predicted).", "",
           table(role_rows(items, pm), ["threshold", "player_markets", "rungs", "hit", "model", "dk", "shortfall_vs_model",
                                                    "shortfall_vs_dk", "se"]),
           f"calib uses threshold {int(100 * calib.ROLE_DOWN)}% (calib.ROLE_DOWN): the only one where flagged rungs hit below "
           "both the model and DK. It was picked after looking at this table (6 thresholds tried, ~1 SE), so treat it as a "
           "hypothesis (CLAUDE.md rule 5).", ""]
    if a.retro:
        rlo, rhi = map(int, a.retro.split("-"))
        rows, tix = retro(a.season, list(range(rlo, rhi + 1)), items, data)
        md += ["## Retro cards, weeks %d-%d, played slates (IN-SAMPLE for calib's fit choices)" % (rlo, rhi), "",
               "Each slate rebuilt offline from the files at its card's publish commit (no odds pull). live = the card as "
               "published. calib uses a model fit with that week left out (so weeks 4-7 are scored by a model that saw later "
               "weeks; week 8's model is weeks 3-7 only, the walk-forward one). Every card scored the same way: all legs "
               "clear = win at the card's estimated payout, any miss = loss (receipts use real closing prices; these won't "
               "match the record to the cent).", "",
               table(summary(rows), ["variant", "slates", "tickets", "no_ticket", "record", "units", "roi"]),
               "### By slate", "",
               table(rows, ["slate", "variant", "commit", "tickets", "W", "L", "V", "units", "role_down_cands"]),
               "### Tickets", "",
               table(tix, ["slate", "variant", "ticket", "result", "units", "payout", "model", "legs"])]
    txt = "\n".join(md)
    if a.out: open(P(a.out) if not os.path.isabs(a.out) else a.out, "w", encoding="utf-8").write(txt); print(f"wrote {a.out}")
    else: print(txt)


if __name__ == "__main__":
    main()
