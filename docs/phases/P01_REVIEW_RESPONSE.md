# Response to independent review of4916a67

All changes below require independent recheck; P01 remains NOT_ACCEPTED. No runtime results claimed.

| Finding | Correction | Verification |
|---|---|---|
| Normative prose omitted, broad candidate mappings | All nonheading/nonfenced source prose/bullets/table data now mapped explicitly to child IDs;12 context/header exclusions have reasons.438 child assertions/392 source records (389 source-spec clauses+3 preserved group records). Added no single-key destructive shortcuts, reliable word-timestamp constraint, Vietnamese/custom output folders, text case, colors/readability presets and every shortcut row | check_plan checks exact source bytes/line, forward/reverse child links, no unmapped prose/table/bullet except explicit exclusions; semantic review still required |
| Hash+journal could adopt foreign identical file | Retain staged hardlink through final-set commit; physical open-handle volume/file identity required for both staged and final; unknown/lost proof conflicts/quarantines, never adopt by hash/planned path | JOBS mandatory foreign-identical-file crash-before-link regression specified; not implemented yet |
| Multi-artifact early job success | Per-artifact commit inserts artifact only; immutable required-set readback then one final job/history transaction | Kill after video commit/before subtitle/final-set transaction specified; not implemented |
| Path excluded in prose but canonical full hash included | Separate full execution_snapshot_digest and explicit render_content_digest projection including stream/font/time/tool semantics | Same bytes relocated path golden test plus changed-stream/font/time negative cases specified |
| Streams/cue time binding ambiguous | Explicit selected video/audio stream indices; cue source/output basis, asset/track/segment refs; resolved output cue per occurrence | Schema required fields checked structurally; repeated/same asset twice/delayed alternate-stream semantic cases specified |
| Dependencies/cycles block independent work | Machine-readable101-node acyclic artifact readiness graph and94 separate acceptance records; P03 dev/account schema local milestones, P06 model→P07 style→render→P06 burn-in acceptance | DFS dependency validation PASS; artifact readiness explicitly not full acceptance |
| Running cancel contradiction | P03-05 allows coordinator running cancellation, forbids only running snapshot update | Text contract aligned with JOBS states |
| R09 value vs time and ducking target | Relative keyframe comment uses keyframe.time; duck targets/source clips/mode/threshold explicit pre-sum, not master narration attenuation | Schema design checks field/comment invariants; semantic audio tests remain future |

Checks after correction: `python scripts/check_plan.py` PASS; `python scripts/check_schema_design.py` PASS1 valid/20 rejected cases plus required-field invariants; `python -m py_compile scripts/check_plan.py scripts/check_schema_design.py` PASS. All are P01 design integrity checks, no application acceptance. Source specs remain untouched.

## Targeted recheck7136521 residual corrections

- Typed per-stream video/audio/subtitle/image records replace global probe geometry/audio fields; includes actual subtitle stream representation. Complete structural example has2video+2audio+subtitle streams with distinct geometry/sample rates/start offsets and explicit clip/audio/cue bindings. Decoder PTS versus output-placement formulas prevent applying stream offset twice.
- Seven lost conjunctions restored directly in child assertions: no machine-wide PATH modification; explicit click/auto-update opt-in before download/install; same-auth multiple pages/channels do not need extra profile; fit25/50/100/200/custom zoom+pan; recording-OFF base-edit/scope prompt; easing curve display/preview; profile color/label/version/check.
- Design validation now2 positive examples and22 rejected invalid vectors (including audio/video metadata separation and required subtitle format). Runtime semantic R01–R15 remains NOT_IMPLEMENTED.
