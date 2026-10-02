@echo off
REM Edge Index — pregame odds collector (NFL). Scheduled as EdgeIndexCollector (9am, 3pm, 9pm).
REM One-time setup: set the ODDS_API_KEY user variable, then
REM   schtasks /create /tn "EdgeIndexCollector" /tr "%~dp0collect_odds.bat" /sc daily /st 09:00 /ri 360 /du 18:00
REM MLB is paused until 2027, so only NFL is collected (the baseball_mlb run is removed).
REM The collector logs what it spends to automation/lines/odds_usage.csv — the same ledger the GitHub workflows use for
REM the weekly Odds API cap — and stops itself past COLLECTOR_WEEKLY_BUDGET (default 1000). This pushes that one file
REM so the workflows see it; it touches nothing under cfb-app/, so it doesn't deploy the site.
cd /d %~dp0..
git pull --rebase --autostash -q >> agent\logs\collector.log 2>&1
python engine\collector.py --sport americanfootball_nfl >> agent\logs\collector.log 2>&1
git add automation/lines/odds_usage.csv
git diff --cached --quiet -- automation/lines/odds_usage.csv && goto :eof
git commit -q -m "collector usage" -- automation/lines/odds_usage.csv >> agent\logs\collector.log 2>&1
git push -q >> agent\logs\collector.log 2>&1 || (git pull --rebase --autostash -q >> agent\logs\collector.log 2>&1 && git push -q >> agent\logs\collector.log 2>&1)
