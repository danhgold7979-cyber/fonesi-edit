# Rebuild P04-05/P07-07 — trim and speed vertical slice

Extend real CPU proof to one ClipMap (source interval, rational speed, output offset must be zero). Narrow supported speed 0.5–2; GUI later gets start/end/speed numeric inputs. Existing source preview remains explicitly pre-edit, never label it output parity. FFmpeg local help confirms trim duration options and atempo range; select bounded common range for proof. Video trim -> PTS reset/speed; audio atrim -> PTS reset -> atempo preserves pitch. Expected duration = interval/speed, with explicit caller policy. Invalid ranges/speed rejected before encode, no silent clamping. No transitions/concatenation/subtime remap or VFR parity claims.

Test real 2s video+tone -> [.5,1.5) at2x -> approximately0.5s, both streams retained, decoded; reject beyond source/offset/speed. Preserve same output publication and cancellation guarantees. Render config immutable ClipMap; queued job snapshot integration remains open.
