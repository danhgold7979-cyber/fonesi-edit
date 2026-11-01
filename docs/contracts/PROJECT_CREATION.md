# Explicit empty project creation (foundation, not Editor acceptance)

The overview's **Create blank project** button opens a modeless form without adding
sample assets or a simulated timeline. The form states all initial output-intent
defaults: MP4/H.264/AAC, yuv420p/BT.709,48kHz stereo, no normalization/limiter,
seed0 and no preset. These are intended settings only, never tested codec support.
Name, even pixel geometry, exact rational FPS and duration are explicit. The
initial creation form bounds geometry to2..16384 and numerator/denominator controls
to1..1000000; this is a provisional form limit, not a new CompositionPlan format
restriction. Broader output settings/editor controls remain their canonical tasks.
Fresh project/plan UUIDs and empty asset/clip/layer/font/audio collections produce
an actual schema/semantic-validated project, with no invented source/account IDs.

`create_project_file` reuses the existing reviewed project writer with
expected_digest=None: new destination only, no overwrite authority. The worker
owns no SQLite connection. Before entering the writer, cancellation creates nothing;
once entered, cancellation is not rollback. Any non-conflict failure is UNKNOWN,
with no retry, destination deletion or optimistic rollback claim. Existing shared
writer cooperating-namespace/advisory-lock and unique-staging assumptions remain
unchanged; this slice does not claim hostile namespace-safe cleanup.

Only confirmed file write and matching readback return CreatedProject. On the GUI
thread, activation rechecks captured session object/revision, exact created digest
and entire project, and absence of a prior same-ID recovery row, then uses existing
prepare_open/choose. Failure preserves the old active session; the created file
remains available for explicit Open/reconciliation. No implicit project DB write is
needed until the existing completed-command autosave path is used.

The modeless dialog does not crowd the overview. Close requests cancellation and
waits for the owned worker; it never destroys or terminates a running QThread.
Cancellation is latched by the UI per attempt (QThread interruption flags may clear
after completion), so late confirmed creation remains on disk but cannot activate
after cancel/close. Stale active-session/revision also prevents activation. UNKNOWN
permanently disables further creation in that panel; changing destination is not a
retry bypass. Old active session and its Save/Open remain available. Confirmed
creation can be inspected/reopened explicitly. No automatic cleanup is added.

This advances P03 project lifecycle foundation only. It does not provide an editor,
media import, rendering, new preset system, full project recovery or phase completion.
