"""NOAA weather for CFB totals (Phase 5B; Tim approved NOAA 2026-10-12).

    python -m engine.cfb.weather.noaa stations     # venue -> nearest active U.S. ISD station
    python -m engine.cfb.weather.noaa pull         # one-time ISD-Lite download (station-years)
    python -m engine.cfb.weather.noaa kickoff      # observed weather at kickoff per game
    python -m engine.cfb.weather.noaa forecast --season 2026 --week 7   # NWS hourly, live games

Sources and terms (docs/cfb/PHASE5_REPORT.md):
  * NCEI ISD-Lite (hourly: temp, wind, 1h/6h precip), which ends 2025-08-25; GHCNh (its NCEI
    successor, by-year parquet) for 2025-26. U.S. stations only: NCEI restricts
    only non-U.S. ISD data (WMO Res. 40). Files: /pub/data/noaa/isd-lite/<year>/<usaf>-<wban>-<year>.gz
  * NWS api.weather.gov (points -> forecastHourly). Free, open data; a User-Agent with contact
    info is required: set NWS_CONTACT (default "edge-index.com").

HISTORICAL = OBSERVED kickoff weather, which was NOT known at the open, so a backtest that uses
it is FLATTERED. Live uses NWS forecasts captured at bet time.
Domes (venues.parquet dome == True) get no weather (indoor flag). Non-U.S. venues: missing.
Downloaded files are untrusted data: they go to data/cfb/raw/weather/isd_lite/ (gitignored),
are parsed as fixed-width numbers only, and are never executed.
"""
from __future__ import annotations
import argparse
import gzip
import io
import os
import time
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd

from engine.cfb import config

RAW = config.RAW / "weather" / "isd_lite"
WX = config.DATA / "weather"
STATIONS = WX / "venue_stations.csv"
KICKOFF = WX / "kickoff_weather.parquet"
FORECASTS = WX / "nws_forecasts_{season}.csv"
HISTORY_URL = "https://www.ncei.noaa.gov/pub/data/noaa/isd-history.csv"
LITE_URL = "https://www.ncei.noaa.gov/pub/data/noaa/isd-lite/{y}/{sid}-{y}.gz"
# ISD (and ISD-Lite) stopped at 2025-08-25; its successor GHCNh covers 2025-26 (~1 week lag)
GHCNH_BASE = "https://www.ncei.noaa.gov/oa/global-historical-climatology-network/hourly"
GHCNH_URL = GHCNH_BASE + "/access/by-year/{y}/parquet/GHCNh_{gid}_{y}.parquet"
GHCNH_LIST = GHCNH_BASE + "/doc/ghcnh-station-list.txt"
GHCNH_RAW = config.RAW / "weather" / "ghcnh"
GHCNH_YEARS = (2025, 2026)
MAX_KM = 50.0
SEASONS = range(2021, config.CURRENT_SEASON + 1)


def _ua() -> str:
    return f"edge-index CFB model ({os.environ.get('NWS_CONTACT', 'edge-index.com')})"


def _get(url: str, timeout=60):
    import requests
    return requests.get(url, headers={"User-Agent": _ua()}, timeout=timeout)


def venues_in_use() -> pd.DataFrame:
    g = pd.read_parquet(config.CLEAN / "games.parquet")
    v = pd.read_parquet(config.CLEAN / "venues.parquet")
    g = g[g.both_fbs & g.season.isin(list(SEASONS)) & ~(g.is_bowl & ~g.is_cfp)]
    use = g.groupby("venue_id").size().rename("games").reset_index().merge(v, on="venue_id", how="left")
    return use


def stations() -> pd.DataFrame:
    WX.mkdir(parents=True, exist_ok=True)
    r = _get(HISTORY_URL, timeout=120)
    r.raise_for_status()
    st = pd.read_csv(io.StringIO(r.text), dtype=str)
    st = st[st.CTRY == "US"].copy()
    st["lat"] = pd.to_numeric(st.LAT, errors="coerce")
    st["lon"] = pd.to_numeric(st.LON, errors="coerce")
    st = st[(st.BEGIN <= "20210101") & (st.END >= "20250801")].dropna(subset=["lat", "lon"])
    st = st[~((st.lat == 0) & (st.lon == 0))]
    use = venues_in_use()
    out = use[(use.dome != True) & (use.country == "US")].dropna(subset=["latitude", "longitude"]).copy()  # noqa: E712
    la1, lo1 = np.radians(out.latitude.values)[:, None], np.radians(out.longitude.values)[:, None]
    la2, lo2 = np.radians(st.lat.values)[None, :], np.radians(st.lon.values)[None, :]
    a = np.sin((la2 - la1) / 2) ** 2 + np.cos(la1) * np.cos(la2) * np.sin((lo2 - lo1) / 2) ** 2
    km = 6371 * 2 * np.arcsin(np.sqrt(a))
    order = np.argsort(km, axis=1)[:, :3]                       # nearest 3 as fallbacks
    rows = []
    for i, r_ in enumerate(out.itertuples()):
        for rank, j in enumerate(order[i]):
            rows.append({"venue_id": r_.venue_id, "venue": r_.name, "rank": rank,
                         "station": f"{st.USAF.values[j]}-{st.WBAN.values[j]}",
                         "station_name": st["STATION NAME"].values[j], "km": float(km[i, j])})
    s = pd.DataFrame(rows)
    s = s[s.km <= MAX_KM]
    s.to_csv(STATIONS, index=False)
    return s


def pull(sleep: float = 0.25, max_rank: int = 0, only_venues=None) -> dict:
    """Download station-years for stations up to `max_rank` (0 = nearest per venue)."""
    s = pd.read_csv(STATIONS)
    s = s[s["rank"] <= max_rank]
    if only_venues is not None:
        s = s[s.venue_id.isin(only_venues)]
    need = sorted(set(s.station))
    RAW.mkdir(parents=True, exist_ok=True)
    got = missing = skipped = 0
    for sid in need:
        for y in SEASONS:
            path = RAW / str(y) / f"{sid}-{y}.gz"
            if path.exists() and y < config.CURRENT_SEASON:
                skipped += 1
                continue
            r = _get(LITE_URL.format(y=y, sid=sid))
            if r.status_code == 404:
                missing += 1
                continue
            r.raise_for_status()
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(r.content)
            got += 1
            time.sleep(sleep)
    return {"stations": len(need), "downloaded": got, "missing_station_years": missing, "cached": skipped}


def read_lite(path: Path) -> pd.DataFrame:
    """ISD-Lite fixed-width: yr mo dy hr temp(C*10) dew slp wdir wspd(m/s*10) sky p1h(mm*10) p6h."""
    with gzip.open(path, "rt") as f:
        df = pd.read_csv(f, sep=r"\s+", header=None,
                         names=["y", "m", "d", "h", "temp", "dew", "slp", "wdir", "wspd", "sky", "p1", "p6"])
    df = df.replace(-9999, np.nan)
    df["ts"] = pd.to_datetime(dict(year=df.y, month=df.m, day=df.d, hour=df.h), utc=True)
    df["temp_f"] = df.temp / 10 * 9 / 5 + 32
    df["wind_mph"] = df.wspd / 10 * 2.23694
    df["p1_mm"] = df.p1.where(df.p1 >= 0, 0.0) / 10        # -1 = trace
    df["p6_mm"] = df.p6.where(df.p6 >= 0, 0.0) / 10
    return df[["ts", "temp_f", "wind_mph", "p1_mm", "p6_mm"]]


def ghcnh_ids() -> dict:
    """ISD 'USAF-WBAN' -> GHCNh id: USW000<WBAN> if listed, else nearest GHCNh station <= 2 km."""
    r = _get(GHCNH_LIST, timeout=180)
    r.raise_for_status()
    rows = [(ln[:11].strip(), float(ln[12:20]), float(ln[21:30])) for ln in r.text.splitlines() if len(ln) > 30]
    gl = pd.DataFrame(rows, columns=["gid", "lat", "lon"])
    ids = set(gl.gid)
    st = pd.read_csv(STATIONS)
    hist = pd.read_csv(io.StringIO(_get(HISTORY_URL, timeout=180).text), dtype=str)
    hist["sid"] = hist.USAF + "-" + hist.WBAN
    hist = hist.set_index("sid")
    out = {}
    for sid in sorted(set(st.station)):
        wban = sid.split("-")[1]
        if wban != "99999" and f"USW000{wban}" in ids:
            out[sid] = f"USW000{wban}"
            continue
        if sid in hist.index:
            la, lo = float(hist.loc[sid, "LAT"]), float(hist.loc[sid, "LON"])
            dkm = 111 * np.hypot(gl.lat - la, (gl.lon - lo) * np.cos(np.radians(la)))
            j = dkm.idxmin()
            if dkm[j] <= 2.0:
                out[sid] = gl.gid[j]
    return out


def pull_ghcnh(sleep: float = 0.25, max_rank: int = 0) -> dict:
    s = pd.read_csv(STATIONS)
    s = s[s["rank"] <= max_rank]
    m = ghcnh_ids()
    pd.Series(m, name="ghcnh_id").rename_axis("station").to_csv(WX / "isd_to_ghcnh.csv")
    got = miss = 0
    for sid in sorted(set(s.station)):
        gid = m.get(sid)
        if not gid:
            miss += len(GHCNH_YEARS)
            continue
        for y in GHCNH_YEARS:
            path = GHCNH_RAW / str(y) / f"{sid}.parquet"
            if path.exists() and y < config.CURRENT_SEASON:
                continue
            r = _get(GHCNH_URL.format(y=y, gid=gid), timeout=180)
            if r.status_code != 200:
                miss += 1
                continue
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(r.content)
            got += 1
            time.sleep(sleep)
    return {"stations": len(set(s.station)), "mapped": sum(1 for x in set(s.station) if x in m),
            "downloaded": got, "missing": miss}


def read_ghcnh(path: Path) -> pd.DataFrame:
    d = pd.read_parquet(path, columns=["DATE", "temperature", "wind_speed", "precipitation"])
    d["ts"] = pd.to_datetime(d.DATE, utc=True)
    d["temp_f"] = pd.to_numeric(d.temperature, errors="coerce") * 9 / 5 + 32
    d["wind_mph"] = pd.to_numeric(d.wind_speed, errors="coerce") * 2.23694
    d["p1_mm"] = pd.to_numeric(d.precipitation, errors="coerce").fillna(0.0)
    d["p6_mm"] = np.nan
    return d[["ts", "temp_f", "wind_mph", "p1_mm", "p6_mm"]]


def kickoff() -> pd.DataFrame:
    """Observed weather at kickoff (nearest hourly obs within 90 min; next station if missing)."""
    g = pd.read_parquet(config.CLEAN / "games.parquet")
    v = pd.read_parquet(config.CLEAN / "venues.parquet").set_index("venue_id")
    g = g[g.both_fbs & g.season.isin(list(SEASONS)) & ~(g.is_bowl & ~g.is_cfp)]
    s = pd.read_csv(STATIONS).sort_values(["venue_id", "rank"])
    cache: dict = {}

    def series(sid, y):
        k = (sid, y)
        if k not in cache:
            p = RAW / str(y) / f"{sid}-{y}.gz"
            q = GHCNH_RAW / str(y) / f"{sid}.parquet"
            parts = [read_lite(p)] if p.exists() else []
            if q.exists():
                parts.append(read_ghcnh(q))
            if parts:
                z = pd.concat(parts).dropna(subset=["temp_f"]).sort_values("ts")
                cache[k] = z.drop_duplicates("ts", keep="first").set_index("ts")
            else:
                cache[k] = None
        return cache[k]

    rows = []
    for r in g.itertuples():
        dome = bool(v.dome.get(r.venue_id)) if r.venue_id in v.index and pd.notna(v.dome.get(r.venue_id)) else False
        row = {"game_id": r.game_id, "indoor": dome, "temp_f": np.nan, "wind_mph": np.nan,
               "precip_mm_1h": np.nan, "station": None, "obs_lag_min": np.nan}
        if not dome:
            for c in s[s.venue_id == r.venue_id].itertuples():
                ser = series(c.station, r.kickoff_utc.year)
                if ser is None or ser.empty:
                    continue
                i = ser.index.get_indexer([r.kickoff_utc], method="nearest")[0]
                lag = abs((ser.index[i] - r.kickoff_utc).total_seconds()) / 60
                if lag > 90 or pd.isna(ser.temp_f.iloc[i]):
                    continue
                win = ser.loc[r.kickoff_utc - pd.Timedelta(hours=1): r.kickoff_utc + pd.Timedelta(hours=3)]
                row.update({"temp_f": ser.temp_f.iloc[i], "wind_mph": ser.wind_mph.iloc[i],
                            "precip_mm_1h": float(win.p1_mm.max()) if len(win) else np.nan,
                            "station": c.station, "obs_lag_min": lag})
                break
        rows.append(row)
    out = pd.DataFrame(rows)
    out["source"] = "observed (ISD-Lite <= 2025-08-25, GHCNh after)"   # NOT known at the open: flatters any backtest
    WX.mkdir(parents=True, exist_ok=True)
    out.to_parquet(KICKOFF, index=False)
    return out


def forecast(season: int, week: int) -> pd.DataFrame:
    """NWS hourly forecast at kickoff for the week's outdoor U.S. games, captured now."""
    g = pd.read_parquet(config.CLEAN / "games.parquet")
    v = pd.read_parquet(config.CLEAN / "venues.parquet").set_index("venue_id")
    now = pd.Timestamp.now(tz="UTC")
    g = g[(g.season == season) & (g.week == week) & g.both_fbs & (g.kickoff_utc > now)]
    rows = []
    for r in g.itertuples():
        if r.venue_id not in v.index:
            continue
        vv = v.loc[r.venue_id]
        if vv.dome is True or vv.country != "US" or pd.isna(vv.latitude):
            continue
        pt = _get(f"https://api.weather.gov/points/{vv.latitude:.4f},{vv.longitude:.4f}")
        if pt.status_code != 200:
            continue
        hourly = _get(pt.json()["properties"]["forecastHourly"])
        if hourly.status_code != 200:
            continue
        per = pd.DataFrame(hourly.json()["properties"]["periods"])
        per["start"] = pd.to_datetime(per.startTime, utc=True)
        i = (per.start - r.kickoff_utc).abs().idxmin()
        p = per.loc[i]
        wind = pd.to_numeric(str(p.windSpeed).split(" ")[-2] if " to " in str(p.windSpeed)
                             else str(p.windSpeed).split(" ")[0], errors="coerce")
        pop = (p.probabilityOfPrecipitation or {}).get("value") if isinstance(p.probabilityOfPrecipitation, dict) else None
        rows.append({"captured_at_utc": now.isoformat(timespec="seconds"), "game_id": r.game_id,
                     "kickoff_utc": r.kickoff_utc, "forecast_hour_utc": p.start,
                     "temp_f": p.temperature, "wind_mph": wind, "precip_prob": pop,
                     "short": p.shortForecast, "source": "nws_forecast"})
        time.sleep(0.2)
    out = pd.DataFrame(rows)
    path = Path(str(FORECASTS).format(season=season))
    out.to_csv(path, mode="a", header=not path.exists(), index=False)
    return out


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", choices=["stations", "pull", "pull-ghcnh", "kickoff", "forecast"])
    ap.add_argument("--season", type=int, default=config.CURRENT_SEASON)
    ap.add_argument("--week", type=int)
    ap.add_argument("--max-rank", type=int, default=0)
    a = ap.parse_args()
    if a.cmd == "stations":
        s = stations()
        print(f"{s.venue_id.nunique()} venues -> {s.station.nunique()} stations (<= {MAX_KM:.0f} km, top 3 each) -> {STATIONS}")
    elif a.cmd == "pull-ghcnh":
        print(pull_ghcnh(max_rank=a.max_rank))
    elif a.cmd == "pull":
        print(pull(max_rank=a.max_rank))
    elif a.cmd == "kickoff":
        k = kickoff()
        print(k.groupby("indoor").agg(games=("game_id", "size"), with_obs=("temp_f", lambda x: x.notna().sum())))
    else:
        f = forecast(a.season, a.week)
        print(f"{len(f)} forecasts captured")
