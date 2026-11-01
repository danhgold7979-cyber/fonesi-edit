# Local project autosave/session review

Initial supplied SHA256 verified:
- storage/autosave.py 1d26f901a6b1ee126205bcbd6a8efdf3ff04c0515e516a348d7be9bf61896c44
- tests/test_autosave.py a990aaf1731c72fc4edd2b1f7c59f094a060a3331d28a281c4f92b337c108c46
- PROJECT_RECOVERY.md 2ae781504775e6517ad4e2745f378b8898448ad4912ecb92308173b8f8abbf33

Verdict HOLD: unknown-outcome classification defect through existing writer.

ProjectSession.save treats every ConflictError as known before mutation. Existing projects._project_lock catches PermissionError/BlockingIOError around yield, meaning the complete writer body. A post-publication PermissionError is converted to ConflictError. Independently reproduced by fault('after_publish')->PermissionError through the real file writer: disk contains edited project, exception ConflictError, session.reconciliation_required=False. This permits further session writes despite the intended uncertainty latch.

Required fix: narrow contention/permission conversion to actual lock acquisition, not writer yield; preserve body/postpublication error type so session latches reconciliation. Add causal real-writer postpublication regression and keep known prewrite CAS refusal non-uncertain.

Independently five existing uncertain autosave/file-save, stale offer and relative-base tests PASS, seven deselected. Explicit choice rereads exact file and DB observation; completed-command identity/revision/CAS and relative-base fail-closed behavior otherwise sound in bounded scope. No GUI baseline or remote action. Inherited ProjectStore ownership weaknesses remain documented/open, not remedied by this new layer.

## Corrected core + real shell integration — scoped CLEAR

Verified correction hashes: projects.py ff3ebe64eb0fe3743012606761d3b1b7aee488245c7db54903a41d2ef7c5f5e9; test_autosave.py f33579e1d9f688f55596298e65b4d838306455a33185c8505e5737d6b4d42a50; shell.py 16a0bcca8fc2476f4280e694eb082d2f589e969bc1620980bb90bb65087219f5; test_project_recovery_ui.py 80ce6b7961ac33bf6fad4e471ea3770b9d9dc64376e12cefde49b814d0d754ee; contract c9f69953d2b36d7685d614d6aca76e7fceb52722806e2a7aef6be6135ac6d2d1. autosave.py unchanged from initial pin.

Shared lock now translates only native acquisition failure; exceptions from writer yield retain uncertain-write classification. Independently ran both real post-publication permission/blocking failures plus actual UI cancel-choice, recovery-save-with-backup and unknown-save-disable cases: 5 PASS, 14 deselected, process exit0. Original failing causal case is now blocked from replay.

Shell offers explicit file/recovery/cancel (default/escape cancel), swaps current model/session only after successful choice, performs actual reviewed save and disables repeated writes on uncertain outcome. No renderer/edit gesture/timer behavior invented. No additional scoped blocker identified.

Remaining gates: full editor command/undo integration, original-base persistence/relink, responsive large-project I/O, cache rules, inherited ProjectStore ownership hardening and native Windows/abnormal-close end-to-end evidence. Local source CLEAR does not close whole P03-07 or authorize remote publication/CI.
