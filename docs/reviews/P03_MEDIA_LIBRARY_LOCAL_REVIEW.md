# P03 media-library persistence — source HOLD pending two causal fixes

2026-11-01 17:09 UTC. Reviewed frozen local slice atop8955252, media_library4ee7f1fd…, projectsdf994454…, media_commands823dae6d…, autosave5d2ed45b…, relink412d6f1a…. No publication or native tool execution.

## Required fixes

1. HIGH — ProjectSession.commit accepts v2-to-v1 downgrade through a correctly advanced CompletedCommand(Project(id,name,newplan)). Independent real temporary SQLite reproduction: add_media persists v2, next legitimate revision constructed with legacy three-field Project persists library=None both in session and durable row. Preservation helper alone does not enforce the no-downgrade contract. Refuse before mutation; explicit removal of last item must retain v2 empty library. Also enforce equivalent rule at direct current-CAS ProjectStore.save and existing-file save boundaries. A valid CAS/digest is concurrency authority, not explicit authorization to silently discard the new field. Verify session/durable row/file bytes unchanged.
2. MEDIUM — MediaLibrary.add checks ID collision and SHA duplicate in one ordered loop. For library(A/idA/hashA,B/idB/hashB), adding A content/metadata with idB returns A no-op before examining B; reversed order raises conflict. Independently reproduced. Precheck UUID ownership across all records before duplicate-content early return; regression both orders.

## Otherwise coherent inspected scope
Explicit None/v2-empty version discriminator; exact immutable record schemas and unknown/observed states; no render readiness; independent stable UUIDs; hash/path/observation consistency, tick-derived signed timing checks, bounded canonical256-bit rationals,256streams and sanitized fields. Existing v1 canonical serializer shape preserved; whole-envelope33MiB limit checked incrementally before writer effects, record projection avoids eager whole-library asdict. Existing composition and library references included in recovery origin predicates and atomic root relink; same-content legacy relink preserves library. Pure commands advance existing plan revision. Backup restore uses existing parse path and tests populated v2 content.

Independent selected pytest run: 4 PASS /30 deselected, exit0: library-only original-base recovery/SaveAs guard, mixed root relink, streaming envelope early cutoff, >128-bit derived rational roundtrip. No repeated full suite. Two additional standalone causal reproductions above succeeded in demonstrating defects; they are not acceptance tests.

Workflow fe4191f9076163ef20dccbe0846fc30a84f331f07c970e19fdd0c974a2aa9f2a: [media-library] alone keeps four targets and LinuxQt,13 affected storage/recovery/relink/creation UI files (author collected162 before new regressions). Unchanged aggregate/schema/frozen/candidate execution skipped; ordinary default unchanged. Workflow scope acceptable, but source remains HOLD pending fixes. Existing unbounded SQLite document SELECT and cooperating file namespace limitations are not newly solved or claimed solved. No real admission/P04 media-bin/render or child/task acceptance.

## 17:10 UTC correction recheck — both findings CLOSED; source/workflow CLEAR

Verified exact final hashes: media_library84e6b90df37f1f0364d0e25954a2196bbae1d4dee208b7f3f9cca95d3dbbce0e, projectsd1e5ebe41089ff8614a407cebcc39893e7ab18b5dcc24a93e50a50ffe4687304, autosave3bd552ab96d9ca91562dfcecd1e2fe4979b0f85148c06083a4eddd1ec8c89d4f, test_media_library565a81499f4d8d9488b7c763fd3d653e1b0630c2192c9cf19ed043ad25653745, test_project_media_library43e9ed83fdfcbd6828074f89207ec32f9eda60cdc9e9b1b9cfde217a5cecb3f0.

UUID ownership conflict is checked across the entire library before any SHA duplicate return. V2-to-v1 refusal occurs before session persistence, within the existing database transaction before UPDATE, and under existing project file lock after digest/identity check but before staging/backup. Explicit empty-v2 removal remains supported. Independent exact three regression instances PASS, exit0: both item orders and combined real session/database/file no-downgrade + empty-v2 positive. No unchanged four cases or aggregate repeated. Initial failed author fixture had no durable row; corrected fixture seeds it and makes meaningful before/after row assertions.

Source and unchanged fe4191f9 workflow CLEAR for scoped four-target validation (author collection now165). This closes the two causal review blockers, not hosted result/real source admission/render/P04/fulltask acceptance. Earlier HOLD text is retained as review history and superseded by this correction section.
