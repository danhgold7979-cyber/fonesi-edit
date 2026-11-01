# ProjectStore ownership hardening — local review

Initial verified hashes: projects.py d8307685682ec3579f9e629dff3e1c3e65015cb8ceeb207ff424cf02b5eed782; test_projects.py e9bb154fa4edd195bf3e9ceb8237dcf6e0fd134907c913b903ef2924e47cc8c4; new identity tests 39a5cb15800f32f0dc5498ea46dd8a5f33d35ddfee5b0da1ccdb99a479d37885; updated docs 403e552816249d91b2e17ce0e71f7ae3ba5e36017e33f4cd0dc23ef8ce53f17e.

HOLD: constructor catches Exception only although it now retains an original raw file descriptor. Independently injected KeyboardInterrupt at before_migration; constructor exited with original FD still valid (os.fstat succeeded). Reviewer closed only its own leaked test FD. Catch BaseException for constructor cleanup; preserve SQLite diagnostics conditionally, close all resources, and keep interrupted initialization unmarked/failclosed.

Also requested nonzero inode guard (as other stores already require) and fresh identity guard after schema reads immediately before WAL/receipt mutation. No additional findings.

Independently three receipt/schema/post-COMMIT-exception cases PASS, three deselected. Exact schema before WAL, extra-object rejection, pre-SQLite receipt validation and no unconditional rollback after successful COMMIT otherwise satisfy this bounded hardening. Existing failed-init retry expectation was correctly replaced with explicit recovery refusal, not silent adoption.

No aggregate, provider, remote or CI operations. Full recovery workflow and native evidence remain open.

## Combined correction — scoped CLEAR

Verified projects.py SHA256 75b531e3c634426f05549f3bbe1e312043cb3f5dfacdc9dfcd4b51fb094a7163 and identity-test SHA256 719f62e512c7a9b5afe742ce77ffcd2dfb16facef02f032c54c8503917519e5c; other pins above unchanged.

Constructor now catches BaseException for cleanup, zero inode is refused, and identity checks occur immediately before WAL configuration and receipt registration. Independently three exact new interrupted-init FD closure, unusable identity and replacement-before-WAL tests PASS, six deselected. Interrupted initialization leaves empty/unmarked file for explicit recovery instead of silently reopening. No remaining identified blocker within this ownership-hardening delta.

No aggregate, Windows proof, restore/repair workflow, whole-phase or remote-publication acceptance implied.
