# Publication live-anchor correction — CLEAR for scoped target testing

Pinac4f0633e82b4151d8c30efa5e454862969a35ba versus8acfdc. Original inode-resurrection finding CLOSED for explicitly live-session-only substrate.

Exclusive-created payload descriptor is duplicated before writer closes, then retained by Destination ExitStack untilclose. Receipt operations require original live descriptor's physicalidentity. Original inode therefore cannot be freed/recycled during this session even if its pathname is removed. Actual payload/final path checks still require same physicalobject and validated content; no hash-only fallback. POSIXdestination fd and Windowsdirectorypins continue protecting root operation identity. Recreated directory namespace alone cannot resurrect a different file as owned while original fileanchor remainslive.

New Destination/restart has no anchor and always returnsUNKNOWN from persistedreceipt, regardless of apparentlymatchingnames/identity/hash. Thus recovery no longer makes unsupported continuity claims. Fullincarnation-safe restart recovery remains an explicit P03-06 gap, not a removed requirement or completed feature.

Independently5focusedLinuxPASS: retainedlink/reopenUNKNOWN, identicalforeign, replacement,2realchildkillcases;23deselected. No aggregate/Windowsrerun. Childkill tests correctly prove preservedoutput + UNKNOWN, not successfulrecovery. PermissionError branches are Windows-only pinbehavior, not simulatedPASS of replacementverification. Additional live-missing-path negative on platforms allowingunlink would strengthen coverage without changing verdict.

No remaining source blocker found for this bounded substrate. CLEAR FOR TARGET TESTING only; no durablejournal, jobsuccess, streamingmediawriter, cleanup, completepublicationcriterion or powerlossacceptance. Earlierledger743b27f remainsindependentlyCLEAR. This technicalreview grants no new remoteauthorization: existingpublicationdenial/approval handling remainsroot's responsibility. No trackedsource/remotemutation byreviewer.
