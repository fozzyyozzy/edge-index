@echo off
REM Edge Index — daily publish: routine -> rebuild -> deploy, in that order.
REM Usage: agent\daily_publish.bat   (or schedule it after games end / before noon)
REM Each step stops the chain on failure so a stale build never ships.

setlocal
cd /d %~dp0..
set LOG=agent\logs\publish_%date:~-4%-%date:~4,2%-%date:~7,2%.log
echo ===== %date% %time% ===== >> %LOG%

echo [1/3] Morning routine (grades yesterday, builds today's card, updates src)...
python backtest\mlb\morning_routine.py
if errorlevel 1 (
    echo ROUTINE FAILED — not building or deploying. See %LOG%
    exit /b 1
)

echo [2/3] Building app (src -^> dist)...
cd cfb-app
call npm run build
if errorlevel 1 (
    echo BUILD FAILED — not deploying. Fix errors above.
    cd ..
    exit /b 1
)

echo [3/3] Deploying to Cloudflare Pages (production branch)...
call npx wrangler pages deploy dist --project-name=edge-index --branch=main --commit-dirty=true
if errorlevel 1 (
    echo DEPLOY FAILED — site unchanged.
    cd ..
    exit /b 1
)
cd ..

echo Done: routine + build + deploy complete. >> %LOG%
echo.
echo ✓ Published. Hard-refresh (Ctrl+F5) to verify: https://www.edge-index.com
endlocal
