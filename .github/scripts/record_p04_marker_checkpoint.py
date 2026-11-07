"""Append the verified P04-05 marker-drag checkpoint to active project ledgers."""
from pathlib import Path


def append_once(path: str, marker: str, section: str, required_prefix: str) -> None:
    target = Path(path)
    text = target.read_text(encoding="utf-8")
    if not text.startswith(required_prefix):
        raise RuntimeError(f"{path}: unexpected document identity")
    if marker in text:
        raise RuntimeError(f"{path}: checkpoint already present")
    target.write_text(text.rstrip() + "\n\n\n" + section.strip() + "\n", encoding="utf-8")


append_once(
    "docs/phases/P04_RESULTS.md",
    "## Slice AR — viewport-routed marker drag and cancel semantics",
    r'''## Slice AR — viewport-routed marker drag and cancel semantics (P04-05, 2026-11-07)

Implementation commit: [`b14c409c8abbcb34d6d94b4ded5ca1c5f2571ed6`](https://github.com/danhgold7979-cyber/fonesi-edit/commit/b14c409c8abbcb34d6d94b4ded5ca1c5f2571ed6). The exact guarded candidate diff was tested by targeted workflow run [`42341716342`](https://github.com/danhgold7979-cyber/fonesi-edit/actions/runs/42341716342), which completed SUCCESS on Ubuntu 24.04 / Python 3.12 and then committed that tested diff to `develop/fonesi-full`.

Implemented:
- `TimelineGraphicsView` routes marker press/move/release through real viewport-local coordinates, scans the full item stack below the mouse-transparent playhead and clamps movement through the existing marker item bounds.
- Marker mutation now binds the canonical `session.project.id`, not the composition-plan ID, so the existing stale-project/revision CAS guard accepts the active project and still rejects stale callbacks.
- A successful drag commits exactly one shared-history command; undo/redo and project-file save/reopen preserve the moved frame.
- Collision refusal restores the prior marker frame without creating a project revision. Escape first cancels an active marker drag and restores its visual origin; when no drag is active it retains the existing In/Out clear behavior. Press/release without movement is a no-op.
- Offscreen regression input uses explicit `QMouseEvent` viewport-local coordinates because Qt's virtual global cursor can be clamped on a small offscreen screen. Assertions still exercise the production viewport event path and were not weakened.

Targeted regression evidence:
- `test_timeline_marker_viewport_drag_commits_once_and_shared_undo_redo`
- `test_timeline_marker_drag_collision_and_escape_do_not_create_commands`
- Result: 2 passed, 0 failed in the guarded apply job. Temporary transfer workflow/script/patch files were deleted by the successful product commit.

Acceptance boundary: this is targeted hosted Linux/Qt-offscreen evidence, not the required exact-HEAD four-runner foundation result and not physical Windows mouse, mixed-DPI/HiDPI, screen-reader, IME, real-media, synchronized A/V seek or render/export acceptance. P04-05 and P04 remain IN_PROGRESS; ED-17 criteria and all acceptance counters remain unchanged pending complete criteria and external gates.''',
    "# P04 — Implementation results and acceptance ledger",
)

append_once(
    "docs/phases/P04_PLAN.md",
    "## Slice AR — viewport-routed marker drag and cancel semantics",
    r'''## Slice AR — viewport-routed marker drag and cancel semantics (P04-05)

**Entry condition:** marker rename, frame-only loop, rational clip move and gap/ripple delete already exist, but viewport marker reposition remained unverified and the first Linux offscreen tests exposed deterministic failures.

**Observed defects:**
- The marker item captured the composition-plan ID while the release callback compared it with `ProjectSession.project.id`, so every legitimate release was rejected as a stale project.
- Qt offscreen clamps the virtual global cursor; `QTest.mouseMove` could deliver a different local coordinate for a wide timeline viewport.
- The playhead is visually above markers, requiring full item-stack lookup rather than top-item-only hit testing.
- The shared shortcut router consumed Escape before the view could cancel an active drag.

**Implementation contract:** use a dedicated `TimelineGraphicsView` to own marker viewport gesture state; bind the canonical project ID and current revision at marker construction; commit only once on a changed, non-cancelled release; restore without revision on collision, Escape or no movement; preserve Escape's In/Out clear action when no marker drag is active. Tests must send exact local viewport mouse events while retaining all command-count, persistence, collision and cancellation assertions.

**Verified targeted result:** guarded Ubuntu 24.04 / Python 3.12 run `42341716342` passed both marker regressions and committed product SHA `b14c409c8abbcb34d6d94b4ded5ca1c5f2571ed6`.

**Remaining gate:** run the full clean-foundation Linux/Windows Python 3.12/3.13 matrix on an exact descendant checkpoint before treating the slice as cross-platform regression-verified. Physical Windows pointer/HiDPI acceptance remains external. P04-05/P04 stay IN_PROGRESS; no ED-17 criterion is accepted. After this gate, continue the next independent P04-06 proxy/seek slice without claiming continuous playback or preview/render parity.''',
    "# P04",
)

append_once(
    "docs/CURRENT_STATUS.md",
    "## P04 marker-drag product checkpoint — 2026-11-07",
    r'''## P04 marker-drag product checkpoint — 2026-11-07

Repository `danhgold7979-cyber/fonesi-edit`, integration branch `develop/fonesi-full`; release branch `main` remains unchanged and no merge was performed. Product commit [`b14c409c8abbcb34d6d94b4ded5ca1c5f2571ed6`](https://github.com/danhgold7979-cyber/fonesi-edit/commit/b14c409c8abbcb34d6d94b4ded5ca1c5f2571ed6) fixes P04-05 marker viewport drag by using canonical project identity, a viewport-local gesture router, full stacked hit testing and contextual Escape cancellation.

Targeted hosted run [`42341716342`](https://github.com/danhgold7979-cyber/fonesi-edit/actions/runs/42341716342) passed both exact marker regressions on Ubuntu 24.04 / Python 3.12 and committed the tested diff. It verifies one commit for successful drag, shared undo/redo and save/reopen persistence, collision refusal, Escape rollback and no-op press/release. It is not a completed four-runner clean-foundation result.

A user-authored descendant verification commit must run Ubuntu and Windows Python 3.12/3.13 against the exact product tree because GitHub does not recursively trigger workflows from a `GITHUB_TOKEN` push. Until that matrix is green, latest cross-platform status remains pending. Physical Windows pointer/HiDPI/IME, continuous playback, synchronized A/V seek, real-media/GPU/Chrome/provider and render/export gates remain open. P04-05 and P04 remain IN_PROGRESS; global task/criterion acceptance counts are unchanged.''',
    "# Current clean rebuild status",
)
