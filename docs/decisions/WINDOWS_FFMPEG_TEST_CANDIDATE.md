# Windows FFmpeg test candidate — read-only evaluation

Downloaded and inspected read-only under explicit engineering scope; NOT executed,
installed or selected for product redistribution. Source publication is separate.
Goal: actual Windows
owned-fixture tests, no system/PATH/browser/security changes or user media.

## Provenance and meaningful adoption (2026-11-01)
[Official FFmpeg downloads](https://www.ffmpeg.org/download.html) links BtbN Windows
builds. [Build repository](https://github.com/BtbN/FFmpeg-Builds) API: maintained,
not archived, pushed2026-11-01;11915stars/1562forks are supplementary only. Five
current releases had17127asset downloads/8358win64; October31release1783win64,
its8.1LGPL-shared asset220. Counts are download events, not unique users/quality
reviews. Official referral, actual downloads and inspectable daily successful-build
automation support bounded evaluation, not security certification. Raw API snapshot:
local runtime/ffmpeg-candidate-api.json (no signed/private URLs).

Candidate, NOT mutable latest:
- Tag `autobuild-2026-10-31-12-59`, asset695397553.
- `ffmpeg-n8.1.3-27-g8dca1586f4-win64-lgpl-shared-8.1.zip`,80356594bytes.
- SHA256 `5cef7bc48e513f3cee7c881e8b2999d835541edb1846c3e89443a67f8f8556ab` from release API.
- [Dated archive](https://github.com/BtbN/FFmpeg-Builds/releases/download/autobuild-2026-10-31-12-59/ffmpeg-n8.1.3-27-g8dca1586f4-win64-lgpl-shared-8.1.zip).
[Upstream README](https://github.com/BtbN/FFmpeg-Builds/blob/master/README.md) says
month-end builds retained2years, other daily builds14days. Missing/hash-mismatched
pin must fail; never substitute latest or another provider.

## License/security/fit limits
Build scripts' MIT repository license is NOT binary/dependency licensing. Upstream
LGPL variant excludes GPL-only x264/x265; shared package needs bundled libraries.
Exact archive inspection below establishes the included LGPLv3 notice, not complete
transitive licensing or H264/H265 production capability.
[FFmpeg security](https://www.ffmpeg.org/security.html) lists versioned fixes; release
page lists8.1.3. Direct security-page fetch timed out; primary-page search evidence
was available, so no claim of a complete/current candidate vulnerability audit.
[Build security page](https://github.com/BtbN/FFmpeg-Builds/security) reports no policy/
published advisories, which does NOT mean vulnerability-free. A Linux shared-library
RPATH issue is not proof about this Windows package; loading needs target testing.

## Remaining gates, before execution/adoption
Inspect exact archive/notices/build provenance; verify ZIP hash/size; bounded safe
extraction into NEW owned CI directory, rejecting traversal/reparse/ADS/overwrites.
No global install/PATH changes. Record executable/DLL hashes and version/build flags.
Use only synthetic owned fixtures, no provider/account/network-media operations.
Actual Windows pair/known-stream/VFR/cancellation checks must pass with this pin;
never replace a failure with stand-in evidence. No binary product artifacts. Final
installation/update/version lease/redistribution remains P03-08/P12 work.

### Pinned recipe inspection (read-only)
The dated release tag resolves to build-recipe commit
`5031c6f1082414e53688d39e521849905071070d` (GitHub ref API). Its
[LGPL defaults](https://github.com/BtbN/FFmpeg-Builds/blob/5031c6f1082414e53688d39e521849905071070d/variants/defaults-lgpl.sh)
select version3 and COPYING.LGPLv3; shared variant enables shared/disables static.
The [Windows packaging recipe](https://github.com/BtbN/FFmpeg-Builds/blob/5031c6f1082414e53688d39e521849905071070d/variants/windows-install-shared.sh)
places executables/DLLs together under bin, with docs/includes/import libraries.
[Build recipe](https://github.com/BtbN/FFmpeg-Builds/blob/5031c6f1082414e53688d39e521849905071070d/build.sh)
copies selected license into archive LICENSE.txt. Thus LGPLv3 is the recipe's
expected FFmpeg notice; archive notice now matches. Transitive notices remain incomplete.
The pinned recipe also uses origin-relative Linux shared RPATH, so do not present
that older Linux issue as an established current candidate defect. Recipe inspection
is not binary reproducibility, signature verification or complete dependency audit.

## Exact archive inspection (2026-11-01, no execution)
The HTTPS download matches the release API size and SHA256 above. All 237 ZIP
entries were streamed/CRC checked and hashed (199,702,858 uncompressed bytes).
Inspection rejected traversal/absolute/ADS/backslash/NUL/case-collision/encrypted/
symlink entries, with 10,000-entry, 256MiB/member and 1GiB total limits. Only three
EXEs, seven DLLs and LICENSE.txt were extracted into a fresh private directory,
files mode0600. Existing system objdump read PE headers; no downloaded code ran.

Included LICENSE.txt: 7651 bytes, SHA256 `da7eabb7bafdf7d3ae5e9f223aa5bdc1eece45ac569dc21b3b037520b4464768`.
It is GNU LGPL version3 text. No separate dependency-license/notice bundle or GPL
license copy was found by archive filename inventory; this is a redistribution
review gap, not a legal conclusion. Build-script MIT does not cover these binaries.

FFmpeg/ffprobe are x86-64 PE files with DYNAMIC_BASE/NX_COMPAT flags and empty
certificate-table directories: no embedded Authenticode signature observed.
HTTPS/API hashes establish matching downloaded bytes, not independent publisher
signature or reproducible-build proof. Seven FFmpeg DLLs are bundled alongside
the EXEs; remaining static imports are Windows API/UCRT libraries. Dynamic/delayed
loads, runtime DLL resolution and target compatibility remain untested.

- `ffmpeg.exe`: 552960 bytes, SHA256 `9f3683fc0480bd4b54d42ae44702f6ac6320b3d4a12a36f3a70bfe37d02fd861`.
- `ffprobe.exe`: 265216 bytes, SHA256 `d93588787cb39d4ea2e74cf9b88998a95d2706add6c1de94a3b021e588cd6bea`.

Read-only embedded configuration strings in avutil/avcodec/avformat agree on
version3/shared, disabled x264/x265 and numerous embedded libraries (including
libass/fontconfig/freetype, OpenH264, AV1/Vulkan/OpenCL/network-related options).
This is not a complete versioned dependency SBOM or CVE audit. Product use must
not imply these optional GPU/network paths were tested or authorized.

Local raw inspection receipts: runtime/ffmpeg-candidate/archive-inventory.json,
pe-inventory.json, embedded-build-config.json. No binaries enter Git/product.

### Proposed next gate — not yet execution authorization
A separately authorized, reviewed test-only Windows job could download this exact
pin, verify archive/member hashes, extract only required EXEs/DLLs/license to a
new owned runner directory and use absolute paths (no PATH/install changes).
Run version/build reporting and synthetic owned local fixture probe/decode/frame/
cancellation tests with bounded owned processes and file/pipe restrictions.
Do not upload binaries, fetch media/providers, or infer product redistribution.
Fail on unavailable/hash-mismatched pin or missing DLL; never substitute another
build. Actual target evidence must precede any Windows codec/readiness claim.

Durable read-only inspection metadata is copied without binaries into
`docs/evidence/p03/windows-ffmpeg-candidate/` (archive inventory, static PE imports,
embedded configuration strings). These reports do not prove successful loading or
complete third-party attribution. Proposed harness `scripts/check_windows_ffmpeg.py`
requires explicit Windows execution flag, exclusive report/work paths, exact archive
and ten member pins; it excludes ffplay. Fresh owned bin/CWD and ephemeral trusted
runner are prerequisites, not an OS sandbox. No candidate was executed during the
sentinel ZIP/control unit tests. The dedicated marker workflow is prepared only;
execution authorization and independent source review remain separate gates.
The corrupt fixture gate establishes that probing completes but validation refuses;
it does not attribute every possible refusal specifically to the decoder stage.
Rotation checks establish a raw matrix and 90-degree summary magnitude, not sign/
matrix-interpretation or preview/export parity. Any stronger claim needs its own
causal assertions. Sentinel tests and static review are not Windows tool evidence.
