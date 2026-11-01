# Verification contract v1

Thresholds below are proposed developer correctness gates, not measured product promises. P02 records whether engines meet them; adjusting a tolerance requires explanation plus reviewed evidence, never changing it merely to make a failure pass. Target hardware and Windows version are unknown; do not invent user's PC. Record CPU model/core count, RAM, storage medium/free bytes, GPU/driver/VRAM, OS build, screen/DPI and exact tool/build hashes before timing acceptance.

## Corpus manifest

Every case has case_id, generator/version/arguments, seed, license/provenance, SHA-256, stream metadata, expected outputs and requirement children. Generated samples contain synthetic gradients/checkerboards/moving shapes, timing slates and known-frequency tones; labelled synthetic, never production downloads. Font samples use available licensed fonts and record exact file hashes; missing CJK font marks those tests NOT_RUN rather than replacing glyphs with boxes.

Minimum cases: landscape 1920×1080/30 and portrait1080×1920/30; square720; fractional30000/1001; VFR alternating frame durations; rotation90 metadata; SAR non-square; no audio; mono/stereo44.1/48k; audio delayed250ms; 1-frame and 10min clip; truncated file; corrupt packet; video/image/audio-only files; PNG alpha and opaque JPEG; Vietnamese/Chinese punctuation/combining characters; SRT/VTT/ASS overlap/long/empty/invalid cue; duplicate filenames across roots; Unicode paths; output nested in input; symlink/junction loop (platform-specific); 10,000 path inventory generated without bundled media; 12-scenes×20-angles lazy matrix; disk/quota/permission faults in isolated fixtures. Add mixed FPS/ratio/aspect batch and multi-folder manual audio playlist.

## Correctness measurements

- Geometry evaluator: rational values exact. Raster edge/anchor position within 1 output pixel on canonical full-resolution path; layer order exact; no missing glyph or clipped text accepted.
- Preview/export: decode same-frame canonical preview and exported video into RGB at declared color transform. Compare golden lossless compositor first (max channel error0); lossy H264 comparison uses mean absolute RGB error≤3/255 and 99th percentile≤15/255 outside one-pixel antialias boundaries; text/logo masks intersection-over-union≥0.99. Color/grain fixtures may require lossless intermediate comparison plus codec-specific documented tolerance, not blanket waiver. A deliberately shifted3px layer/missing text/wrong z must fail.
- Timing: each frame/time-map decision exact; encoded video duration within one output frame and audio duration within one codec frame (AAC1024samples) of expected; audio event alignment within max(1 output frame,20ms). Tones/impulses measured by sample energy cross-correlation, not just file duration; shifted100ms sentinel must fail. Subtitle appearance checked at start−1frame/start/end−1frame/end for every transformed segment.
- Output validation: ffprobe stream/codec/dimensions/duration + actual decode without errors; expected audio presence; sidecar parse with exact cue IDs/text/time policy; final SHA receipt. Existence-only checks forbidden.
- Matrix: exhaustive oracle for small feasible spaces; all scene/order/W/K/uniqueness constraints; seeded regeneration exact with full history snapshot; large case bounded memory, timeout not infeasible.
- Persistence: save→close→open canonical semantic equality; crash injection at journal boundaries; source hashes unchanged; foreign sentinel output intact; secret sentinels absent from exported project/preset/log/CSV.

## Performance protocol

Separate proposed budgets from observations. Initial developer UX target: input event handling p95≤50ms and no UI event-loop stall>250ms during background render; seek latency p95≤250ms with warm proxy on declared1080p corpus; startup cold/warm timings recorded, target gate chosen after P02 packaging measurement. Run 5 warmups +30 measured seeks and60s event-loop sampling, report p50/p95/max, failures and cold cache separately. Do not substitute average for worst stalls. RAM/VRAM/resource caps follow measured baseline and admission policy, not universal constants. Large batch planning should scale with selected inputs/requested outputs, not theoretical product; measure 10k paths and12×20 matrix with fixed search budget.

P02 chooses reference hardware from actual available measured environment. Linux development acceptance is separate from Windows10/11 (where compatible versions remain supported), CPU-only and available GPU encode/filter/decode tests. Exact user's target PC gate remains OPEN until actual run. A packaging startup test is not media playback/export or installer acceptance.

## External matrix

All ten source platforms × URL kind × media kind × public/account scope × enumerate/paginate/download/subtitles/sync are independent cells. Each declared capability requires permitted live URL, timestamp, connector/tool versions, completion/partial flags, account identity scope, actual validated output and second-sync result. Rate limit/private/unavailable cells retain blocked/error status. Do not expose URLs/account IDs in public fixtures when private. Chrome evidence tests official Windows Chrome, A(FacebookA+TikTokA), B(FacebookB), open/locked/restart/expired/challenge/mismatch, bridge and source rights separately. No credentials are entered by automation on behalf of user without authority.

Translation: rights-cleared Chinese→Vietnamese corpus covering proper names/glossary/long cues/context; exact cue mapping and usage; human adequacy review; configured spending cap, unknown-billing fault/reconcile tests. Local fake provider only tests adapter behavior. GPU lists are not execution proof: actual tiny encode/decode/filter and fallback separately. Installer provenance/license/signature/hash must be established before download execution/distribution.

## Evidence schema and gate

Each record: `{id,generation:clean-2026-11-01,commit,task_ids,criterion_ids,kind:unit|integration|gui|live|target|manual_review,command,environment,tools,corpus_hashes,started_at,finished_at,status:PASS|FAIL|NOT_RUN|BLOCKED,observations,artifact_paths,limitations}`. No blank commit for accepted runtime evidence; plan review can use document hash. Evidence list empty at start. Source group accepted only if all mandatory children accepted; task/phase gate aggregates without treating skipped as pass. One aggregate owner per checkpoint. Reviewer verifies semantics beyond JSON shape/counts.
