# P10 clean rebuild results — checkpoint 1

State: PARTIAL — full phase gate OPEN

## Implemented
App-open schedule anti-overlap primitives, stable-file watcher, owned-cache cleanup with leases, resource metrics/admission helpers and batch/rolling dependency planner.

## Evidence
Watcher stable/change/output exclusion, schedule overlap/misfire, safe cache, resource-denial tests passed.

## Remaining / NOT RUN
Automation helpers are NOT yet all wired into desktop scheduler/settings. Adaptive resource hysteresis, per-tool/account leases, app-closed Windows opt-in scheduling, full DAG failure propagation/progress/ETA remain open.

Baseline evidence is not clean-code evidence. No claim that an entire requirement group passes from a single example.

## Checkpoint 2 — latest
Explicit app-open stable-file watcher now wired into Settings, output/cache/profile exclusions, job-kind admission and RAM/disk reserve connected. Full DAG/source-side checkpoint/resume, adaptive hysteresis, per-account/tool leases and app-closed scheduling still open.
