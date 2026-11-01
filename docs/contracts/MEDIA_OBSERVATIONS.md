# Typed media observations — partial P03-03

`normalize_probe(ProbeResult)` preserves every container-global stream index in
source order, including data/attachment/unknown tracks and cover-art disposition.
It returns immutable bounded observations, NEVER a render-ready CompositionPlan.
Unknown geometry/SAR/layout/timing remains null with fixed diagnostic codes; no
stereo/square-pixel/zero-time/CFR assumptions, no track dropping. Exact integer
stream ticks times rational timebase take precedence over rounded decimal fields;
decimal disagreement beyond displayed rounding precision is reported, not silently
used. Signed starts are preserved. Container duration is separate from each stream.
Raw display-matrix fixed-point integers and rotation summaries/tags are separate
facts: no reflection/perspective/rotation coercion or double application. Frame PTS
are explicitly NOT_OBSERVED; average/r frame rate cannot create a VFR map. Frame
scanning, readiness conversion, actual editor import and unsupported-layout handling
remain follow-on scope rather than silently excluded product formats.

Inputs: max16MiB JSON,256streams,256side-data entries/stream, bounded numbers and
labels; stdlib frozen dataclasses/Fraction/JSON plus existing numeric parser reused.
No new parser dependency/upstream source copied. JSON output uses exact num/den
pairs and drops arbitrary tags, filenames, raw tool stderr and other private data.
This is observation, not media decode validity, trusted tool registry or executable
identity capability.

`--inspect-media ABSOLUTE_MEDIA --ffprobe ABSOLUTE_TRUSTED_EXECUTABLE` explicitly
executes the caller-selected ffprobe through existing owned process/fingerprint
logic. No fallback/discovery/download, GUI/data-store initialization, source writes
or job success. Exit0 means observation returned, not readiness. Failures print a
fixed message. The caller must authorize/trust the executable; project metadata
cannot supply this grant. Existing process timeout/output bounds apply, not a hard
OS-I/O deadline for hashing/stat calls.

Primary protocol reference (read-only; ffmpeg.org docs fetch timed out):
- https://raw.githubusercontent.com/FFmpeg/FFmpeg/n7.1/fftools/ffprobe.c — stream tick/timebase fields, display side data and frame timestamp distinctions.
- https://raw.githubusercontent.com/FFmpeg/FFmpeg/n7.1/libavutil/display.h — raw matrix layout/fixed-point conventions and rotation direction.
Current local executable version/hash and source-file hashes are in the scoped
Linux receipt, not inferred from the n7.1 documentation reference. No Windows
FFmpeg or all-version protocol compatibility is claimed.
