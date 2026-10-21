"""NBA availability: the official league injury report (primary) and ESPN's injuries feed (fallback + cross-check).

    python -m engine.nba.injuries                 # latest official report -> data/nba/injuries/, plus ESPN diff
    python -m engine.nba.injuries --url <pdf>     # a specific report

Official report: a PDF published every 15 minutes on game days, URL pattern
    https://ak-static.cms.nba.com/referee/injury/Injury-Report_YYYY-MM-DD_HH_MMAM.pdf
listed on https://official.nba.com/nba-injury-report-<season>-season/. Both reachable from GitHub Actions (Phase 0).
Every parsed row keeps report_time (ET, from the PDF header) so a hold can say which report it came from.

Statuses: Out, Doubtful, Questionable, Probable, Available, plus a team-level NOT YET SUBMITTED row.
ESPN's feed only says Out / Day-To-Day, so the cross-check compares out vs not-out.
"""
from __future__ import annotations
import argparse
import io
import re
from datetime import datetime
from pathlib import Path

import pandas as pd

from engine.nba import http
from engine.nba.crosswalk import name_key
from engine.nba.teams import NAME_TO_NBA

ROOT = Path(__file__).resolve().parents[2]
RAW = ROOT / "data" / "nba" / "raw" / "injury"
OUT = ROOT / "data" / "nba" / "injuries"
INDEX = "https://official.nba.com/nba-injury-report-{season}-season/"
PDF_RE = re.compile(r"https://ak-static\.cms\.nba\.com/referee/injury/Injury-Report_(\d{4}-\d{2}-\d{2})_(\d{2})_(\d{2})(AM|PM)\.pdf")
ESPN_URL = "https://site.api.espn.com/apis/site/v2/sports/basketball/nba/injuries"
STATUSES = ("Out", "Doubtful", "Questionable", "Probable", "Available")
NYS = "NOT YET SUBMITTED"
COLS = ["game_date", "game_time", "matchup", "team", "player", "status", "reason"]
HEADER = {"Date": "game_date", "Time": "game_time", "Matchup": "matchup", "Team": "team",
          "Player": "player", "Current": "status", "Reason": "reason"}
TEAM_SQUASHED = {re.sub(r"\s", "", k): v for k, v in NAME_TO_NBA.items()}


def report_urls(season: str) -> list[str]:
    """Every report PDF linked for a season ('2026-27'), oldest first."""
    html = http.get(INDEX.format(season=season)).text
    return sorted(set(m.group(0) for m in PDF_RE.finditer(html)), key=report_time_from_url)


def report_time_from_url(url: str) -> datetime:
    d, h, m, ap = PDF_RE.search(url).groups()
    return datetime.strptime(f"{d} {h}:{m} {ap}", "%Y-%m-%d %I:%M %p")


def fetch_pdf(url: str) -> bytes:
    path = RAW / url.rsplit("/", 1)[1]
    if path.exists():
        return path.read_bytes()
    b = http.get(url).content
    if not b.startswith(b"%PDF"):
        raise http.FetchError(f"{url} is not a PDF")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(b)
    return b


def _lines(page, prev_cols: dict | None = None) -> tuple[list[dict], dict]:
    """Words grouped into text lines, and the column x-starts read from this page's header row
    (or the previous page's, when a page doesn't repeat the header)."""
    words = page.extract_words(x_tolerance=1.2)
    cols = {}
    for w in words:
        if w["text"] in HEADER and HEADER[w["text"]] not in cols:
            cols[HEADER[w["text"]]] = w["x0"] - 3
    # "Date"/"Time" sit after "Game": the column starts at "Game"
    if "game_date" in cols:
        cols["game_date"] = 0
    if "game_time" in cols:
        cols["game_time"] = min(w["x0"] for w in words if w["text"] == "Game" and w["x0"] > 60) - 3
    head_top = min((w["top"] for w in words if w["text"] == "Matchup"), default=0)
    if len(cols) < len(HEADER):
        if not prev_cols:
            raise ValueError("injury report parse: no column header on the first page")
        cols, head_top = prev_cols, 0
    title = [w["top"] for w in words if w["text"] == "Injury" and w["x0"] > 200]
    lines: dict[int, list] = {}
    for w in words:
        if w["top"] <= head_top + 2 or (title and abs(w["top"] - title[0]) < 3):
            continue
        key = next((k for k in lines if abs(k - w["top"]) < 3), round(w["top"]))
        lines.setdefault(key, []).append(w)
    order = sorted(cols.items(), key=lambda kv: kv[1])
    out = []
    for top in sorted(lines):
        if any(w["text"].startswith("Page") for w in lines[top]):      # footer "Page 1 of 5"
            continue
        cells: dict[str, list[str]] = {}
        for w in sorted(lines[top], key=lambda w: w["x0"]):
            col = [c for c, x in order if w["x0"] >= x][-1] if any(w["x0"] >= x for _, x in order) else order[0][0]
            cells.setdefault(col, []).append(w["text"])
        out.append({"top": top, **{c: " ".join(v) for c, v in cells.items()}})
    return out, cols


def _clean_reason(s: str) -> str:
    return re.sub(r"\s+", " ", s).strip(" -")


def player_name(raw: str) -> str:
    """'Jackson Jr., Jaren' -> 'Jaren Jackson Jr.'; 'Dennis, RayJ' -> 'RayJ Dennis'."""
    if "," not in raw:
        return raw.strip()
    last, first = raw.split(",", 1)
    return f"{first.strip()} {last.strip()}".strip()


def parse_pdf(data: bytes) -> pd.DataFrame:
    import pdfplumber
    rows, report_time, cols = [], None, None
    with pdfplumber.open(io.BytesIO(data)) as pdf:
        for page in pdf.pages:
            if report_time is None:
                m = re.search(r"Injury Report:\s*(\d{2}/\d{2}/\d{2})\s+(\d{2}:\d{2})\s*(AM|PM)", page.extract_text() or "")
                if m:
                    report_time = datetime.strptime(" ".join(m.groups()), "%m/%d/%y %I:%M %p")
            lines, cols = _lines(page, cols)
            page_rows, frags = [], []
            for ln in lines:
                nys = next((c for c in ("player", "status", "reason")
                            if re.sub(r"\s", "", ln.get(c) or "").upper() == NYS.replace(" ", "")), None)
                if nys:                                    # team-level row; the text drifts between columns
                    ln = {**ln, nys: None, "player": None, "status": NYS}
                if ln.get("player") or ln.get("status"):
                    page_rows.append(dict(ln))
                else:
                    frags.append(ln)
            # wrapped cells: a fragment line belongs to the nearest row, preferring rows whose cell is empty
            for f in frags:
                for col, text in f.items():
                    if col == "top" or not page_rows:
                        continue
                    near = sorted(page_rows, key=lambda r: (bool(r.get(col)) and col == "reason", abs(r["top"] - f["top"])))
                    r = near[0]
                    r.setdefault("_" + col, []).append((f["top"], text))
            for r in page_rows:
                for col in COLS:
                    parts = [(r["top"], r[col])] if r.get(col) else []
                    parts += r.pop("_" + col, [])
                    if parts:
                        r[col] = " ".join(t for _, t in sorted(parts))
            rows.extend(page_rows)
    df = pd.DataFrame(rows).reindex(columns=COLS)
    for c in ("game_date", "game_time", "matchup", "team"):          # grouped cells are printed once per group
        df[c] = df[c].ffill()
    df["player"] = df.player.map(lambda s: player_name(s) if isinstance(s, str) else s)
    df["reason"] = df.reason.map(lambda s: _clean_reason(s) if isinstance(s, str) else s)
    df["team"] = df.team.map(lambda s: TEAM_SQUASHED.get(re.sub(r"\s", "", s), s) if isinstance(s, str) else s)
    df["report_time"] = report_time
    bad = df[~df.status.isin(STATUSES + (NYS,))]
    if len(bad):
        raise ValueError(f"injury report parse: {len(bad)} rows with an unknown status, e.g. {bad.iloc[0].to_dict()}")
    off = df[~df.team.isin(NAME_TO_NBA.values())]
    if len(off):
        raise ValueError(f"injury report parse: unmapped team {off.team.iloc[0]!r}")
    return df


def espn_injuries() -> pd.DataFrame:
    d = http.get_json(ESPN_URL)
    rows = []
    for t in d.get("injuries", []):
        team = NAME_TO_NBA.get(t.get("displayName"))
        for i in t.get("injuries", []):
            a = i.get("athlete", {})
            m = re.search(r"/id/(\d+)/", " ".join(l.get("href", "") for l in a.get("links", [])))
            rows.append({"team": team, "player": a.get("displayName"), "espn_id": m.group(1) if m else None,
                         "status": i.get("status"), "updated": i.get("date"), "comment": i.get("shortComment")})
    return pd.DataFrame(rows)


def disagreements(official: pd.DataFrame, espn_df: pd.DataFrame) -> pd.DataFrame:
    """Players whose out / not-out status differs between the sources, plus players only one source lists.
    Only teams on the official report are compared (it lists only teams playing that day)."""
    o = official.dropna(subset=["player"]).assign(key=lambda d: d.player.map(name_key))
    e = espn_df[espn_df.team.isin(o.team.unique())].assign(key=lambda d: d.player.map(name_key))
    m = o[["team", "player", "status", "key"]].merge(e[["team", "status", "key"]], on=["team", "key"], how="outer",
                                                    suffixes=("_official", "_espn"), indicator=True)
    out_o = m.status_official.isin(["Out"])
    out_e = m.status_espn.eq("Out")
    diff = (m._merge != "both") | (out_o != out_e)
    keep = diff & ~(m._merge.eq("left_only") & m.status_official.isin(["Available", "Probable"]))
    return m[keep].drop(columns=["key"]).rename(columns={"_merge": "found_in"})


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--url")
    ap.add_argument("--season", default="2026-27")
    a = ap.parse_args()
    url = a.url or report_urls(a.season)[-1]
    df = parse_pdf(fetch_pdf(url))
    OUT.mkdir(parents=True, exist_ok=True)
    stamp = report_time_from_url(url).strftime("%Y-%m-%d_%H%M")
    df.assign(source_url=url).to_csv(OUT / f"official_{stamp}.csv", index=False)
    try:
        e = espn_injuries()
        d = disagreements(df, e)
        e.to_csv(OUT / f"espn_{stamp}.csv", index=False)
        d.to_csv(OUT / f"disagree_{stamp}.csv", index=False)
        print(f"{url.rsplit('/', 1)[1]}: {len(df)} rows, {df.team.nunique()} teams; ESPN {len(e)} rows; "
              f"{len(d)} disagreements")
    except http.FetchError as err:
        print(f"{url.rsplit('/', 1)[1]}: {len(df)} rows; ESPN fallback unavailable: {err}")


if __name__ == "__main__":
    main()
