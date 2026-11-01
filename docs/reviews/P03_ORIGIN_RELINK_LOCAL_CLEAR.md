# Local original-base persistence and same-content relink review

Verdict: CLEAR for this bounded dependency slice.

Verified SHA256:
- projects.py 97384acfb1fdf3c1dec4cd31de11de45cad51bf8d4103e2a2b70ce62298dccf5
- autosave.py 25f901265f2eb49976f956317b63fcfb5fec5fdf7d942a03973f65ac114fc4fd
- relink.py b66ef0fcbc4c63b8e7f262bc91a953c6cc11e9bcd3bc4464bb9b7f4a13ed8d9e
- test_autosave.py e3e676c432160f358a97ae1af2d35d06aec0bc19ffde3a0c46abf3bbee4de9eb
- test_project_origin_relink.py 34c96b777627f6780c90a10bc216a96f24f6bbd1d01ad3a889081be9dd837ecc
- PROJECT_RECOVERY.md 76a2a822e12618d7c4a3a3936ab28c468951bbbf835f2396d16f81b5dd2d508b

Independently five focused owned-v1 migration/rollback, moved-project original-base recovery and same-content asset/font relink cases PASS; six deselected. No baseline aggregate/native tests repeated.

Migration requires verified ownership and exact predecessor schema, retains consistent validated backup, rechecks predecessor under transaction, and preserves existing receipt lineage. Legacy rows retain NULL origin rather than guessed paths. Original base is committed with the project snapshot under the same CAS. Recovery maps relative execution references to the recorded base; unknown legacy base fails closed. Different known base triggers choice even for identical JSON. No automatic rollback/replay on uncertain COMMIT is added.

Relink validates selected asset/font identity, regular candidate, exact content SHA against both model hashes, cancellation and typed next revision. Original project/source bytes remain untouched until explicit completed-command commit. It is an observation, not enduring file authority; actual execution must revalidate. No renderer/output equivalence is inferred beyond identical content and unchanged render-content projection.

No new scoped blocker identified. Backup restoration, relink picker/background responsiveness, actual Windows/abnormal-close target evidence and full phase criteria remain open. No remote publication or CI action.

Pre-delivery hold: author identified schema path_ref does not enforce native relative syntax. A project-base path beginning with an absolute root can cause Path(origin)/ref to ignore origin. Final clearance is held pending rejection of absolute/Windows root-or-drive-qualified/NUL references before recovery mutation. Initial scoped findings above are provisional until that self-identified defect is closed.

## Final path-syntax correction — CLEAR

Verified autosave.py 2cd98fb1a667f1d86c994d71a7808de71e3c2d8b9891027005eb7540b66f921f; origin tests 0c61ff020e723b735289ad0fd3fcef5c4fc31d18a5aee949456b23a4cebf7513; contract ee09a11d207f1f0fb039965354dfaa412838c169b213b5b735104ed8877c20cc. Other initial hashes unchanged.

Native absolute paths, Windows drive/root-qualified paths and NUL are now refused before joining a project-relative reference to original base. Ordinary parent-relative references remain valid; no unrelated containment rule imposed. Independently five exact ambiguous-reference regressions PASS, eleven deselected. An initial mistyped -k selection ran no tests (exit5), then corrected exact selection above ran all five; no aggregate repeat. Pre-delivery hold resolved; final bounded-scope source verdict CLEAR with previously stated gates unchanged.
