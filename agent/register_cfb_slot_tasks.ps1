# Registers one Windows scheduled task per CFB line-capture slot (Tim, 2026-10-19).
# Each task wakes the computer and runs:  python -m engine.cfb.lines.trigger --slot <name>
# which dispatches the cfb-lines workflow's `slot` input (GitHub's own crons run hours late).
# Times are ET (this machine runs Eastern time), 2 minutes after each slot. Re-running this script
# replaces the tasks. Remove them all with:  Get-ScheduledTask -TaskPath "\EdgeIndex\" | Unregister-ScheduledTask -Confirm:$false
# Requires: the token file %USERPROFILE%\.edge-index\gh_actions_token.txt (see engine/cfb/lines/trigger.py)
# and, for wake-to-run, "Allow wake timers" enabled in the active power plan.
# Runs "whether user is logged on or not" (S4U: no stored password, no network-share access, which the
# trigger doesn't need), so it must be run from an ELEVATED PowerShell. Wake timers wake the PC from
# sleep only: a shut-down PC (Fast Startup) is not woken, and the task runs at the next boot instead.

$ErrorActionPreference = "Stop"
$Repo   = Split-Path -Parent $PSScriptRoot
$Python = (Get-Command python).Source
$Slots  = @(
    @{Name="sun18"; Day="Sunday";    Time="18:02"},
    @{Name="sun22"; Day="Sunday";    Time="22:02"},
    @{Name="mon09"; Day="Monday";    Time="09:02"},
    @{Name="tue10"; Day="Tuesday";   Time="10:02"},
    @{Name="wed10"; Day="Wednesday"; Time="10:02"},
    @{Name="fri10"; Day="Friday";    Time="10:02"},
    @{Name="tue18"; Day="Tuesday";   Time="18:02"},
    @{Name="wed18"; Day="Wednesday"; Time="18:02"},
    @{Name="thu18"; Day="Thursday";  Time="18:02"},
    @{Name="fri18"; Day="Friday";    Time="18:02"},
    @{Name="sat11"; Day="Saturday";  Time="11:02"},
    @{Name="sat15"; Day="Saturday";  Time="15:02"},
    @{Name="sat19"; Day="Saturday";  Time="19:02"}
)
$Settings = New-ScheduledTaskSettingsSet -WakeToRun -StartWhenAvailable -AllowStartIfOnBatteries `
            -DontStopIfGoingOnBatteries -ExecutionTimeLimit (New-TimeSpan -Minutes 10)
$Principal = New-ScheduledTaskPrincipal -UserId "$env:USERDOMAIN\$env:USERNAME" -LogonType S4U -RunLevel Limited
foreach ($s in $Slots) {
    $Action  = New-ScheduledTaskAction -Execute $Python -Argument "-m engine.cfb.lines.trigger --slot $($s.Name)" -WorkingDirectory $Repo
    $Trigger = New-ScheduledTaskTrigger -Weekly -DaysOfWeek $s.Day -At $s.Time
    Register-ScheduledTask -TaskName "CFB lines $($s.Name)" -TaskPath "\EdgeIndex\" -Action $Action `
        -Trigger $Trigger -Settings $Settings -Principal $Principal -Description "Dispatch cfb-lines slot $($s.Name)" -Force | Out-Null
    Write-Output "registered CFB lines $($s.Name): $($s.Day) $($s.Time) ET"
}
