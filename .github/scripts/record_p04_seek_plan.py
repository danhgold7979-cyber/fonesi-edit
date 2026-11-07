"""Append the next reviewed P04-06 implementation slice before code changes."""
from pathlib import Path

path = Path("docs/phases/P04_PLAN.md")
text = path.read_text(encoding="utf-8")
marker = "## Slice AS — exact rational preview seek plan (P04-06)"
if not text.startswith("# P04"):
    raise RuntimeError("unexpected P04 plan identity")
if marker in text:
    raise RuntimeError("Slice AS plan already exists")
section = r'''
## Slice AS — exact rational preview seek plan (P04-06)

**Purpose:** establish one pure, immutable and exactly rational mapping from an output-frame playhead to the selected video stream and all currently active matching original-role audio streams. This is the shared seek contract required before any synchronized preview transport can be implemented; it does not decode media, generate a persistent proxy, play audio/video, certify codec support or claim preview/export parity.

**Inputs and identity:** accept only a validated `CompositionPlan`, one existing selected video clip ID and a nonnegative integer output-frame index. Capture the plan ID/revision, exact output frame rate and exact output time in the result. Reject image clips, freeze-frame clips, missing/ambiguous stream references, invalid frame indices and playheads outside the selected clip's half-open moving interval. The function must not mutate the plan or filesystem.

**Exact mapping:** map output time through the selected clip's `output_start`, `source_in` and `speed` to one exact source-relative timestamp, then add the selected stream's exact `start_time` to obtain the decoder timestamp. For audio, include every active `role == original` clip bound to the same asset, applying each audio clip's own output interval, trim, speed and stream start. Sort audio seeks deterministically by stream index and clip ID. No matching audio is represented by an empty tuple, not a fabricated stream or fallback.

**Integration boundary:** the existing one-frame still-preview request must consume the new seek plan instead of reimplementing video timestamp arithmetic. Existing filmstrip sampling and waveform observation remain unchanged in this slice because they have different interval/window semantics. Generation/revision/clip stale-result checks, explicit FFmpeg trust and content-bound cache rules remain authoritative.

**Tests before acceptance:** cover base video/audio mapping with differing stream starts; trim, non-unit speed and nonzero output offsets; multiple active original audio clips; no-audio output; half-open clip end rejection; invalid clip/frame/freeze refusal; deterministic ordering; canonical plan immutability; and UI proof that one-frame preview passes the helper's exact stream/timestamp into the existing worker. Run affected preview/media tests plus the full clean-foundation Linux/Windows Python 3.12/3.13 matrix on an exact descendant commit.

**Acceptance boundary:** passing these tests proves deterministic rational seek planning only. Physical Windows device timing, real-media corpus seek accuracy, audible A/V synchronization, continuous playback, proxy generation/invalidation, GPU decode and render/export parity remain open P04-06/P02/P07 gates. P04-06 and P04 remain IN_PROGRESS; no ED-17 acceptance criterion changes in this slice.
'''
path.write_text(text.rstrip() + "\n\n\n" + section.strip() + "\n", encoding="utf-8")
