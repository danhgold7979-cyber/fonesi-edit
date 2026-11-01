# Queue progress transport — source CLEAR in bounded scope

2026-11-01. Independently verified all six supplied dirty SHA256 pins (inbox, observations, view, queue UI, new tests, contract), atop unpublished 6c43609 checkpoint. Read-only review; no aggregate/native/FFmpeg repeat.

Bounded latest-per-job numeric observations, canonical identifiers/hash and attempt validation, fixed event capacity and deterministic oldest eviction prevent an unbounded Qt signal stream. Inbox builds observers on owner thread and reuses existing lease/snapshot/token authority checks; observation transport has no write/publication authority. Close retires the transport. The corrected close/admission lock remains intact.

Queue projection exposes hash only, not snapshot content/request keys/paths. UI matches store, job, snapshot and attempt and refuses painting canceled/non-running/publication-held rows. Initial and failed reads do not consume pending events; refresh clears previous labels. Stream end explicitly does not mean successful job completion. Timer stops at page retirement. Completed/stale observations are not execution authorization.

Independent selected tests: real owned Python producer stdout → Qt counters → actual selected cancel → same owner inbox → process retirement → database acknowledgment; store/hash/attempt/final-row filters. **2 PASS / 3 deselected, exit 0.** No previous inbox tests rerun.

No blocker found. Source CLEAR for the supplied optional owner-route integration and corresponding targeted CI. Default shell still has no scheduler/executor; no full P03-04/P03-05 or OPS-02.02 closure, no FFmpeg/native Windows inference. Progress is best-effort, based on the last successful queue snapshot rather than an atomic live DB subscription; coalescing/overflow intentionally loses observations, not jobs. A scheduler must refresh durable state at lifecycle transitions and connect its real owner route before this becomes default end-to-end functionality.

## Integration test oracle adjustment, 12:39 UTC
Verified test_queue_view.py SHA256 `1d1a009920634f17f40d488c279e60c86cacd750453c9674229a323805cb2263`. Replacing blanket substring `snapshot` rejection is correct for the deliberately reviewed hash-only projection. Exact field allowlist, persisted-hash equality, absence of request-key sentinel, absence of snapshot_json field/content retain and sharpen the intended secrecy boundary. No application source change. Source/test adjustment CLEAR; no duplicate aggregate or focused test rerun. Author reports initial aggregate 573 PASS / 36 SKIP / 1 obsolete-oracle failure and corrected focused test 1 PASS; preserve failed aggregate as historical, do not label original aggregate green.
