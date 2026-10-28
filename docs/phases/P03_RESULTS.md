# P03 clean rebuild results — checkpoint 1

State: PARTIAL — full phase gate OPEN

## Implemented
Qt-independent versioned project model; rational time maps; immutable SQLite jobs, dependencies, pause/cancel/retry/lease recovery; process groups; safe artifact publication; backup/autosave.

## Evidence
18 core + real subprocess queue tests passed; included in final 51-test suite.

## Remaining / NOT RUN
Migration beyond initial schema, sustained crash campaign, resource-aware admission integration, fully immutable resolved tool leases and Windows process-tree acceptance remain open.

Baseline evidence is not clean-code evidence. No claim that an entire requirement group passes from a single example.

## Checkpoint 2 — latest
Resource admission now wired into scheduler, separate render/download/probe limits, failed required-dependency propagation, pending-only priority/snapshot APIs. Real worker dispatch verified from frozen executable. Remaining: exhaustive migration/crash Windows matrix and atomic artifact/history guarantees under kill boundaries.
