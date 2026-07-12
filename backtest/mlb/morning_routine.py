# -*- coding: utf-8 -*-
"""
Edge Index — Morning Routine Agent
Pulls lines, runs models, updates MLBHub + RecordTracker, builds and deploys.

Usage:
  python morning_routine.py                    # run pipeline only
  python morning_routine.py --build            # pipeline + build app
  python morning_routine.py --deploy           # pipeline + build + deploy

Schedule with Windows Task Scheduler:
  Program:   python
  Arguments: C:/Users/tyose/edge-index/agent/morning_routine.py --deploy
  Start in:  C:/Users/tyose/edge-index/agent
  Trigger:   Daily 8:30 AM (after morning lines are posted)
"""
import os, sys, json, subprocess, re, argparse
from datetime import date, datetime, timedelta

# Force UTF-8 everywhere. Under Task Scheduler the console defaults to cp1252,
# which crashes on ✓ / emoji / accented names (Martín Pérez, Jesús Luzardo).
os.environ["PYTHONUTF8"] = "1"
os.environ["PYTHONIOENCODING"] = "utf-8"
try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

BASE    = r"C:\Users\tyose\edge-index"
MLB_DIR = os.path.join(BASE, "backtest", "mlb")
APP_SRC = os.path.join(BASE, "cfb-app", "src")
APP_DIR = os.path.join(BASE, "cfb-app")
LOG_DIR = os.path.join(BASE, "agent", "logs")
TODAY   = date.today().isoformat()
YEST    = (date.today() - timedelta(days=1)).isoformat()

os.makedirs(LOG_DIR, exist_ok=True)
LOG_FILE = os.path.join(LOG_DIR, f"routine_{TODAY}.log")

def log(msg):
    ts = datetime.now().strftime("%H:%M:%S")
    line = f"[{ts}] {msg}"
    try:
        print(line)
    except Exception:
        print(line.encode("ascii", "replace").decode("ascii"))
    try:
        with open(LOG_FILE, 'a', encoding='utf-8', errors='replace') as f:
            f.write(line + "\n")
    except Exception:
        pass  # logging must never crash the routine

def run(cmd, cwd=None, label="", required=False):
    log(f"  >> {label or cmd[:70]}")
    env = dict(os.environ, PYTHONUTF8="1", PYTHONIOENCODING="utf-8")
    try:
        r = subprocess.run(cmd, shell=True, cwd=cwd or MLB_DIR,
                           capture_output=True, text=True,
                           encoding="utf-8", errors="replace", env=env)
    except Exception as e:
        log(f"     ERR launching step: {e}")
        if required:
            log(f"  ✗ REQUIRED step failed — aborting")
            sys.exit(1)
        return False
    for line in (r.stdout or "").strip().split("\n")[-10:]:
        if line.strip():
            log(f"     {line}")
    if r.returncode != 0:
        if r.stderr:
            log(f"     ERR: {r.stderr[:200]}")
        if required:
            log(f"  ✗ REQUIRED step failed — aborting")
            sys.exit(1)
        return False
    return True

def step(n, title):
    log(f"\n{'='*60}\nSTEP {n}: {title}\n{'='*60}")

# ── STEP 1: Grade yesterday ────────────────────────────────────
def grade_yesterday():
    step(1, f"Grade yesterday ({YEST})")
    run(f"python mlb_results_checker.py", label="results checker")
    # Grade — posted_plays must already exist from yesterday
    ok = run(f"python mlb_grade_patch.py --grade {YEST}", label="grade patch")
    if not ok:
        log(f"  WARN Grade failed — posted card may not exist for {YEST}")
    return ok

# ── STEP 2: Roster maintenance ────────────────────────────────
def roster_maintenance():
    step(2, "Roster + trade maintenance")
    run("python mlb_trade_tracker.py --update",  label="trade tracker")
    run("python mlb_roster_verify.py --fix",      label="roster verify")

# ── STEP 3: Pull today's lines ────────────────────────────────
def pull_lines():
    step(3, f"Pull today's lines ({TODAY})")
    ok = run("python mlb_odds_puller.py", label="odds puller", required=True)
    path = os.path.join(MLB_DIR, f"mlb_lines_{TODAY}.json")
    if os.path.exists(path):
        d = json.load(open(path))
        log(f"  ✓ {len(d.get('props',[]))} props · {len(d.get('run_lines',[]))} run lines · {len(d.get('games',[]))} games")
    return ok

# ── STEP 4: Run stat caches ────────────────────────────────────
def run_caches():
    step(4, "Update stat caches")
    run(f"python mlb_current_stats.py --update-cache --date {TODAY}", label="current stats")
    run(f"python mlb_savant.py --update-cache --date {TODAY}",        label="savant cache")
    run(f"python mlb_pitcher_hand.py --date {TODAY}",                 label="pitcher hands")

# ── STEP 5: Run models ────────────────────────────────────────
def run_models():
    step(5, "Run models")
    run(f"python mlb_run_today.py --date {TODAY}",       label="run today (props)")
    run(f"python mlb_pitcher_under.py --date {TODAY}",   label="pitcher K unders")
    run(f"python mlb_umpire.py --date {TODAY}",          label="umpire assignments")
    run(f"python mlb_team_rl.py --date {TODAY}",         label="team run lines")
    run(f"python mlb_power_score.py --date {TODAY}",     label="power score")
    run(f"python mlb_parlay_builder.py --date {TODAY} --no-parlays --max-plays 7",
        label="parlay builder")

# ── STEP 6: Update MLBHub ─────────────────────────────────────
def update_hub():
    step(6, "Update MLBHub.jsx")
    # Load today's plays
    plays_path = os.path.join(MLB_DIR, f"mlb_plays_{TODAY}.json")
    rl_path    = os.path.join(MLB_DIR, f"mlb_team_rl_{TODAY}.json")
    power_path = os.path.join(MLB_DIR, f"mlb_power_{TODAY}.json")

    if not os.path.exists(plays_path):
        log("  ✗ mlb_plays file not found — skipping hub update")
        return False

    plays  = json.load(open(plays_path))
    rl     = json.load(open(rl_path))    if os.path.exists(rl_path)    else {}
    power  = json.load(open(power_path)) if os.path.exists(power_path) else {}

    hub = os.path.join(APP_SRC, "MLBHub.jsx")
    if not os.path.exists(hub):
        log(f"  ✗ MLBHub.jsx not found at {hub}")
        return False

    content = open(hub, encoding='utf-8').read()

    # Update TODAY date
    content = re.sub(r'const TODAY = "[^"]+";', f'const TODAY = "{TODAY}";', content)

    # Update version comment to force new deploy hash
    content = re.sub(r'// v\d{4}-\d{2}-\d{2}', f'// v{TODAY}', content)

    # ── Build PITCHER_PLAYS ──────────────────────────────────
    pp = [p for p in plays.get('pitcher_plays', [])
          if p and p.get('tier') in ('AUTO','T1')]
    pitcher_lines = []
    for p in pp[:4]:
        prop_label = "strikeouts" if p['prop'] == 'strikeouts' else p['prop']
        notes = p.get('notes', [f"L5 avg {p.get('l5_avg','?')} Ks"])
        notes_js = '[' + ','.join(f'"{n}"' for n in notes[:5]) + ']'
        alts = p.get('alt_lines', [])
        alts_js = '[' + ','.join(str(a) for a in alts[:2]) + ']'
        pitcher_lines.append(
            f'  {{pitcher:"{p["player"]}",team:"{p.get("team","?")}",opp:"{p.get("opp","?")}",home:"{p.get("home","?")}",\n'
            f'   prop:"{prop_label}",line:{p["line"]},odds:{p["odds"]},tier:"{p["tier"]}",model_prob:{p["model_prob"]},\n'
            f'   streak:{p.get("streak",0)},l5_avg:{p.get("l5_avg",0)},k_per_ip:{p.get("k_per_ip",0)},opp_k_pct:{p.get("opp_k_pct",0.22)},\n'
            f'   alt_lines:{alts_js},hand:"{p.get("hand","R")}",notes:{notes_js}}},'
        )
    if pitcher_lines:
        new_pp = 'const PITCHER_PLAYS = [\n' + '\n'.join(pitcher_lines) + '\n];'
        content = re.sub(r'const PITCHER_PLAYS = \[.*?\];', new_pp, content, flags=re.DOTALL)
        log(f"  ✓ {len(pitcher_lines)} pitcher plays written")

    # ── Build BATTER_PLAYS ───────────────────────────────────
    bp = [p for p in plays.get('batter_plays', [])
          if p and p.get('tier') in ('AUTO','T1')]
    # Filter to -150 or better odds
    bp_singles = [p for p in bp if p.get('odds', -999) >= -150][:5]
    batter_lines = []
    for p in bp_singles:
        notes = p.get('notes', [f"{p.get('streak',0)}-game hit streak"])
        notes_js = '[' + ','.join(f'"{n}"' for n in notes[:5]) + ']'
        batter_lines.append(
            f'  {{batter:"{p["player"]}",team:"{p.get("team","?")}",opp:"{p.get("opp","?")}",home:"{p.get("home","?")}",\n'
            f'   prop:"hits",line:0.5,odds:{p["odds"]},tier:"{p["tier"]}",model_prob:{p["model_prob"]},\n'
            f'   hit_streak:{p.get("streak",0)},pitcher_hand:"{p.get("pitcher_hand","R")}",\n'
            f'   xba:null,xba_diff:null,xwoba:null,vs_team:null,notes:{notes_js}}},'
        )
    if batter_lines:
        new_bp = 'const BATTER_PLAYS = [\n' + '\n'.join(batter_lines) + '\n];'
        content = re.sub(r'const BATTER_PLAYS = \[.*?\];', new_bp, content, flags=re.DOTALL)
        log(f"  ✓ {len(batter_lines)} batter plays written")

    # ── Build FADE_PLAYS from current stats ──────────────────
    fade_path = os.path.join(MLB_DIR, f"mlb_plays_{TODAY}.json")
    if os.path.exists(fade_path):
        fade_data = json.load(open(fade_path))
        fades = fade_data.get('fade_plays', [])
        # Tier 1 only: below .100
        t1_fades = [f for f in fades if float(f.get('l14_avg',1)) < 0.100][:6]
        if t1_fades:
            fade_lines = []
            for f in t1_fades:
                fade_lines.append(
                    f'  {{batter:"{f["player"]}",team:"{f.get("team","?")}",opp:"{f.get("opp","?")}",\n'
                    f'   l14_avg:"{f.get("l14_str","?")}",l14:"{f.get("l14_label","?")}",\n'
                    f'   odds_over:{f.get("odds_over",0)},odds_under:{f.get("odds_under",0)},\n'
                    f'   reason:"{f.get("reason","Cold bat")}"}}, '
                )
            new_fades = 'const FADE_PLAYS = [\n' + '\n'.join(fade_lines) + '\n];'
            content = re.sub(r'const FADE_PLAYS = \[.*?\];', new_fades, content, flags=re.DOTALL)
            log(f"  ✓ {len(t1_fades)} fade plays written")

    # ── Update RL plays ──────────────────────────────────────
    hot  = rl.get('hot_plays',  [])
    cold = rl.get('cold_plays', [])
    log(f"  RL: {len(hot)} hot · {len(cold)} cold qualifying plays")

    open(hub, 'w', encoding='utf-8').write(content)
    log(f"  ✓ MLBHub.jsx updated")
    return True

# ── STEP 6.5: Regenerate RecordTracker.jsx from posted cards ──
def update_record_tracker():
    step("6.5", "Regenerate RecordTracker.jsx")
    gen = os.path.join(MLB_DIR, "generate_record_data.py")
    cards_dir = os.path.join(MLB_DIR, "posted_cards")
    target = os.path.join(APP_SRC, "RecordTracker.jsx")
    if not os.path.exists(gen):
        log(f"  ✗ generator not found at {gen} — skipping")
        return False
    if not os.path.exists(target):
        log(f"  ✗ RecordTracker.jsx not found at {target} — skipping")
        return False
    ok = run(
        f'python "{gen}" --cards-dir "{cards_dir}" --inject "{target}"',
        label="generate record data"
    )
    if ok:
        log("  ✓ RecordTracker.jsx regenerated from posted cards")
    else:
        log("  ⚠ RecordTracker regen failed — record may be stale")
    return ok

# ── STEP 7: Build app ─────────────────────────────────────────
def build_app():
    step(7, "Build React app")
    ok = run("npm run build", cwd=APP_DIR, label="npm run build")
    if ok:
        log("  ✓ Build complete → dist/")
    else:
        log("  ✗ Build failed — check for JSX errors")
    return ok

# ── STEP 8: Deploy ────────────────────────────────────────────
def deploy():
    step(8, "Deploy to Cloudflare Pages")
    ok = run(
        "npx wrangler pages deploy dist --project-name=edge-index --commit-dirty=true",
        cwd=APP_DIR, label="wrangler deploy"
    )
    if ok:
        log("  ✓ Live at https://www.edge-index.com")
    else:
        log("  ✗ Deploy failed")
    return ok

# ── STEP 9: Log posted card ───────────────────────────────────
def log_posted_card(plays_str, fades_str):
    step(9, f"Log posted card for {TODAY}")
    if not plays_str or not fades_str:
        log("  ⚠ No plays/fades provided — skipping card log")
        log("  Run manually: python mlb_posted_plays.py --date " + TODAY + " --plays '...' --fades '...'")
        return False
    ok = run(
        f'python mlb_posted_plays.py --date {TODAY} --plays "{plays_str}" --fades "{fades_str}"',
        label="log posted card"
    )
    return ok

# ── SUMMARY ───────────────────────────────────────────────────
def summary():
    step(9, "Summary")
    plays_path = os.path.join(MLB_DIR, f"mlb_plays_{TODAY}.json")
    rl_path    = os.path.join(MLB_DIR, f"mlb_team_rl_{TODAY}.json")
    if os.path.exists(plays_path):
        d = json.load(open(plays_path))
        pp = [p for p in d.get('pitcher_plays',[]) if p and p.get('tier') in ('AUTO','T1')]
        bp = [p for p in d.get('batter_plays',[])  if p and p.get('tier') in ('AUTO','T1')]
        log(f"\n  Pitchers: {len(pp)} qualifying  |  Batters: {len(bp)} qualifying")
        for p in (pp+bp)[:8]:
            name = p.get('player','?')
            prop = "K" if p.get('prop')=='strikeouts' else "H"
            log(f"  {p.get('tier','?'):5} {name:26} {prop} OVER {p.get('line','?')} ({p.get('odds','?'):+}) {p.get('model_prob',0)*100:.0f}%")
    if os.path.exists(rl_path):
        rl = json.load(open(rl_path))
        hot  = rl.get('hot_plays',  [])
        cold = rl.get('cold_plays', [])
        if hot or cold:
            log(f"\n  Run Lines:")
            for p in hot:
                log(f"  HOT {p['team']:28} -1.5  {p['odds']}  Score:{p['score']:+.2f}")
            for p in cold:
                log(f"  CLD {p['team']:28} +1.5  +{p['odds']}  Score:{p['score']:+.2f}")
    log(f"\n  Log: {LOG_FILE}")
    log(f"\n  ⚠ Card NOT auto-posted — review plays then run:")
    log(f"  python mlb_posted_plays.py --date {TODAY} --plays '...' --fades '...'")

def safe(fn, *a, **k):
    """Run a phase; if it throws, log and continue. Keeps one bad step from
    killing the whole unattended morning run."""
    try:
        return fn(*a, **k)
    except SystemExit:
        raise  # honor required-step aborts
    except Exception as e:
        import traceback
        log(f"  ✗ {fn.__name__} crashed: {e}")
        log(f"     {traceback.format_exc()[:300]}")
        return False

# ── MAIN ──────────────────────────────────────────────────────
if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--build",  action="store_true", help="Build app after pipeline")
    parser.add_argument("--deploy", action="store_true", help="Build + deploy after pipeline")
    parser.add_argument("--skip-grade",  action="store_true", help="Skip grading yesterday")
    parser.add_argument("--skip-cache",  action="store_true", help="Skip stat cache updates")
    args = parser.parse_args()

    log(f"\nEDGE INDEX MORNING ROUTINE — {TODAY}")
    log(f"{'='*60}")

    if not args.skip_grade:
        safe(grade_yesterday)

    safe(roster_maintenance)
    pull_lines()  # required-gated internally; its sys.exit still aborts on no lines

    if not args.skip_cache:
        safe(run_caches)

    safe(run_models)
    safe(update_hub)
    safe(update_record_tracker)

    if args.build or args.deploy:
        built = safe(build_app)
        if built and args.deploy:
            safe(deploy)

    safe(summary)
    log(f"\n✓ Done — {datetime.now().strftime('%H:%M:%S')}")
