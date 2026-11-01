# Windows FFmpeg candidate — bounded read-only review

2026-11-01 14:48 UTC. No binary executed, downloaded, installed or published by reviewer. No full archive rehash repeated.

## Verdict
Candidate dossier is appropriately qualified for root's separate decision about a reviewed, synthetic test-only Windows gate. This is NOT execution authorization, product adoption, redistribution approval, legal opinion or security certification. No factual blocker found in selected local crosschecks.

## Independently checked
- Retained release snapshot identifies dated tag/asset695397553, exact filename, size80356594 and SHA2565cef7bc48e513f3cee7c881e8b2999d835541edb1846c3e89443a67f8f8556ab, matching archive inspection receipt. Prior full archive hash/CRC pass remains author evidence, not repeated here.
- ZIP central inventory:237entries/199702858 uncompressed bytes; only LICENSE.txt filename among license/copying/notice matches. Filename search does not establish absence of every possible embedded legal notice.
- Independently hashed extracted ffmpeg.exe552960bytes and ffprobe.exe265216bytes: match documented9f3683fc… and d9358878… pins. Parsed PE headers directly: x86-64 machine0x8664, DLL characteristics0x160 (DYNAMIC_BASE/NX_COMPAT present), certificate-table directory zero. This is absence of embedded certificate evidence, not a malware/safety assessment.
- LICENSE.txt7651bytes hashda7eabb7… matches; contents identify GNU LGPLv3. Build-script MIT does not establish binary/dependency licensing. Incomplete dependency notices/SBOM and reproducibility remain stated gaps.
- Ten PE inventory records cover three EXEs/seven DLLs. Listed nonbundled static imports are Windows/API/UCRT names. Static import inventory cannot prove delayed/dynamic runtime resolution.
- Embedded configuration consistently identifies shared/version3 and disabled x264/x265, alongside optional network/GPU/other libraries. Neither codec availability nor correct DLL loading has been executed/proven.
- Fresh official FFmpeg download-page verification timed out; pinned GitHub recipe web fetch cache-missed. Thus official referral/recipe-reference claims were not independently refreshed in this pass; existing dossier attribution remains historical author evidence, not newly verified provenance.

## Required implementation gates before test execution
1. Separate root authorization and source-reviewed harness/workflow. Exact immutable asset/hash; missing/hash mismatch fails closed without alternate provider/latest fallback. Extract only ffmpeg/ffprobe plus required seven DLLs and notice into a new owned directory; ffplay not needed.
2. Bound archive bytes/entry counts/member and total extraction, reject Windows device names/trailing-dot-or-space aliases, case collisions, traversal/ADS/reparse and overwrite. Preserve selected member hashes. Current Linux inspection does not by itself prove a Windows extractor safe.
3. Absolute EXE paths do not bind transitive DLL resolution. Use owned controlled working/bin directory, no untrusted media directory as CWD and no global PATH/DLL/security changes; record loaded build/version facts and full bundle hashes. Fail missing dependency; do not silently copy host DLLs into candidate bundle. File/pipe protocols reduce media I/O surface, not an OS sandbox or proof of no arbitrary network capability.
4. Run only owned synthetic fixture generation/probe/full decode/frame observations and cancellation through existing bounded owned-process adapter. Confirm which codecs actually exist before choosing explicit fixture codec; no libx264 assumption for LGPL candidate and no substitution interpreted as equivalent H264 product support. Version/library consistency, known stream identity/timing/SAR and cancellation retirement must be measured separately.
5. Record exact OS/Python/tool/member hashes and source, positive and causal negative results. Real Windows FFmpeg tests must actually execute (not stand-in/skip), while UI/display-matrix/VFR completeness/production codec promises remain separately scoped. Upload only bounded logs/JSON/JUnit, not EXEs/DLLs or user media.

The proposed gate can establish narrowly measured target behavior; it cannot close installation/update leases, full dependency security/licensing, redistribution or all P03-08/P12 requirements.
