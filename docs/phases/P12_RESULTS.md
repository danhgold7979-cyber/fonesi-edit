# P12 clean rebuild results — checkpoint 1

State: PARTIAL — full phase gate OPEN

## Implemented
Runtime CLI entry and frozen-worker dispatch design available; third-party notices preserved.

## Evidence
Packaging NOT RUN on clean code.

## Remaining / NOT RUN
Clean frozen Linux and Windows builds/worker proofs, dependency bundle checks, installer/update/rollback acceptance, final Vietnamese guide and release criteria remain open.

Baseline evidence is not clean-code evidence. No claim that an entire requirement group passes from a single example.

## Checkpoint 2 — latest
Clean frozen Linux build passed UI +4 subprocess jobs (batch/matrix/yt-dlp/gallery-dl) +source preservation +35-source hash audit. Two packaging failures were diagnosed/fixed without weakening TLS: Qt/system FFmpeg shared-library shadowing; missing executor stdlib TLS adjunct. Windows CI now builds and executes same proof with pinned9.0.2 tool artifact; Windows NOT RUN until that exact commit completes. Build manifest records dirty working tree honestly, source hashes match checkpoint code. Public redistribution licensing/target user-machine acceptance still open.
