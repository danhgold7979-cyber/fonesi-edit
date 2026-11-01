# Required-set admission review — a045d0215ed75d0bde7cb66141fb7d4bb8fb13ec

Verdict: HOLD pending typed/readback policy-bound consistency fix.

## Concrete blocker
Typed RequiredOutput accepts ExpectedStream tolerance Fraction(1,2**129), marks publication_ready and serializes it; RequiredOutputs.from_dict rejects the same manifest because rational components exceed 128 bits. submit persists that intent without readback validation, leaving an accepted job permanently unpublishable. Reviewer reproduced constructor/to_dict/from_dict mismatch. Enforce identical bounds before durable submission and test rejection adds no job row.

Author additionally identified stage_subtitle hashing oversized input before parser MAX_BYTES rejection; batch early size/type rejection before SHA with constructor-trap regression.

## Independently checked
Nine selected rollback, cancel/expiry/corruption, member-row mutation and legacy/intent-only policy cases PASS; nine deselected. No actual FFmpeg/frozen/aggregate rerun. Code review confirms exact required-role membership, live-owned staging, current owner/worker validation before DB transactions, atomic set/member prepare and job/set/member claim with rollback. No member publication, final success, completion history or restart adoption API exists.

Nonblocking clarity: assign self.job after successful COMMIT rather than before, so failed claim does not leave a rolled-back publishing record in memory. Current guard compares snapshot/attempt/token rather than that state, so no current authority escalation observed.

Remaining gates include actual newer Windows evidence, physical name-alias admission, tool registry, full publication/finish/recovery and criterion acceptance. No remote publication authorization is implied.

## Correction closure — b086ccccb94a6d2eff8bd09610c8cdc1273fb0de

Verdict: CLEAR for scoped required-set staging/prepare/claim checkpoint and newer-target testing.

Typed manifests and persisted readback now share MAX_RATIONAL_BITS=128, checking every Fraction field before any submission. Oversized subtitle bytes are rejected before hashing. claim changes in-memory self.job only after COMMIT. Independently ran exact four targeted regressions (oversized rational no-row + boundary roundtrip, prehash trap, transaction rollback memory/DB, normal all-role claim): 4 PASS, 16 deselected. No FFmpeg/baseline aggregate rerun.

No remaining identified source blocker within this bounded checkpoint. Hold new implementation expansion for actual newer-source hosted/Windows evidence as parent directed. Source CLEAR is not actual Windows PASS, full P03 acceptance, new criterion closure, final publication/restart implementation or authorization to bypass the specific remote-publication denial.
