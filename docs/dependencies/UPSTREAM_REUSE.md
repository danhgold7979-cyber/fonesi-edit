# Reuse-first dependency decisions — 2026-11-01

User priority: reuse established, effective upstream code instead of rebuilding it;
require meaningful adoption and positive quality signals, not stars alone. GitHub
availability is neither a license nor execution permission. No archived Fonesi code
is imported. Existing reviewed Qt/SQLite/FFmpeg/JSON-Schema/stdlib machinery stays;
do not churn correct tested adapters merely to claim a new dependency.

## 1. pysubs2 1.9.1 — preferred bounded subtitle parser candidate

**State: PROVISIONAL SOURCE ADOPTION after the user/root quality gate; Windows and
release acceptance remain OPEN.** Highest-value
next reuse: P03 sidecar validation / P04 SRT, VTT and ASS parsing rather than another
custom parser. It does not replace rational timeline evaluation, cue identity,
word-timing reliability, editor rendering or preview/export parity.

- Official [repository/tag](https://github.com/tkarabela/pysubs2/tree/6371ae8bc2f9fed19aeb51a8e09d920e8bb86ce5),
  source commit `6371ae8bc2f9fed19aeb51a8e09d920e8bb86ce5`.
- [PyPI1.9.1](https://pypi.org/project/pysubs2/1.9.1/) released2026-10-30;
  pure Python, no additional dependencies, Python>=3.12. MIT notice copied unchanged
  from inspected wheel into `pysubs2-LICENSE.txt`; retain it in any distributed package.
- Wheel `pysubs2-1.9.1-py3-none-any.whl`,48092bytes;
  SHA256 `4210ebedc54e8272e741fc5888a1721f74056bbd91b7aac7cc90b6559cd055b4`.
  PyPI Trusted Publishing provenance names the same source commit. Downloaded only
  for read-only ZIP/source/metadata inspection; computed byte hash matches. No import,
  installation, repository-code execution or build hook was run during the initial
  survey. Subsequent authorized integration installs only this verified official
  wheel into the local virtualenv, with exact dependency/hash lock and MIT notice.
- Meaningful use: [PSF-hosted PyPI Stats API](https://pypistats.org/api/packages/pysubs2/recent)
  observed193478downloads/month,94564/week,12003/day at this check; raw response retained
  in evidence. These are download events, not unique users or satisfaction ratings.
  [Bazarr's current vendored module](https://github.com/morpheus65535/bazarr/blob/master/libs/pysubs2/__init__.py)
  demonstrates actual downstream use; [its format-tools issue](https://github.com/morpheus65535/bazarr/issues/3285)
  documents operational SRT/ASS/VTT integration. No Bazarr GPL code is copied.
- Positive quality signal: exact-source [upstream CI40979280401](https://github.com/tkarabela/pysubs2/actions/runs/40979280401)
  has successful Python3.12/3.13/3.14/3.15 jobs with type checks, lint, tests and tests
  of built wheel/sdist. [Release run40979370783](https://github.com/tkarabela/pysubs2/actions/runs/40979370783)
  also succeeded. This is upstream evidence, not Fonesi Windows integration proof.
- Security check: OSV query PyPI/pysubs2/1.9.1 returned no known advisory records at
  2026-11-01T06:19:23Z; raw query/response retained. This is not a security guarantee.
  Direct GitHub advisories endpoint was unavailable through the connector; do not
  describe that unavailable check as a clean scan.
- Known limitations must be tested, not hidden: [open#120](https://github.com/tkarabela/pysubs2/issues/120)
  reports malformed ASS timestamps raising bare ValueError outside the library's own
  exception hierarchy; catch and reject safely, never invent zero timings.
  [open#100](https://github.com/tkarabela/pysubs2/issues/100) concerns ASS header fidelity;
  [open#101](https://github.com/tkarabela/pysubs2/issues/101) concerns overlapping
  ASS→SRT conversion. A historical1.7.0 package was yanked for a missing subpackage;
  pin/hash and wheel import/format tests are mandatory, not optional.

Integration gate: bounded adapter admits only explicit SRT/VTT/ASS/SSA, enforces input/
line/cue limits before parsing, catches malformed-format errors, preserves original
bytes/provenance and cue IDs, represents milliseconds as exact rationals, refuses
unsupported fidelity instead of silently dropping it, and never fabricates word
alignment. Run Unicode/overlap/empty/corrupt/long-file/adversarial cases and actual
Windows3.12/3.13 wheel/frozen-package tests. The exact version/artifact hashes are now locked for provisional source integration;
release/Windows acceptance requires those target tests. No blanket mature-library or
format PASS claim.20 focused Linux adapter tests pass; independent review pending.

## 2. yt-dlp 2026.10.26 — download connector candidate

Official [release](https://github.com/yt-dlp/yt-dlp/releases/tag/2026.10.26), commit
`f264a6cbd1f630894da0f368df00f8aae50140e0`; project source Unlicense. The
[official README](https://github.com/yt-dlp/yt-dlp/blob/2026.10.26/README.md) warns that
bundled release artifacts contain dependencies with other licenses. Audit the exact
chosen Windows artifact, checksums/signature and dependency notices before installation.
Use as pinned subprocess through owned process/tool-registry adapters, not copy
extractors or execute arbitrary plugins/config from an uncontrolled environment.

[Pinned supported-sites list](https://github.com/yt-dlp/yt-dlp/blob/2026.10.26/supportedsites.md)
contains YouTube, Bilibili, TikTok, Facebook, Instagram, Twitter/X, Douyin and XiaoHongShu
families. Threads and Kuaishou were not listed in that snapshot; do not claim all ten
platforms work. Some listed variants are explicitly broken. Each URL/media/account/
pagination/subtitle/sync cell still needs permitted live tests. Adoption/community/
security evidence for the exact artifact and tool dependency choices remains pending;
no live download, cookie read, Chrome/profile operation or install occurred in this survey.

## 3. PyAV 19.0.2 — defer until decoder experiment requires it

Official [release](https://github.com/PyAV-Org/PyAV/releases/tag/v19.0.2) dated2026-10-21;
wrapper [license metadata](https://github.com/PyAV-Org/PyAV/blob/v19.0.2/pyproject.toml)
is BSD-3-Clause. Native FFmpeg libraries in chosen wheels have their own build/license
obligations; the wrapper label is not a complete binary redistribution assessment.
Could supply decoded frames/timebases, but introduces in-process native lifecycle/
crash and packaging boundaries. Current Qt canonical raster plus owned FFmpeg process
architecture already exists; do not add/churn without a measured requirement gap.
Exact wheel hash/provenance, broad adoption/quality/security and Windows tests remain
required. No PyAV wheel was downloaded or executed.

## 4. Portalocker 4.4.2 — evaluated, no replacement now

Official [tag](https://github.com/wolph/portalocker/tree/2fb4ce92a16718039472879f6b43612806281650),
commit `2fb4ce92a16718039472879f6b43612806281650`, released2026-10-28; upstream
[BSD-3-Clause license](https://github.com/wolph/portalocker/blob/v4.4.2/LICENSE).
It can supply cross-platform OS-lock machinery, but not our original-DB incarnation,
marked-file non-overwrite rules, permanent revocation, monotonic coordinator epoch,
owned process quiescence or multi-artifact transaction. Existing small adapters already
reuse stdlib/native locking. Replacing those now would add dependency/churn without
closing the requirement gap. No installation, execution or broad quality approval.

## Decision boundary

The exact application ownership/state/snapshot/publication rules still require small
reviewed integration code; no evaluated library proves them automatically. Reuse
standard libraries and established engines underneath rather than copying an unrelated
app's complete codebase. Keep target evidence and license obligations per actual
artifact. New source publication remains separately gated by repository authorization;
this survey does not resolve the held6729ef7 public-tree action.
