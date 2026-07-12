import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
"""
Edge Index — Master Runner

Usage:
  python run_backtest.py           # Full run
  python run_backtest.py --quick   # Skip PFR scraping
  python run_backtest.py --manual  # Force manual 94-player seeder
  python run_backtest.py --report  # Report only
"""
from db_setup        import init_db, get_conn
from seeder_expanded import seed_expanded as seed_manual_data
from line_estimator  import build_prop_lines
from backtester      import run_backtest, generate_report

def main():
    quick  = '--quick'  in sys.argv
    report = '--report' in sys.argv
    manual = '--manual' in sys.argv

    print("="*65)
    print("EDGE INDEX BACKTESTING PIPELINE")
    print("="*65)

    print("\n[1/4] Initializing database...")
    init_db()

    if report:
        print("\n[REPORT ONLY MODE]")
        generate_report()
        return

    # Step 2: Check if nflverse data exists — prefer it over manual seeder
    print("\n[2/4] Seeding player game logs...")
    _conn = get_conn()
    nflverse_count = _conn.execute(
        "SELECT COUNT(*) FROM game_logs"
    ).fetchone()[0]
    nflverse_players = _conn.execute(
        "SELECT COUNT(DISTINCT player_id) FROM game_logs"
    ).fetchone()[0]
    _conn.close()

    if not manual and nflverse_players >= 100:
        # nflverse data already loaded — just clear backtest_results
        # and keep game logs + players + prop lines intact
        _conn2 = get_conn()
        _conn2.execute("DELETE FROM backtest_results")
        _conn2.commit()
        _conn2.close()
        print(f"  Using nflverse data: {nflverse_players} players, "
              f"{nflverse_count:,} game logs — skipping manual seeder")
    else:
        print(f"  nflverse data not found ({nflverse_players} players) "
              f"— running manual seeder")
        seed_manual_data(keep_lines=True)

    # Step 3: Check for real lines
    print("\n[3/4] Checking prop lines...")
    _conn3 = get_conn()
    real_count = _conn3.execute(
        "SELECT COUNT(*) FROM prop_lines WHERE source LIKE 'actual%'"
    ).fetchone()[0]
    _conn3.close()

    if real_count > 0:
        print(f"  Found {real_count:,} real market lines (DK/FD/BetMGM) — skipping estimator")
    else:
        print("  No real lines — building estimates")
        build_prop_lines()

    # Step 4: Run backtest
    print("\n[4/4] Running backtest...")
    df = run_backtest()

    if df is not None and not df.empty:
        generate_report(df)
        out_path = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                "backtest_results.csv")
        df.to_csv(out_path, index=False)
        print(f"\nFull results saved to: {out_path}")
    else:
        print("\nBacktest produced no results.")
        print("Check that game logs were seeded correctly.")

if __name__ == "__main__":
    main()
