# Local root-folder relink / GUI lifecycle review

Verdict: CLEAR for bounded verified root remap and actual UI integration.

Verified SHA256:
- storage/relink.py ea2227df1f32c26d2aa23dc738cd55bdb6dac50fa8f5ae8e609331d1dc5814c3
- autosave.py 3609b8914a4dabf2a9b6a97910e49bf36af984de0bce016748d8b135b7f7e50c
- ui/project_relink.py c9eb028428ac118e67c00ee87e22fbd39293ba92b0ebdf4259ba60cd133bd22b
- shell.py fc2189404db1959e416e512ebbe979ab55178aab66c155645fdce3fff6a64ea7
- __main__.py 34ee174c8a42733ed2a0c1127a9e34669b19633a6b93ec92f7decb363764814a
- test_root_relink.py dfcdf69076ae35d9398cd49dcc27a74a887a2936e4d4f8c519c6fa9601d8bbf7
- test_project_recovery_ui.py 9545887ece0e0790e90f097b74d0942eb24b57ed2394a9df956454f83d982d55
- contract b5271cb21f8ee624a0fd095c81e10c327c49082481c1616f886bca3b9004653c

Independently five targeted all-or-nothing mismatch, distinct project-base/media-subroot, cancel/close late-result and stale-session cases PASS, two deselected, clean process exit0. No aggregate or native target rerun.

Mapping normalizes source references against actual project base before selecting references under the explicit old root; outside references remain unchanged. Every mapped candidate must match both stored hashes before returning one completed revision. No source writes or partial model commit. Background work captures immutable project/base; GUI owner commits only the same session, with revision/CAS checks. Explicit GUI cancellation latch survives QThread interruption-flag reset; close waits for both worker families and successful wait(0) before destruction. Open/save are inhibited while verification runs, and uncertain commit disables retry through session state.

No identified blocker in this scope. Paths/fingerprints are observations, not enduring capabilities; media execution must revalidate. Native Windows, abnormal-shutdown/full editor integration and complete requirement acceptance remain open. No remote publication/CI action.

Final source-only hardening verified: shell.py SHA256 d042d751a3dfee4b18345e78717db95c770901c5d33b786c844c81965a0f3762. request_stop now latches close_requested and refreshes disabled project actions after stopping both worker families, including the actual entrypoint's event-processing retirement path. Consistent with existing closeEvent; scoped CLEAR retained. Other hashes/evidence unchanged; no additional test run or remote action.
