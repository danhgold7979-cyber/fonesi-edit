# Uncommitted live publication/finish review

Base HEAD 3f82d54b2f31252fde370adc7acad320c86f1149. This review is NOT a new commit or hosted run.

Verified initial hashes:
- publication.py: 061c74475d60d25502f028834564777587a81a2ba478739f3a918b8d62ac7fe2
- test_publication_session.py: 020e8ef92664637784e22591f6d3e5a6d377eab954b7dc41ff8cf9fe82339894
- test_coordinator_ownership.py: 7b15b2820f7d923d3d5a68a269461ec9e22eb14e0f633facfaa4e92e129bc975
- clean-foundation.yml: b4dbd2654d839d5ef4adea37615f9ff434da994a8473439b755ed5a25ae0d60b
- PUBLICATION_IMPLEMENTATION.md: edaa17e435a439a0bec9a0dbbaaec4d927436dfefb4a9100bab7a91705894ffd

## Findings requiring correction
1. HIGH: publish_member checks coordinator before Destination.publish, but the latter performs slow hash verification before native link without a fresh authority guard. Independently injected epoch change immediately after successful _verify: publish_member raises CoordinatorLost later, but final file already exists and artifact rows remain zero. Add live owner/job/exact journal check after verification immediately before native no-replace link; test loss during hash creates no final.
2. Target portability: new final/stage mutation tests perform rename/unlink while original FD retained. Windows can legitimately reject deletion. Recognize this only as prevented mutation with unchanged owned object/no premature history, not proof that injected corruption was detected. Existing filesystem tests already model this distinction.

## Checked nonblocking boundaries
Independently 5 tests for before/after member/final COMMIT failures and filesystem-postlink uncertainty PASS, 27 deselected. Exact-set/history transaction and live-only reconciliation have no additional identified defect in this slice. Restart UNKNOWN, failed postlink readback conflict and no cleanup remain explicit limitations.

Read Microsoft LockFileEx official remarks https://learn.microsoft.com/en-us/windows/win32/api/fileapi/nf-fileapi-lockfileex : OS release after process termination may be delayed. Test-only bounded observation still requires actual successful acquisition and retries only CoordinatorBusy after confirmed child exit; SQLite/identity/epoch failures remain failures. No native Windows outcome claimed from Linux tests.

All review commands local/read-only except this external report. No commits, push, CI launch, new criterion closure or phase acceptance.

## Corrected local batch — scoped CLEAR

Verified corrected SHA256 values (still UNCOMMITTED, same base HEAD):
- artifacts/filesystem.py: 9b1ca767653c5ae8b2740991fd8f83e801b32449d93064fbd79bc765bd7d6e77
- jobs/publication.py: 88fc6d3cdfbb512ed20ef372b95b64a5b7a929d5fab6575522361e46277713ed
- tests/test_publication_session.py: f9b5bd00504511cb3435679ce728fc4824fef283feb17ba9a5737fb10c0bf7f9
- contract: 7935186bbbfae2199ba618a30ce8905984e10cd365d79c7042e3ac42a467b1d0
Other two workflow/coordinator-test hashes unchanged from above.

Destination.publish now rechecks destination and invokes live coordinator/job/exact-journal guard after slow stage readback immediately before native link. Independently ran new epoch-loss/no-final regression, normal exact-set completion and five mutated-evidence cases: 7 PASS, 26 deselected. Prior five COMMIT uncertainty checks remain unchanged evidence. Windows pin-denial branches explicitly verify retained bytes/no history and do not claim mutation injection.

No remaining identified blocker for this bounded live-session completion source. CLEAR is local source review only: retain user hold on new commits/push/CI until phase readiness or an agreed exception. Actual Windows/native evidence for this batch, restart recovery/cleanup and full phase criteria remain open. No new assertion closure.
