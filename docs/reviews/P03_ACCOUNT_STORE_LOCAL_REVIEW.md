# Local account metadata persistence review

Base local HEAD154a9db. Initial SHA256 verified:
- accounts/store.py 6d752ced3aeedcf34c0112ee4b8a66fcb16b2eae3048d029a5d4a25cfb6c05db
- test_account_store.py b5ead230b9f47d0c4c3a05472975992bcc880bb6b6bf3c074f59eadbe3259976
- ACCOUNT_STORAGE.md fc83baabaa2b09c897de8f8b80a5403aafcabab2f0d371f32609c978930ac5e1

Verdict: HOLD for two concrete defects.

1. Binding identity conflation. Original SETTINGS_AND_BROWSER_SPEC.md section3 lines85/89 requires one signed-in identity per platform per browser profile, while one authenticated identity can access many pages/channels. Existing reviewed Catalog.bind enforces profile/platform uniqueness. New store/tests instead allow channel-A/channel-B as separate Binding.identity values in one profile/platform. Enforce unique(profile_id,platform) for both create/update; keep channel/source access separate (may remain future scope), without requiring a Chrome profile for each channel.
2. Silent unmarked v0 adoption. Constructor initializes any preexisting appID0/version0/empty-schema SQLite file. Reviewer safely created such a 4096-byte unmarked database; AccountStore accepted and modified it. This contradicts stated no-adoption policy. Track exclusive creation, initialize only newly created owned file, and fail closed on preexisting unmarked zero-length or v0 SQLite unless explicit separately authorized adoption is designed. Add untouched-byte/no-receipt negatives.

Independently five targeted stale-CAS, immutable profile identity and foreign/future/malformed tests PASS; seven deselected. Remaining reviewed strengths: strict bounded model allowlist, immutable profile installation/ownership, original FD guard, exact schema check before WAL, metadata/default/unlink transactions and honest historical timestamps. No cookie/browser/provider actions. No full aggregate or remote action.

## Combined correction — scoped CLEAR

Verified corrected hashes: store.py ff274233d0d698f59d1928eee4b1328c5f65c307f9fdeb0b3c1582535ea16d1c; tests 75c2707cb0945d73046004fb6996ec296816cd09cfebd71716161dad12931abe; contract b6c4b64b1d313e9f3de685c3acbf04d9d2686e2b6626d6274d5e10638b520f0c.

UNIQUE(profile_id,platform) now prevents multiple login identities on create/update. Separate bounded SourceAccess rows reuse the reviewed account scope (binding/profile/platform/identity/generation); many channels share one authenticated binding. Writes check current binding version and scope transactionally; identity/generation changes hide old scope observations from current lookup, while preserving historical rows. Unlink cascades metadata only.

Preexisting unmarked/foreign files are rejected before SQLite open, including zero-length and empty v0 stores. New initialization follows exclusive creation; initialization/receipt crash remains explicitly fail-closed.

Independently five correction cases PASS, eleven deselected: both untouched unmarked-file cases, login uniqueness insert/update, multichannel single binding/reopen/unlink, stale rights scope. No full aggregate or live provider test. No remaining identified blocker for bounded metadata persistence. These are last-known observations, never fresh rights/browser admission authority. Native Windows, credential-store/profile-path/job integration and phase acceptance remain open; no remote action/new criterion closure.
