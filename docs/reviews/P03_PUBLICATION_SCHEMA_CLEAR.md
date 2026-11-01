# Targeted schema/design correction — CLEAR for next implementation slice

Pin01abeaa4125e855705e70d80db288bedc8f5e15c/tree02b5df16. Reviewed exactdelta frome534771. Independently4focusedregressionsPASS,12deselected; noaggregate.

Closed: invalid/foreignexistingreceipt now rejected after exactschema validation but BEFOREbackup/WAL/migration; unchangedDB/receipt/no backup tested. Missingversionedreceipt rejectedbydefault, explicitadopt_unmarked only after exactschema. SQL storedCREATEcomparison now preserves literalcase/bytes, closing alteredCHECK acceptance. Historicalnormalizedv1hash is ownershiplineageonly; actualcurrent schema independently exact. Transaction migration now rechecksapplicationID alongsideversion/schema, causalracefixture rejects.

Design entryCLEAR: explicit lifetime markedOSlock, nonblockingcontention, liveFD/namecontinuity, monotonicDBepoch+ownerUUID, set-boundepoch, pertransaction ownershipcheck. Workerlease gatesbeforeclaim; afterclaim coordinatorauthority continues independently of expiringworkerheartbeat. Restartnewowner getsnewepoch and nooldanchoradoption. Existing exactset/finalsuccess-onlytransaction and UNKNOWNrecoverylimitation retained. These are implementationrequirements, not an implementedcoordinatorclaim.

Nonblocking naming clarification beforeAPIs: contract sometimes calls old uncommitted sets UNKNOWN, while artifact_sets stateenum lacksunknown (publications enumhasit). Define UNKNOWN as derived recoveryclassification with publicationsunknown/jobblocked/setunchanged, or explicitly add setstate with migration; do not improvise invalidstatewrites. Priorunpublishedv2prototype has differenttable/signaturehash; do not silently adopt it asnewv2—failclosed or use explicit reviewedmigration if anypersistentuserDB everusedit.

No newblockingfinding within this targetedreview. CLEAR to implement coordinatorfollowingcontract and runaffectedtargettests; no completeP03-06/criterionclosure, no remoteauthorizationoverride. Rootownsdeniedpublicationapprovalhandling. No trackedsource/remotemutation byreviewer.
