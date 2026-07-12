"""
Edge Index — Play Logger
Saves every suggested play to a master CSV at time of suggestion.
This is the immutable audit trail — never edit, only append.

Usage:
  python mlb_log_plays.py --date 2026-05-09
  python mlb_log_plays.py --date 2026-05-09 --result   (add results)
  python mlb_log_plays.py --summary                    (show record)
"""
import os, sys, csv, json, argparse
from datetime import date, datetime

BASE_DIR  = os.path.dirname(os.path.abspath(__file__))
LOG_FILE  = os.path.join(BASE_DIR, "edge_index_plays.csv")
PARLAY_LOG = os.path.join(BASE_DIR, "edge_index_parlays.csv")

PLAY_FIELDS = [
    "date","sport","player","prop","line","odds","tier",
    "model_prob","streak","l5","l10","game",
    "logged_at","result","actual","void","notes"
]

PARLAY_FIELDS = [
    "date","sport","parlay_id","legs","odds","hit_prob","ev",
    "logged_at","result","pnl_100"
]

def init_logs():
    """Create CSV files with headers if they don't exist."""
    if not os.path.exists(LOG_FILE):
        with open(LOG_FILE, 'w', newline='') as f:
            csv.DictWriter(f, fieldnames=PLAY_FIELDS).writeheader()
        print(f"Created {LOG_FILE}")

    if not os.path.exists(PARLAY_LOG):
        with open(PARLAY_LOG, 'w', newline='') as f:
            csv.DictWriter(f, fieldnames=PARLAY_FIELDS).writeheader()
        print(f"Created {PARLAY_LOG}")

def log_plays_from_json(game_date, sport="MLB"):
    """
    Load today's plays JSON and append to master CSV.
    Only logs plays not already in the CSV for this date.
    """
    plays_path = os.path.join(BASE_DIR, f"mlb_plays_{game_date}.json")
    if not os.path.exists(plays_path):
        print(f"No plays file: {plays_path}")
        return

    with open(plays_path) as f:
        data = json.load(f)

    # Check what's already logged for this date
    existing = set()
    if os.path.exists(LOG_FILE):
        with open(LOG_FILE, 'r') as f:
            for row in csv.DictReader(f):
                if row['date'] == game_date:
                    existing.add(f"{row['player']}|{row['prop']}|{row['line']}")

    new_plays = []
    all_plays = (
        data.get('pitcher_plays', []) +
        data.get('batter_plays', [])
    )

    for p in all_plays:
        if not p or p.get('tier') == 'SKIP':
            continue

        player = p.get('player', p.get('pitcher', p.get('batter', '')))
        prop   = p.get('prop', '')
        line   = p.get('line', '')
        key    = f"{player}|{prop}|{line}"

        if key in existing:
            continue

        prop_label = {
            'strikeouts':   'K',
            'hits':         'H',
            'total_bases':  'TB',
            'home_runs':    'HR',
        }.get(prop, prop.upper()[:2])

        game = f"{p.get('home','?')}"

        row = {
            'date':       game_date,
            'sport':      sport,
            'player':     player,
            'prop':       f"{prop_label} OVER {line}",
            'line':       line,
            'odds':       p.get('odds', ''),
            'tier':       p.get('tier', ''),
            'model_prob': p.get('model_prob', ''),
            'streak':     p.get('streak', ''),
            'l5':         p.get('l5', ''),
            'l10':        p.get('l10', ''),
            'game':       game,
            'logged_at':  datetime.now().strftime('%Y-%m-%d %H:%M'),
            'result':     '',
            'actual':     '',
            'void':       '',
            'notes':      '',
        }
        new_plays.append(row)

    if new_plays:
        with open(LOG_FILE, 'a', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=PLAY_FIELDS)
            writer.writerows(new_plays)
        print(f"Logged {len(new_plays)} new plays for {game_date}")
    else:
        print(f"No new plays to log for {game_date}")

    return new_plays

def log_parlays_from_json(game_date, sport="MLB"):
    """Log today's parlays to the parlay CSV."""
    parlays_path = os.path.join(BASE_DIR, f"mlb_plays_{game_date}.json")
    if not os.path.exists(parlays_path):
        return

    # Check existing
    existing = set()
    if os.path.exists(PARLAY_LOG):
        with open(PARLAY_LOG, 'r') as f:
            for row in csv.DictReader(f):
                if row['date'] == game_date:
                    existing.add(row['parlay_id'])

    # Load parlay builder output if exists
    builder_path = os.path.join(BASE_DIR, f"mlb_parlays_{game_date}.json")

    rows = []
    if os.path.exists(builder_path):
        with open(builder_path) as f:
            parlays = json.load(f)
        for i, p in enumerate(parlays, 1):
            pid = f"{game_date}_P{i}"
            if pid in existing:
                continue
            legs_str = " + ".join([
                f"{l['player']} {l['prop']} ({l['odds']:+})"
                for l in p.get('legs', [])
            ])
            rows.append({
                'date':       game_date,
                'sport':      sport,
                'parlay_id':  pid,
                'legs':       legs_str,
                'odds':       p.get('odds', ''),
                'hit_prob':   p.get('hit_prob', ''),
                'ev':         p.get('ev', ''),
                'logged_at':  datetime.now().strftime('%Y-%m-%d %H:%M'),
                'result':     '',
                'pnl_100':    '',
            })

    if rows:
        with open(PARLAY_LOG, 'a', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=PARLAY_FIELDS)
            writer.writerows(rows)
        print(f"Logged {len(rows)} parlays for {game_date}")

def update_results(game_date):
    """Interactive result entry for a given date."""
    rows = []
    updated = 0

    with open(LOG_FILE, 'r') as f:
        rows = list(csv.DictReader(f))

    print(f"\nEntering results for {game_date}")
    print("Commands: hit/h, miss/m, void/v, skip/s (enter to skip)")
    print("─" * 55)

    for row in rows:
        if row['date'] != game_date or row['result']:
            continue

        print(f"\n{row['player']} {row['prop']} ({row['odds']}) [{row['tier']}]")
        result = input("Result [h/m/v/s]: ").strip().lower()

        if result in ('h', 'hit'):
            actual = input("Actual value: ").strip()
            row['result'] = 'HIT'
            row['actual'] = actual
            updated += 1
        elif result in ('m', 'miss'):
            actual = input("Actual value: ").strip()
            row['result'] = 'MISS'
            row['actual'] = actual
            updated += 1
        elif result in ('v', 'void'):
            row['result'] = 'VOID'
            row['void']   = 'postponed/cancelled'
            updated += 1
        else:
            continue

    with open(LOG_FILE, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=PLAY_FIELDS)
        writer.writeheader()
        writer.writerows(rows)

    print(f"\nUpdated {updated} plays")

def show_summary():
    """Print running record from CSV."""
    if not os.path.exists(LOG_FILE):
        print("No play log found")
        return

    with open(LOG_FILE, 'r') as f:
        rows = [r for r in csv.DictReader(f) if r['result']]

    if not rows:
        print("No results logged yet")
        return

    hits   = [r for r in rows if r['result'] == 'HIT']
    misses = [r for r in rows if r['result'] == 'MISS']
    voids  = [r for r in rows if r['result'] == 'VOID']
    settled = hits + misses

    def pnl(plays):
        total = 0
        for p in plays:
            odds = int(p['odds']) if p['odds'] else -110
            if p['result'] == 'HIT':
                total += 100*(100/abs(odds)) if odds < 0 else 100*(odds/100)
            elif p['result'] == 'MISS':
                total -= 100
        return total

    print(f"\n{'='*55}")
    print(f"EDGE INDEX — ALL-TIME RECORD")
    print(f"{'='*55}")
    print(f"Total plays:  {len(settled)} settled, {len(voids)} voided")
    rate = len(hits)/len(settled) if settled else 0
    print(f"Record:       {len(hits)}-{len(misses)} ({rate*100:.1f}%)")
    print(f"P&L @$100:    ${pnl(settled):+.0f}")

    # By tier
    print(f"\nBY TIER:")
    for tier in ['AUTO','T1','T2','T3']:
        t_rows = [r for r in settled if r['tier'] == tier]
        if not t_rows:
            continue
        t_hits = [r for r in t_rows if r['result']=='HIT']
        t_rate = len(t_hits)/len(t_rows)
        print(f"  {tier:5} {len(t_hits)}-{len(t_rows)-len(t_hits)} "
              f"({t_rate*100:.0f}%)  ${pnl(t_rows):+.0f}")

    # By date
    print(f"\nBY DATE:")
    dates = sorted(set(r['date'] for r in settled))
    for d in dates:
        d_rows = [r for r in settled if r['date'] == d]
        d_hits = [r for r in d_rows if r['result']=='HIT']
        d_rate = len(d_hits)/len(d_rows)
        d_void = len([r for r in rows if r['date']==d and r['result']=='VOID'])
        void_str = f" ({d_void}v)" if d_void else ""
        print(f"  {d}  {len(d_hits)}-{len(d_rows)-len(d_hits)}"
              f"{void_str}  ({d_rate*100:.0f}%)  ${pnl(d_rows):+.0f}")

    print(f"{'='*55}")

    # Parlay summary
    if os.path.exists(PARLAY_LOG):
        with open(PARLAY_LOG, 'r') as f:
            parlays = [r for r in csv.DictReader(f) if r['result']]
        if parlays:
            p_hits = [p for p in parlays if p['result']=='HIT']
            p_pnl  = sum(float(p['pnl_100']) for p in parlays if p['pnl_100'])
            print(f"\nPARLAYS:")
            print(f"  Record: {len(p_hits)}-{len(parlays)-len(p_hits)}")
            print(f"  P&L:    ${p_pnl:+.0f}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--date",    default=date.today().isoformat())
    parser.add_argument("--result",  action="store_true")
    parser.add_argument("--summary", action="store_true")
    parser.add_argument("--sport",   default="MLB")
    args = parser.parse_args()

    init_logs()

    if args.summary:
        show_summary()
    elif args.result:
        update_results(args.date)
    else:
        log_plays_from_json(args.date, args.sport)
        log_parlays_from_json(args.date, args.sport)
        print(f"\nRun --result to enter today's outcomes")
        print(f"Run --summary to see all-time record")
