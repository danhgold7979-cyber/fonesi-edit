# P03-06 admission review — HOLD pending one portability fix

2026-11-01. Local uncommitted admission delta reviewed; no aggregate rerun or remote action.

Observed SHA256 at review:
- jobs/admission.py d34ae7af131acea9d79238a827d777bc824aff1be5b0ba30585657954864edbc
- jobs/publication.py a219d26d2da97d246ee5b91a1324f9deab18b7b1c25263900d464e062f66f471
- test_publication_admission.py 7a6fb1b35497940538d4e0091012c707ce47f6dda3f269580ed8106c82b86508

## Blocker: cross-API timestamp equality reintroduced
NamespaceAdmission.__init__ compares full descriptor fstat signature to named stat signature; guard then compares both to that single baseline. Existing probe.fingerprint already explicitly avoids this because Windows named and descriptor timestamps can differ in precision. A stable valid source/font can therefore fail admission before any operation.

Independent causal reproduction: unchanged regular source, same identity/size, descriptor timestamp observation shifted by one nanosecond via proxy while named stat remains unchanged. Constructor rejects with PublicationUnknown('Source changed during admission'). No source bytes modified, no external tools or full tests run.

Fix: capture independent named and opened signatures. Check physical identity across APIs and named stability across opening; thereafter compare each API only to its own baseline, retaining permanent revocation and genuine size/time/identity mutation detection. Add stable precision mismatch plus actual mutation causal regression. No need repeat unchanged 48-test baseline.

No additional blocker found in bounded delta. Original source/font read-only descriptors, immutable absolute path requirement, configured cache/output overlap refusal, final collision checks, source guard after I/O/immediately before native link, and bounded manifest/cache/artifact scan exclusions fit the stated scope. These are live namespace observations, not content-hash validation, arbitrary omitted-cache detection, restart authority or cleanup implementation. Cleanup to be reviewed separately.
