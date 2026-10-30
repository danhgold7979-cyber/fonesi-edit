# Rebuild P09-02/03 — bounded deterministic matrix planning

Pure independent logic, no filesystem/media render yet. Inputs: ordered unique scene IDs, unique allowed angle IDs per scene, explicit history with matching scene order, N, windowW, minimum differing scenesK, Kscope previous/window, seed and candidate budget. Unique combinations mandatory. W prohibits reusing an angle at its scene in any of W previous rows; K checks previous row or each row in W as selected. History includes prior rows and never silently crosses scene-order scope.

Lazy mixed-radix product, seed-driven coprime stride permutation; never allocate whole product. Small lookahead chooses least-used angle sum, heuristic balance only. Work/cancel bound; incomplete search is NOT proof of unsatisfiability. Preserve requested constraints, no hidden relaxation. Return rows+COMPLETE/SEARCH_LIMIT/CANCELED and examined count; actual render/reservation/history commit remain separate gates.

Tests exhaustive small product, huge logical space with tiny budget, deterministic seed/config/history, W/K invariants, invalid/scope-mismatched history, uniqueness, cancellation. No UI claims or full P09 acceptance.

Default wall-clock search budget2s, configured1ms–60s, checked before candidate/pool validations; individual bounded validation may slightly exceed deadline. Outcome depends on time budget and machine performance; same seed/config produces same prefix only when examined-candidate budget rather than wall timeout controls stop. No exact cross-machine count guarantee under wall deadline.
