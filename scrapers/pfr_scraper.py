"""
EDGE INDEX — Pro Football Reference Game Log Scraper
=====================================================
Mirrors your portal tracker's Playwright + parquet caching architecture.

Scrapes:
  - Player game logs (passing, rushing, receiving) from PFR
  - Snap count / usage data from PFR snap counts pages
  - Defensive stats (yards/game allowed by position) for matchup data

Caching:
  - Parquet files per player per season (same pattern as portal tracker)
  - Only re-scrapes weeks with new data (incremental)
  - GitHub Actions runs this Thursday 6am ET automatically

Usage (local):
    python pfr_scraper.py --players "players.json" --week 10 --season 2025

Usage (GitHub Actions):
    Called by .github/workflows/weekly_update.yml
"""

import asyncio
import json
import time
import argparse
import os
import re
from pathlib import Path
from datetime import datetime, timezone
from typing import Optional
import pandas as pd
import numpy as np

# ── Constants ─────────────────────────────────────────────────────────────────

PFR_BASE      = "https://www.pro-football-reference.com"
CACHE_DIR     = Path("data/cache")
OUTPUT_DIR    = Path("data/processed")
LOGS_DIR      = Path("data/logs")

# PFR throttle: 20 requests/minute enforced, we stay well under
REQUEST_DELAY = 4.0   # seconds between requests (15/min max)

# PFR player ID map — add players here as you expand coverage
# Format: "Display Name": "pfr_player_id"
# Find ID in PFR URL: /players/H/HillTy00.htm → HillTy00
DEFAULT_PLAYERS = {
    # WR
    "Tyreek Hill":      "HillTy00",
    "Justin Jefferson": "JeffJu00",
    "CeeDee Lamb":      "LambCe00",
    "Davante Adams":    "AdamDa01",
    "Stefon Diggs":     "DiggSt00",
    # TE
    "Travis Kelce":     "KelcTr00",
    "Sam LaPorta":      "LaPoSa00",
    # RB
    "Christian McCaffrey": "McCAhCh01",
    "Breece Hall":      "HallBr01",
    "Derrick Henry":    "HenrDe00",
    # QB
    "Lamar Jackson":    "JackLa02",
    "Josh Allen":       "AlleJo02",
    "Patrick Mahomes":  "MahoPa00",
    "Jalen Hurts":      "HurtJa00",
}

# PFR defensive stat page IDs by position
DEF_STAT_PAGES = {
    "passing":   "passing_def",
    "rushing":   "rushing_def",
    "receiving": "receiving_def",
}


# ── Parquet Cache Helpers (same pattern as portal tracker) ────────────────────

def cache_path(player_id: str, season: int, stat_type: str) -> Path:
    """Return the parquet cache path for a player-season."""
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    return CACHE_DIR / f"{player_id}_{season}_{stat_type}.parquet"


def load_cached(player_id: str, season: int, stat_type: str) -> Optional[pd.DataFrame]:
    """Load cached parquet if it exists and is fresh (< 6 hours old)."""
    path = cache_path(player_id, season, stat_type)
    if not path.exists():
        return None
    age_hours = (time.time() - path.stat().st_mtime) / 3600
    if age_hours > 6:
        return None
    try:
        return pd.read_parquet(path)
    except Exception:
        return None


def save_cache(df: pd.DataFrame, player_id: str, season: int, stat_type: str) -> None:
    """Save dataframe to parquet cache."""
    path = cache_path(player_id, season, stat_type)
    df.to_parquet(path, index=False, compression="snappy")


def load_or_create_master(season: int) -> pd.DataFrame:
    """Load master game log parquet for the season, or create empty."""
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    master_path = OUTPUT_DIR / f"game_logs_{season}.parquet"
    if master_path.exists():
        return pd.read_parquet(master_path)
    return pd.DataFrame()


def save_master(df: pd.DataFrame, season: int) -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    path = OUTPUT_DIR / f"game_logs_{season}.parquet"
    df.to_parquet(path, index=False, compression="snappy")
    print(f"  [cache] Saved master → {path} ({len(df)} rows)")


# ── HTML Parsing Helpers ──────────────────────────────────────────────────────

def _safe_float(val: str, default: float = 0.0) -> float:
    """Convert PFR table cell string to float safely."""
    if not val or val.strip() in ("", "--", "Did Not Play", "Inactive", "N/A"):
        return default
    cleaned = re.sub(r"[^\d.\-]", "", val.strip())
    try:
        return float(cleaned)
    except ValueError:
        return default


def _safe_int(val: str, default: int = 0) -> int:
    return int(_safe_float(val, default))


def parse_game_log_table(html: str, position: str, season: int) -> pd.DataFrame:
    """
    Parse a PFR game log HTML page into a structured DataFrame.
    Handles passing, rushing, and receiving columns dynamically.
    """
    try:
        tables = pd.read_html(html, attrs={"id": "stats"})
        if not tables:
            return pd.DataFrame()
        df = tables[0]
    except Exception:
        # Fallback: try first table with 'Week' column
        try:
            all_tables = pd.read_html(html)
            df = next((t for t in all_tables if "Week" in t.columns), pd.DataFrame())
        except Exception:
            return pd.DataFrame()

    if df.empty:
        return df

    # PFR uses multi-level headers sometimes — flatten
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = ["_".join(str(c) for c in col).strip("_") for col in df.columns]

    # Remove header repeat rows
    df = df[df.iloc[:, 0].astype(str).str.match(r"^\d+$", na=False)].copy()
    df = df.reset_index(drop=True)

    # Standardize column mapping
    col_map = {
        # Core
        "Week":       "week",
        "Date":       "date",
        "Tm":         "team",
        "Opp":        "opponent",
        # Home/Away indicator — PFR uses "" for home, "@" for away
        "Unnamed: 4": "home_away_raw",
        # Passing
        "Cmp":        "pass_comp",
        "Att":        "pass_att",
        "Yds":        "pass_yards",
        "TD":         "pass_tds",
        "Int":        "interceptions",
        # Rushing
        "Att.1":      "rush_att",
        "Yds.1":      "rush_yards",
        "TD.1":       "rush_tds",
        # Receiving
        "Tgt":        "targets",
        "Rec":        "receptions",
        "Yds.2":      "rec_yards",
        "TD.2":       "rec_tds",
        # Game info
        "GS":         "game_started",
        "Sk":         "sacks",
    }

    # Rename what we find
    rename = {k: v for k, v in col_map.items() if k in df.columns}
    df = df.rename(columns=rename)

    # Numeric conversion
    numeric_cols = [
        "week", "pass_comp", "pass_att", "pass_yards", "pass_tds",
        "rush_att", "rush_yards", "rush_tds",
        "targets", "receptions", "rec_yards", "rec_tds",
    ]
    for col in numeric_cols:
        if col in df.columns:
            df[col] = df[col].apply(lambda x: _safe_float(str(x)))

    # Home/away flag
    if "home_away_raw" in df.columns:
        df["home_away"] = df["home_away_raw"].apply(
            lambda x: "away" if str(x).strip() == "@" else "home"
        )
    else:
        df["home_away"] = "home"

    df["season"] = season
    df["position"] = position.upper()

    # Drop rows where week is 0 (bye, DNP, etc.)
    df = df[df["week"] > 0].copy()

    return df


def parse_defense_ranks(html: str, stat_type: str) -> pd.DataFrame:
    """
    Parse PFR team defense rankings page.
    Returns DataFrame with team name + rank for each stat category.
    """
    try:
        tables = pd.read_html(html)
        df = tables[0] if tables else pd.DataFrame()
    except Exception:
        return pd.DataFrame()

    if df.empty:
        return df

    if isinstance(df.columns, pd.MultiIndex):
        df.columns = ["_".join(str(c) for c in col).strip("_") for col in df.columns]

    df = df.rename(columns={"Tm": "team"})
    df = df[df["team"].astype(str).str.len() < 30].copy()

    # Add rank columns (lower yards = better defense = lower rank number)
    if stat_type == "passing" and "Yds" in df.columns:
        df["pass_yards_allowed"] = df["Yds"].apply(lambda x: _safe_float(str(x)))
        df["def_pass_rank"] = df["pass_yards_allowed"].rank(ascending=True).astype(int)
    elif stat_type == "rushing" and "Yds" in df.columns:
        df["rush_yards_allowed"] = df["Yds"].apply(lambda x: _safe_float(str(x)))
        df["def_rush_rank"] = df["rush_yards_allowed"].rank(ascending=True).astype(int)
    elif stat_type == "receiving" and "Yds" in df.columns:
        df["rec_yards_allowed"] = df["Yds"].apply(lambda x: _safe_float(str(x)))
        df["def_rec_rank"] = df["rec_yards_allowed"].rank(ascending=True).astype(int)

    df["stat_type"] = stat_type
    return df[["team", "stat_type"] + [c for c in df.columns
               if "rank" in c or "allowed" in c]].copy()


# ── Playwright Scraper ────────────────────────────────────────────────────────

class PFRScraper:
    """
    Playwright-based scraper for Pro Football Reference.
    Same browser automation pattern as your portal tracker's On3 scraper.

    Key design decisions:
    - Headed=False (headless) for GitHub Actions
    - Randomized delays to stay under PFR's rate limit
    - User-agent rotation (single realistic UA is fine for PFR)
    - Incremental: only fetches pages not already in cache
    """

    USER_AGENT = (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    )

    def __init__(self, headless: bool = True, delay: float = REQUEST_DELAY):
        self.headless = headless
        self.delay    = delay
        self.browser  = None
        self.page     = None
        self._request_count = 0

    async def __aenter__(self):
        from playwright.async_api import async_playwright
        self._pw      = await async_playwright().start()
        self.browser  = await self._pw.chromium.launch(headless=self.headless)
        context       = await self.browser.new_context(user_agent=self.USER_AGENT)
        self.page     = await context.new_page()
        # Block images/fonts to speed up scraping
        await self.page.route(
            "**/*.{png,jpg,jpeg,gif,svg,ico,woff,woff2,ttf}",
            lambda r: r.abort()
        )
        return self

    async def __aexit__(self, *args):
        await self.browser.close()
        await self._pw.stop()

    async def _get(self, url: str) -> str:
        """Fetch a URL and return HTML content with rate limiting."""
        if self._request_count > 0:
            jitter = self.delay + np.random.uniform(0.5, 2.0)
            await asyncio.sleep(jitter)
        await self.page.goto(url, wait_until="domcontentloaded", timeout=30000)
        self._request_count += 1
        return await self.page.content()

    async def scrape_player_game_log(
        self,
        player_name: str,
        player_id: str,
        position: str,
        season: int,
        force_refresh: bool = False,
    ) -> pd.DataFrame:
        """
        Scrape a player's season game log from PFR.
        Uses parquet cache — only hits PFR if cache is stale.
        """
        # Check cache first (same pattern as portal tracker)
        if not force_refresh:
            cached = load_cached(player_id, season, "gamelog")
            if cached is not None:
                print(f"  [cache] {player_name} — loaded from parquet")
                return cached

        # Build PFR URL
        # Pattern: /players/{FIRST_LETTER}/{player_id}/gamelog/{season}/
        first_letter = player_id[0].upper()
        url = f"{PFR_BASE}/players/{first_letter}/{player_id}/gamelog/{season}/"

        print(f"  [scrape] {player_name} → {url}")
        html = await self._get(url)
        df   = parse_game_log_table(html, position, season)

        if df.empty:
            print(f"  [warn] No data parsed for {player_name}")
            return df

        df["player_name"] = player_name
        df["player_id"]   = player_id

        # Cache it
        save_cache(df, player_id, season, "gamelog")
        print(f"  [cache] {player_name} — saved {len(df)} games to parquet")
        return df

    async def scrape_snap_counts(
        self,
        player_id: str,
        player_name: str,
        season: int,
    ) -> pd.DataFrame:
        """
        Scrape snap count / usage % for a player.
        PFR snap page: /players/{L}/{id}/splits/{season}/
        """
        cached = load_cached(player_id, season, "snaps")
        if cached is not None:
            return cached

        first_letter = player_id[0].upper()
        url = f"{PFR_BASE}/players/{first_letter}/{player_id}/splits/{season}/"
        print(f"  [scrape] snap counts {player_name} → {url}")
        html = await self._get(url)

        try:
            tables = pd.read_html(html)
            # Find the "By Week" table
            snap_table = next(
                (t for t in tables if "Snap" in str(t.columns.tolist())),
                pd.DataFrame()
            )
            if not snap_table.empty:
                snap_table["player_id"] = player_id
                save_cache(snap_table, player_id, season, "snaps")
            return snap_table
        except Exception:
            return pd.DataFrame()

    async def scrape_defense_rankings(self, season: int) -> dict[str, pd.DataFrame]:
        """
        Scrape team defensive rankings for pass/rush/receiving.
        Returns dict keyed by stat_type.
        """
        results = {}
        for stat_type, page_id in DEF_STAT_PAGES.items():
            cached = load_cached("DEF", season, stat_type)
            if cached is not None:
                results[stat_type] = cached
                continue

            url = f"{PFR_BASE}/years/{season}/{page_id}.htm"
            print(f"  [scrape] defense rankings ({stat_type}) → {url}")
            html = await self._get(url)
            df   = parse_defense_ranks(html, stat_type)
            if not df.empty:
                save_cache(df, "DEF", season, stat_type)
                results[stat_type] = df

        return results


# ── Pipeline Orchestrator ─────────────────────────────────────────────────────

class EdgeIndexPipeline:
    """
    Full weekly data pipeline:
      1. Scrape player game logs (incremental)
      2. Scrape defensive rankings
      3. Merge + enrich with Vegas lines (manual input for now)
      4. Save master parquet
      5. Generate model-ready JSON for pick sheet

    Thursday morning GitHub Actions workflow calls this automatically.
    """

    def __init__(self, season: int, week: int, players: dict = None):
        self.season  = season
        self.week    = week
        self.players = players or DEFAULT_PLAYERS

    async def run(self, force_refresh: bool = False) -> dict:
        """Execute full pipeline. Returns summary of what was updated."""
        LOGS_DIR.mkdir(parents=True, exist_ok=True)
        log_path = LOGS_DIR / f"pipeline_{self.season}_w{self.week}.json"

        print(f"\n{'='*60}")
        print(f"EDGE INDEX PIPELINE — Season {self.season}, Week {self.week}")
        print(f"Players: {len(self.players)} | Force refresh: {force_refresh}")
        print(f"{'='*60}\n")

        summary = {
            "season": self.season,
            "week":   self.week,
            "run_at": datetime.now(timezone.utc).isoformat(),
            "players_updated": [],
            "players_failed":  [],
            "defense_updated": False,
        }

        all_logs = []

        async with PFRScraper() as scraper:

            # 1. Player game logs
            for player_name, player_id in self.players.items():
                # Determine position from player list
                # (In production, store this in players.json)
                position = self._infer_position(player_name)
                try:
                    df = await scraper.scrape_player_game_log(
                        player_name, player_id, position,
                        self.season, force_refresh
                    )
                    if not df.empty:
                        all_logs.append(df)
                        summary["players_updated"].append(player_name)
                except Exception as e:
                    print(f"  [error] {player_name}: {e}")
                    summary["players_failed"].append(
                        {"player": player_name, "error": str(e)}
                    )

            # 2. Defensive rankings
            try:
                def_rankings = await scraper.scrape_defense_rankings(self.season)
                if def_rankings:
                    self._save_defense_rankings(def_rankings)
                    summary["defense_updated"] = True
            except Exception as e:
                print(f"  [error] defense rankings: {e}")

        # 3. Merge all player logs into master parquet
        if all_logs:
            master = pd.concat(all_logs, ignore_index=True)
            existing = load_or_create_master(self.season)
            if not existing.empty:
                # Upsert: replace existing rows for same player+week
                key_cols = ["player_id", "season", "week"]
                if all(c in master.columns and c in existing.columns
                       for c in key_cols):
                    existing = existing[
                        ~existing.set_index(key_cols).index.isin(
                            master.set_index(key_cols).index
                        )
                    ]
                master = pd.concat([existing, master], ignore_index=True)
            save_master(master, self.season)
            summary["total_rows"] = len(master)

        # 4. Save pipeline log
        with open(log_path, "w") as f:
            json.dump(summary, f, indent=2, default=str)
        print(f"\n[pipeline] Complete. Log → {log_path}")
        return summary

    def _infer_position(self, player_name: str) -> str:
        """
        Quick position lookup. In production, load from players.json.
        """
        qbs = {"Lamar Jackson", "Josh Allen", "Patrick Mahomes", "Jalen Hurts"}
        rbs = {"Christian McCaffrey", "Breece Hall", "Derrick Henry"}
        tes = {"Travis Kelce", "Sam LaPorta"}
        if player_name in qbs:  return "QB"
        if player_name in rbs:  return "RB"
        if player_name in tes:  return "TE"
        return "WR"

    def _save_defense_rankings(self, rankings: dict[str, pd.DataFrame]) -> None:
        OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
        for stat_type, df in rankings.items():
            path = OUTPUT_DIR / f"def_rankings_{stat_type}_{self.season}.parquet"
            df.to_parquet(path, index=False, compression="snappy")
            print(f"  [cache] Defense {stat_type} rankings → {path}")


# ── Model Data Loader ─────────────────────────────────────────────────────────

class ModelDataLoader:
    """
    Loads cached parquet data and converts to PlayerGame objects
    for direct use in nfl_props_model.py.

    Usage:
        loader = ModelDataLoader(season=2025)
        games = loader.get_player_games("Tyreek Hill", n_games=8)
        # → list[PlayerGame] ready for PropModel.project_player()
    """

    def __init__(self, season: int):
        self.season = season
        self._master: Optional[pd.DataFrame] = None
        self._def_pass: Optional[pd.DataFrame] = None
        self._def_rush: Optional[pd.DataFrame] = None
        self._def_rec:  Optional[pd.DataFrame] = None
        self._load()

    def _load(self):
        self._master   = load_or_create_master(self.season)
        pass_path = OUTPUT_DIR / f"def_rankings_passing_{self.season}.parquet"
        rush_path = OUTPUT_DIR / f"def_rankings_rushing_{self.season}.parquet"
        rec_path  = OUTPUT_DIR / f"def_rankings_receiving_{self.season}.parquet"
        if pass_path.exists():
            self._def_pass = pd.read_parquet(pass_path)
        if rush_path.exists():
            self._def_rush = pd.read_parquet(rush_path)
        if rec_path.exists():
            self._def_rec  = pd.read_parquet(rec_path)

    def get_player_games(self, player_name: str, n_games: int = 8) -> list:
        """Return last n games as PlayerGame objects."""
        # Import here to avoid circular dependency
        import sys
        sys.path.insert(0, str(Path(__file__).parent.parent / "models"))
        from nfl_props_model import PlayerGame

        if self._master is None or self._master.empty:
            print(f"  [warn] No master data loaded for {player_name}")
            return []

        player_df = self._master[
            self._master["player_name"] == player_name
        ].sort_values("week")

        if player_df.empty:
            print(f"  [warn] No data found for {player_name}")
            return []

        recent = player_df.tail(n_games)
        games  = []

        for _, row in recent.iterrows():
            g = PlayerGame(
                week       = int(row.get("week", 0)),
                opponent   = str(row.get("opponent", "UNK")),
                home_away  = str(row.get("home_away", "home")),
                snap_pct   = float(row.get("snap_pct", 0.80)),
                pass_att   = float(row.get("pass_att",   0)),
                pass_comp  = float(row.get("pass_comp",  0)),
                pass_yards = float(row.get("pass_yards", 0)),
                pass_tds   = float(row.get("pass_tds",   0)),
                rush_att   = float(row.get("rush_att",   0)),
                rush_yards = float(row.get("rush_yards", 0)),
                rush_tds   = float(row.get("rush_tds",   0)),
                targets    = float(row.get("targets",    0)),
                receptions = float(row.get("receptions", 0)),
                rec_yards  = float(row.get("rec_yards",  0)),
                rec_tds    = float(row.get("rec_tds",    0)),
                team_pass_att = float(row.get("team_pass_att", 35)),
                team_rush_att = float(row.get("team_rush_att", 25)),
                vegas_total   = float(row.get("vegas_total",   44)),
                team_spread   = float(row.get("team_spread",    0)),
            )
            games.append(g)

        return games

    def get_defense_rank(self, team_abbr: str, stat_type: str) -> int:
        """Return defensive rank (1–32) for a team against a stat type."""
        df_map = {
            "passing":   self._def_pass,
            "rushing":   self._def_rush,
            "receiving": self._def_rec,
        }
        df = df_map.get(stat_type)
        if df is None or df.empty:
            return 16   # default to middle

        # PFR uses 3-letter team abbreviations
        row = df[df["team"].str.upper() == team_abbr.upper()]
        if row.empty:
            return 16

        rank_col = [c for c in df.columns if "rank" in c]
        if not rank_col:
            return 16

        return int(row[rank_col[0]].values[0])


# ── CLI Entry Point ───────────────────────────────────────────────────────────

async def main():
    parser = argparse.ArgumentParser(description="Edge Index data pipeline")
    parser.add_argument("--season",  type=int, default=2025)
    parser.add_argument("--week",    type=int, required=True)
    parser.add_argument("--players", type=str, default=None,
                        help="Path to players.json (optional)")
    parser.add_argument("--refresh", action="store_true",
                        help="Force re-scrape even if cached")
    args = parser.parse_args()

    # Load custom player list if provided
    players = DEFAULT_PLAYERS
    if args.players and Path(args.players).exists():
        with open(args.players) as f:
            players = json.load(f)
        print(f"Loaded {len(players)} players from {args.players}")

    pipeline = EdgeIndexPipeline(
        season  = args.season,
        week    = args.week,
        players = players,
    )
    summary = await pipeline.run(force_refresh=args.refresh)
    print(f"\nSummary: {json.dumps(summary, indent=2, default=str)}")


if __name__ == "__main__":
    asyncio.run(main())
