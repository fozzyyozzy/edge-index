"""
Edge Index — Master NFL Thursday Runner
Run this every Thursday before games start.

Usage:
  python run_nfl.py --week 1 --season 2026
  python run_nfl.py --week 1 --season 2026 --dry-run
  python run_nfl.py --week 1 --season 2026 --reddit
"""
import os, sys, argparse, subprocess

NFL_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "nfl")

def run(script, args):
    cmd = [sys.executable, os.path.join(NFL_DIR, script)] + args
    print(f"\n{'='*65}")
    print(f"Running: {script}")
    print(f"{'='*65}")
    result = subprocess.run(cmd, cwd=NFL_DIR)
    return result.returncode == 0

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--week",    type=int, required=True)
    parser.add_argument("--season",  type=int, required=True)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--reddit",  action="store_true",
                        help="Also output Reddit streak sheet")
    args = parser.parse_args()

    base_args = ["--week", str(args.week), "--season", str(args.season)]
    dry_args  = base_args + (["--dry-run"] if args.dry_run else [])

    print(f"\nEDGE INDEX — NFL WEEK {args.week} {args.season}")
    print(f"{'═'*65}")

    # Step 1: Pull live schedule
    ok = run("live_schedule.py", dry_args)
    if not ok:
        print("Schedule pull failed — continuing with demo data")

    # Step 2: Run full pipeline
    ok = run("weekly_pipeline.py", dry_args)
    if not ok:
        print("Pipeline failed — check errors above")
        sys.exit(1)

    # Step 3: Generate streak sheets
    reddit_args = base_args + (["--reddit"] if args.reddit else [])
    run("streak_sheets.py", reddit_args)

    # Step 4: Generate line analysis
    run("line_analysis.py", base_args)

    print(f"\n{'='*65}")
    print(f"✓ WEEK {args.week} {args.season} PLAYBOOK COMPLETE")
    print(f"{'='*65}")
    print(f"Output files:")
    print(f"  nfl/schedule_w{args.week}_{args.season}.json")
    print(f"  nfl/weekly_plays_w{args.week}_{args.season}.json")
    print(f"  → Copy JSON to cfb-app/src/ and npm run build")
