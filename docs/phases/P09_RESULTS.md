# P09 clean rebuild results — checkpoint 1

State: PARTIAL — full phase gate OPEN

## Implemented
Natural scene sort/content IDs; bounded seeded lazy W/K/unique solver, exhaustive small-space proof vs bounded timeout; editable matrix revalidation, CSV, per-row project/queue and transactional reservation/history primitives.

## Evidence
Small full-product oracle, strict W/K, huge product bounded search, cancel/timeout, locked candidate and history tests passed.

## Remaining / NOT RUN
Full persisted historical sequence fed into UI solver, atomic enqueue-reservation coupling and failed reservation transitions, scene/angle/row locking UI, rename rollback and duration-allocation UI still need integration.

Baseline evidence is not clean-code evidence. No claim that an entire requirement group passes from a single example.

## Checkpoint 2 — latest
Natural scene/render pipeline passed from frozen worker. Reservation/history and editable matrix remain partial; persisted history must still be fed to UI solver and enqueue/reservation made atomic.
