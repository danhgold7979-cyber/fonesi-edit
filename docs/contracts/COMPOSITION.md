# CompositionPlan v1 — normative domain contract (proposal for P02 validation)

No legacy implementation imported. Version is `schema_version:1`, evaluator revision `eval-1`; unsupported versions are rejected without rewriting original. UTF-8 JSON forbids NaN/Infinity, duplicate keys, unknown fields and secrets. Canonical encoding sorts keys, uses compact separators and UTF-8; SHA-256 includes schema/evaluator revision and asset/font hashes, not local path spelling. Numeric values below use rationals `[integer numerator, positive integer denominator]` reduced to canonical form; bool is not an integer. UUID strings identify objects. Draft may contain missing refs but cannot compile/enqueue until resolved.

## Required root shape

| Field | Type / invariant |
|---|---|
| schema_version / evaluator_version | exact integer 1 / string eval-1 |
| id / revision | UUID / nonnegative integer; editing creates new revision |
| output | width,height positive even integer for default yuv420p; fps positive rational; duration positive rational seconds; sample_rate integer; channel_layout enum mono/stereo; color_space bt709 default; pixel_format yuv420p default; container mp4, video_codec h264, audio_codec aac default; unsupported alternatives need capability check |
| assets | ordered list of Asset with unique id; no external URI auto-fetch |
| clips | ordered list of Clip; explicit gaps and overlap transitions |
| layers | ordered list of Layer; order explicit, no dict iteration dependence |
| audio | ordered list of AudioClip and master processing |
| transitions | explicit video/audio overlap records with left/right clip IDs and duration |
| fonts | FontAsset list with hash, face index, family/style, fallback refs, license/provenance refs |
| seed / algorithm_revision | unsigned 64-bit integer / exact generator revision |
| provenance | project UUID/revision, preset ID/version/hash, source/account references only |

Asset: `{id,kind:video|image|audio,path_ref,sha256,probe}`. Probe: duration/time_base rational, streams (type/index/codec), displayed dimensions, SAR rational, rotation in quarter-turns or validated matrix, video frame timestamp index for VFR, audio sample rate/layout/start_time. Fast stat fingerprint is invalidation hint, not identity proof. Missing/changed hash requires relink/preflight, never silently substitutes content.

Clip: `{id,asset_id,source_in,source_out,output_start,speed,fit,crop,transform,color}`. Source range `[in,out)` within probed interval; speed>0. Output end is `output_start+(out-in)/speed`. Crop normalized left/top/width/height with positive dimensions, bounds within displayed source; fit contain/cover/stretch with explicit background color/blur. Transform includes flip_x/y, rotation, position and scale. Clip speed affects its linked audio/cues via the same map. Repeating a clip creates explicit segments with unique IDs; freeze is explicit last-source-frame segment, not speed zero. Ordered clips may overlap only through valid transitions; gap default black/silence.

Layer: `{id,type:mask|logo|text|subtitle,z,intervals,transform,style,content,keyframes,visible,locked_fields}`. Z total order uses `(z,id)`; default video→mask→logo/text/subtitle only establishes initial z, not an immutable restriction. Intervals are nonempty, sorted, disjoint half-open output seconds; no implicit forever past output duration. Transform stores normalized position x/y, positive width/height or scale, anchor enum nine points, clockwise degrees, opacity [0,1]. Negative positions allowed only with explicit out-of-frame warning; renderer does not silently clamp. Masks: rectangular rounded shape; mode blur/mosaic/color; amount, feather, radius, RGBA validated by engine capabilities. Logos reference image ID and optional source crop. Text references FontAsset, content, font size in output pixels, spacing/line spacing, wrap width, alignment, max lines, overflow policy (wrap/shrink bounded/warn), fill/outline/shadow/background/padding/radius. Subtitle content references cue IDs/language track and original/translated bilingual linked blocks with independent style/visibility. Missing glyph/font blocks parity certification; explicit user fallback persists its resolved hash.

Keyframe: `{property,time,value,easing}`. Property path from supported animatable registry (x/y/width/height/scale/rotation/opacity); time absolute rational seconds or normalized rational [0,1] with explicit mode. Duplicate time per property invalid. Before first/after last hold nearest keyframe. Between frames evaluate linear, ease-in u², ease-out 1−(1−u)², ease-in-out 3u²−2u³; rotation interpolates numeric degrees (no hidden shortest-path). Lock prevents editing/auto, not evaluation. Motion presets compile into immutable keyframes/analytic segments tagged with evaluator revision and seed, never independently randomized in preview/export. Unsupported path/easing is typed error, not ignored.

AudioClip: `{id,asset_id,source_in,source_out,output_start,speed,preserve_pitch,gain_db,pan,mute,solo,fade_in,fade_out,role}`. Role original/main/music/sfx; ranges and mapping same Clip; gain finite dB; pan [-1,1]. Solo audible set is nonmuted solo clips if any, otherwise all nonmuted clips. Loop/crossfade/SFX triggers compile to explicit repeated instances and exact offsets before snapshot. Ducking policy contains marked intervals or measured envelope hash, threshold/attack/release; no fabricated speech detection. Master: sample rate/layout, explicit normalization target (LUFS/peak), optional limiter and measured report. Silence generated only where intentional and reported when required audio is missing.

## Authoritative evaluation and order

`validate(plan, asset_catalog, capabilities) -> diagnostics[]`; error blocks compile, warning requires displayed acknowledgment policy. `evaluate(plan,t) -> EvaluatedFrame(layers,source_requests,audio_spans,diagnostics)` is pure and shared by preview/compile; arbitrary Qt painter transforms cannot redefine export geometry. `compile(plan, capabilities) -> ExecutionPlan(steps,expected_artifacts,tool_leases)` either supports every enabled property or errors by property path. No successful partial render.

1. Resolve asset orientation/SAR into displayed source coordinates; decode source frame by presentation timestamp (latest PTS ≤ requested source time).
2. Intersect source range, map output time `s=in+(t-output_start)*speed`; clips/cues use same segmented map. Trim precedes speed. For subtitles, intersect each source cue with each segment, map both endpoints and preserve provenance.
3. Crop displayed source; apply flip/rotation; fit canvas and explicit background; color transforms in declared order brightness→contrast→saturation→gamma→temperature.
4. Composite clips/transitions; evaluate layers at t; resolve font layout using same raster/layout provider for preview and export; apply local size/crop, anchor-relative scale/rotation, translation, opacity then z-order compositing. Mask samples already composited underlying pixels at its z.
5. Evaluate/mix audio resampling/time map→pitch policy→gain/pan→fades/ducking→sum→normalization/limiter. Audio crossfade overlap participates in duration equation.
6. Convert final pixel/color/output codec. Proxy changes decoded resolution, never logical coordinates, timing or font metrics.

Time remains rational until raster/sample boundary. Output frame n samples t=n/fps, n in `[0,ceil(duration*fps))`; final duration policy rounds to complete output frames and reports exact rational duration. Sample index is floor(t*sample_rate); negative input clipped before indexing. UI time display is rounded only for display. Pixel positions use half-up rounding (`floor(x+1/2)`) at raster boundary; no repeated integer rounding through transforms. Out of range evaluate returns typed range error; half-open end is not active.

High-quality preview uses the canonical compositor path at the requested output frame; responsive draft preview is explicitly labeled until parity verified. P02 must prove shaping/filter engine choice before full P04/P07. Schema acceptance does not mean any engine implements all fields.

## Mandatory tests / pass definitions

Schema missing/unknown/invalid-ref/nonfinite/duplicate-ID/timepoint cases; rational NTSC and VFR boundary mapping; noncentral anchors/rotation/opacity/layer order; Vietnamese/Chinese glyph/fallback/wrapping; each easing boundary and seed determinism; crossfade duration/audio sample count; mute/solo; missing capability must fail. Same snapshot yields identical evaluated geometry on preview/export. Pixel/audio tolerances and sentinel failure probes in VERIFICATION.md. Every schema field must map to criterion, evaluator test and UI/editor use before P07 acceptance.
