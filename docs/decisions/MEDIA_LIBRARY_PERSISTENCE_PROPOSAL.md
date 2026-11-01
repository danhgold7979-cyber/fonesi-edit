# P03 media persistence — local implementation, pending source/native acceptance

Scope: P03-02/03 stable-ID unresolved-capable source records and P03-07 compatible
project persistence. Media-bin/import/drop UI belongs P04-01 and requires separate
artifact entry/phase branch, not relabelling it as completed P03. Root approved
preparing this design on2026-11-01; independent design review is recorded in P03_MEDIA_LIBRARY_PERSISTENCE_DESIGN_REVIEW.md; source review is pending.

## Separate observation from executable composition

A project source library must accept content-bound observations with missing
metadata, no audio, signed starts, attached pictures/data/unknown streams, rotation
matrix facts and unresolved frame coverage. It must not force incomplete observations
into render-ready CompositionPlan assets or fabricate duration/FPS/layout/orientation.
A library item never grants executable trust, output validation or renderer readiness.
Frame-scan records are not included in this initial envelope (bounded summary may be
added later); EOF alone remains no complete-map/media-validity proof.

## Project envelope evolution

- Continue reading v1 exactly; read-only open never rewrites file/DB or creates a
  backup. Existing v1 projects with only composition data retain v1 serialization.
- Introduce v2 only for an explicit completed command adding a source-library field.
  Keep v2 even if its last item is removed; no implicit downgrade. No SQLite table
  migration is needed: existing project documents are versioned JSON and existing
  ProjectStore CAS protects their row version.
- Future versions fail closed before overwrite. V1 readers must reject v2 rather
  than drop the library. Existing file save expected-digest and backup behavior
  protects concurrent old writers; old in-memory store writers still require CAS.
- Update EVERY Project reconstruction (autosave recovery, same-content relink,
  root relink, creation/copy) to preserve the library explicitly. Do not silently
  drop v2 data when only CompositionPlan changes. Existing project-relative
  composition references keep their original-base semantics.
- Initial library paths can be absolute or project-relative using the same explicit
  path_ref semantics; relative origins must participate in recovery/relink/SaveAs
  restrictions, not be resolved against cwd. Unresolved origin remains explicit.

## Item identity and record

Each item has a project-stable UUID, content SHA256, path_ref bound to that SHA,
content size observation, typed MediaObservation and a versioned observation format.
Identity is assigned once at first import; same-content relink/rename preserves it.
A duplicate-content policy must be explicit (reuse/no-op vs explicit relink), never
silently replace metadata or bind different bytes to an existing ID. SHA alone is
not a deletion/ownership capability. Existing composition asset IDs remain intact;
no automatic library-to-composition conversion or ambiguous legacy-ID conflation.

Persist only sanitized typed observation fields already exposed by normalize_probe,
not raw ffprobe tags/URLs/tool output/credentials or trusted executable paths. Unknown
facts stay None; stream index remains container-global and list order is retained.
All serialized fields require exact names/types, bounded strings/collections, unique
stream indices and canonical rationals. Derived tick*time_base values may need up
to192bits: storage bounds must roundtrip valid current observations, not repeat the
previous typed-vs-reader rational mismatch. The implemented symmetric bound is256bits for canonical rational numerator/denominator.

## Commands, safety and tests before implementation acceptance

- Import preparation does read/hash/probe off GUI thread with existing typed process
  retirement. Applying is a separate completed command bound to exact captured
  project/session/revision. Unknown retirement cannot be erased by editing paths.
- Content changes between observation and apply must refuse or require fresh
  observation; no metadata-only check masquerading as byte immutability. Do not hash
  large sources on the GUI thread. Initial pure persistence tests can use explicit
  trusted constructed observations without claiming actual file admission.
- Same-content relink extends existing source/font machinery to library references,
  updates all linked representations deliberately, and is atomic in memory before
  CAS. Different content requires separate explicit replacement, not relink.
- Regressions: v1 read/save unchanged bytes; v2 save/reopen/autosave recovery preserves
  all library facts/IDs; future/malformed data fails without writing; copies/relink
  never drop library; signed time/unknown/no-audio/multi-stream/attached-picture
  roundtrip; duplicate ID/content conflict; bounded huge/NUL/float/noncanonical data;
  moved project base and root relink; process-kill/CAS/write-unknown behavior.

## Chosen local implementation and remaining gates

The local pure persistence slice uses independent canonical UUIDs and at most10,000
records, each at most256 streams. Exact same SHA/path/size/observation is a no-op
returning the existing ID, regardless of proposed fresh ID; conflicting same-SHA
facts refuse and require explicit relink/refresh. No automatic legacy asset linkage.
NOT_PROBED/PROBE_UNAVAILABLE carry no observation; OBSERVED remains render_ready=False.
Typed input and deserialized input use the same fact validation, including tick-based
times, content hashes, immutable arrays and explicit unresolved reasons. Paths have
32,768-character cap, non-NUL and explicit absolute/project-relative base. This is
an envelope bound, not a promise the OS supports every such path.

V1 library=None remains byte-compatible; explicit empty MediaLibrary stays v2.
Project.with_plan preserves the library for composition-only changes. add_media
advances the existing composition/project revision exactly once and returns a
CompletedCommand; duplicate no-op returns no command. Recovery and both relink paths
preserve IDs/facts and account for library-only relative references; unknown original
base refuses. Whole envelope writes stream JSON projections with a33MiB UTF-8 bound
before file mutation, sharing the existing reader bound. No database table change.

Source tests cover new-domain roundtrip/invalid facts, command CAS, file+SQLite
reopen, moved-origin recovery, mixed legacy/library root relink, bounded serialization,
and actual owned-v1 migration backup→restore→reopen containing a v2 document.
The first backup test correctly refused an unmarked test database; its fixture was
corrected to register the known exact legacy schema, not by weakening ownership.

Still OPEN: actual file observation/admission→command binding, P04 import/bin UI,
refresh/remove commands, composition conversion, renderer and frame-map readiness.
Existing SQLite load query blob allocation has not been redesigned by this slice;
whole-envelope parse/write bounds are not a general database-memory bound.
No new dependencies/tool execution or P03 task/child acceptance is inferred.

Source-review corrections: v2→v1 is explicitly refused at completed-command,
repository update and matched existing-file write boundaries, before mutation.
An explicit empty v2 library remains valid. UUID/content conflict detection scans
all existing UUIDs before duplicate-SHA no-op, so result does not depend on order.
