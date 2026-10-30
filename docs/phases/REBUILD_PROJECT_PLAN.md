# Rebuild P03-02/07 — project save/open without media mutation

Schema1 project stores UUID, title, ordered unique media IDs, absolute source references, optional rational ClipMap. No arbitrary config, cookies, keys, profiles or executable commands. 4MiB document limit, at most1000 items, duplicate keys and unknown fields rejected, exact nested field checks. Project load never invokes external programs automatically; GUI probes selected media only after explicit open/import action.

Save-as creates a new immutable project file via owned staging + fsync + no-overwrite atomic link. Existing projects never overwritten by this slice; future Save/autosave needs generation-aware version history/backup separately. Missing media references retained for relink, not silently discarded. Tests roundtrip time precision, unknown/secret fields, duplicates, future versions, missing media preservation and collision leaves original bytes. Rebuild schema intentionally distinct from old project exports; unsupported old documents rejected, not migrated by guesswork.

Current schema only supports output_start0; unsupported timeline offsets reject rather than silently drop. UI keeps exact rational source model across unedited load/save, separate from display decimals; a deliberate numeric edit creates the new exact decimal rational.
