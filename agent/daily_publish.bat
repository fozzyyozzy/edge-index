@echo off
REM Edge Index — daily publish: pull -> MLB morning routine -> commit + push the MLB site files.
REM No local build or deploy: the push to main (cfb-app/**) triggers .github/workflows/deploy.yml,
REM which builds and deploys to Cloudflare Pages.
REM Usage: agent\daily_publish.bat   (scheduled as EdgeIndexPublish)
REM Each step stops the chain on failure so nothing half-done is pushed.

setlocal
cd /d %~dp0..
set LOG=agent\logs\publish_%date:~-4%-%date:~4,2%-%date:~7,2%.log
echo ===== %date% %time% ===== >> %LOG%

echo [1/3] Pulling main (bot commits from the card and receipts workflows)...
git pull --ff-only >> %LOG% 2>&1
if errorlevel 1 (
    echo PULL FAILED — local changes or a diverged branch. Not running the routine. See %LOG%
    exit /b 1
)

echo [2/3] MLB morning routine (grades yesterday, builds today's card, updates the MLB site files)...
python backtest\mlb\morning_routine.py
if errorlevel 1 (
    echo ROUTINE FAILED — nothing committed. See %LOG%
    exit /b 1
)

echo [3/3] Committing and pushing the MLB site files...
REM RecordTracker.jsx (record), MLBHub.jsx (Full Card), daily_card.json + record.json (K Board) — all written by the routine.
git add cfb-app/src/RecordTracker.jsx cfb-app/src/MLBHub.jsx cfb-app/public/data/daily_card.json cfb-app/public/data/record.json
git diff --cached --quiet
if not errorlevel 1 (
    echo Nothing changed — no commit, no deploy. >> %LOG%
    echo Nothing changed today; site left as is.
    goto :done
)
git commit -m "MLB daily update %date:~-4%-%date:~4,2%-%date:~7,2%" >> %LOG% 2>&1
git push >> %LOG% 2>&1
if errorlevel 1 (
    REM a bot commit landed while the routine ran: replay ours on top once and retry
    git pull --rebase >> %LOG% 2>&1 && git push >> %LOG% 2>&1
    if errorlevel 1 (
        echo PUSH FAILED — committed locally but not pushed; the site will not update. See %LOG%
        exit /b 1
    )
)
echo Pushed; deploy.yml will build and deploy. >> %LOG%
echo Pushed. GitHub Actions (deploy-site) builds and deploys: https://www.edge-index.com

:done
echo Done. >> %LOG%
endlocal
