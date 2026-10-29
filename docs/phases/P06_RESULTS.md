# P06 — Kết quả phụ đề

Đã có SRT/VTT/ASS bằng pysubs2, cue ID/source/lock, kiểm tra timing, xuất no-overwrite, Google/LibreTranslate adapters, cache, quota reserve và thuật ngữ bảo vệ có kiểm tra marker. 3 test chuyên biệt qua cho Unicode round-trip, lock/cache/glossary/quota và warning. Transport test được gắn nhãn; không coi là chất lượng dịch live đã đạt. UI và burn-in nối chung compositor/app tiếp theo.

Vòng tích hợp thêm draft tự lưu, tìm/thay/offset, dịch câu chọn và nạp kết quả giữ sửa tay. Song ngữ có hai layer gốc/đích riêng; batch bind theo role/ngôn ngữ, auto chỉ dịch đích. Sửa recovery tái dùng file dịch cùng nội dung, giữ file đã chỉnh tay. Xem [báo cáo local cuối](../LOCAL_VERIFICATION.md).

## P06-06 — Atomic create-only subtitle publication (29/10/2026)

[Plan](P06_ATOMIC_SUBTITLE_PLAN.md) preceded [code 47f1534](https://github.com/danhgold7979-cyber/fonesi-edit/commit/47f15345d0533a5a14b884c0f45f438d7ac51139) and [test 62cedf7](https://github.com/danhgold7979-cyber/fonesi-edit/commit/62cedf7cf8a9130bb04cd3419a5fb388e70d08a9). New SRT/VTT/ASS outputs are serialized before publishing, written to a same-directory temporary file and fsynced, then atomically linked under the final name without overwriting a concurrent existing file. Existing overwrite mode still uses staged `os.replace`. Failed fsync, competing output and unsupported hard links remove only the temp and preserve original/manual files. A hard-link-free filesystem fails explicitly rather than exposing partial output.

[CI 40862447183](https://github.com/danhgold7979-cyber/fonesi-edit/actions/runs/40862447183) **SUCCESS on code/test SHA 62cedf7**: **556 Linux passed; 555 Windows passed + 1 intentional POSIX fixture skip**; plan validation, desktop/native-host build and frozen packaged application proof PASS on both runners. This is source/synthetic failure-injection proof, not real FAT/exFAT or power-loss validation.

## P06-06 — Verify cached source/translated subtitle files before attachment (29/10/2026)

[Plan](P06_ATTACH_RECONCILIATION_PLAN.md) preceded [Qt code 536225a](https://github.com/danhgold7979-cyber/fonesi-edit/commit/536225a128f0805aa1ede012605263df607450c0) and [test 1532c12](https://github.com/danhgold7979-cyber/fonesi-edit/commit/1532c127b31ef21586d81baf0b1dad7465b57312). `SubtitlesPage.attach` now reads back existing generated source and translated SRT sidecars and verifies cue text/timing before touching the Editor model. It refuses altered or linked paths rather than silently reusing a stale hash-derived filename. Tests cover edited source/target bytes, unchanged composition on failure, symlink-detection branch and clean reuse.

[CI 40863067947](https://github.com/danhgold7979-cyber/fonesi-edit/actions/runs/40863067947) **SUCCESS at exact SHA 1532c12**: **558 Linux / 557 Windows passed + 1 intentional skip**, packaged desktop/native-host and frozen proof PASS both systems. Symlink rejection uses a cross-platform mocked detection branch; actual Windows symlink/ACL tests remain open.

## P06-04 — Lossless bilingual split/merge (29/10/2026)

[Plan](P06_BILINGUAL_CUE_EDIT_PLAN.md) preceded [pure implementation dd0db74](https://github.com/danhgold7979-cyber/fonesi-edit/commit/dd0db749686a8a75d4b30457eb8ff73c9c0f0766) and [Qt integration 6cad9d2](https://github.com/danhgold7979-cyber/fonesi-edit/commit/6cad9d2b542dfb0ec09e951e2bcc09a0c04bbd25). Splitting CJK/Latin captions now retains every character in source and target strings, maps two positive time intervals, propagates cue lock and refuses one-character/too-short cues without fabricating `…`. Merge preserves both languages, lock state and overall time coverage. Pure tests and Qt split/merge regression were added.

An intermediate [test-only CI 40863617405](https://github.com/danhgold7979-cyber/fonesi-edit/actions/runs/40863617405) failed two assertions because expected Python newline literals had been double-escaped; [test fix f94eb64](https://github.com/danhgold7979-cyber/fonesi-edit/commit/f94eb646727a3ae1746a25d9367b8a7b26779ddc) corrected the expectations without weakening any production invariant.

**Verified final integrated source/test commit:** [99f1be8](https://github.com/danhgold7979-cyber/fonesi-edit/commit/99f1be8fbc7f6f1ce9f8b0c3fe63959a7bf5e1fc), [CI 40863776921](https://github.com/danhgold7979-cyber/fonesi-edit/actions/runs/40863776921) **SUCCESS: 562 Linux passed / 561 Windows passed + 1 intentional POSIX skip**; plan checker, production desktop/native-host and frozen packaged proofs PASS both runners.

**Still OPEN:** full undo history for subtitle table, per-cue drag on timeline, provider-live Chinese/Vietnamese quality and cost, long media/text corpus, real Chrome/auth, Windows physical-device installation, GPU/font/HiDPI, non-NTFS ACL/hard-link behavior and power-loss durability. These checks do not close P06 overall.

## P06-04 — Undo/Redo for the cue table and native focus policy (29/10/2026)

[Plan](P06_CUE_UNDO_PLAN.md) preceded [source and regression commit 39dc892](https://github.com/danhgold7979-cyber/fonesi-edit/commit/39dc8927cb6b372974f8e1e599331374d4f0a389), which adds `CueEditHistory` to the existing desktop tab: the last 100 **in-session** raw table states (original/translation/timestamp/lock/stable cue ID). Cell changes and complete bulk operations become Undo steps; Undo/Redo restore rows without reparsing invalid time drafts or creating recursive history, invalidate redo on new edit and persist the restored draft. Loading another subtitle document resets cue history without resetting canvas Undo. The global shortcuts Ctrl+Z/Ctrl+Shift+Z route to cue history only when the Subtitle tab is selected; native text editing and IME remain protected.

[First CI 40867002996](https://github.com/danhgold7979-cyber/fonesi-edit/actions/runs/40867002996) failed one focus-widget assertion on both runners: editable Qt combo owns focus by proxy for its embedded QLineEdit. [Fix 8bfddb8](https://github.com/danhgold7979-cyber/fonesi-edit/commit/8bfddb8eef811b4421e7c2d7e2a3c02d197a3c3f) routes native Undo/Redo to that editor and accepts both documented Qt focus targets in the regression; all other tests remained active.

**Verified:** [CI 40867450628](https://github.com/danhgold7979-cyber/fonesi-edit/actions/runs/40867450628) **SUCCESS on exact code/test commit `8bfddb8`**, **568 Linux PASS / 567 Windows PASS + 1 intentional POSIX-only skip**, plan checker, desktop/native-host build and synthetic localhost frozen application proof **PASS on both**. Windows development build artifact was created.

**Still open:** unlimited or crash-persistent undo journal, per-cue drag on the time ruler, live provider quality/cost/language, large/long subtitle corpora, physical Windows input/focus/IME/HiDPI, actual Chrome session, non-NTFS hard links/ACL, GPU and power-loss. P06 **not fully accepted**; intermittent SQLite Windows [#6](https://github.com/danhgold7979-cyber/fonesi-edit/issues/6) also remains unresolved.

## P06-05 — Selected-cue timing lane with atomic Undo (29/10/2026)

[Plan](P06_CUE_TIMELINE_DRAG_PLAN.md) preceded [feature 13d9757](https://github.com/danhgold7979-cyber/fonesi-edit/commit/13d97573d9377eaf8fa3a4020a48613bbe946bf6) and [regression a6adf88](https://github.com/danhgold7979-cyber/fonesi-edit/commit/a6adf8861e195a33aa577054da13b2eec1adc57e). The integrated Subtitle tab now displays the selected cue on a bounded timing lane; users can drag its center or start/end handles. Geometry is clamped to valid positive cue durations and time zero, invalid raw time fields disable dragging, Esc cancels without committing. Release updates only that row's two time cells and records one Undo snapshot; original/translated text, lock and stable cue ID are retained. Tests exercise Qt mouse drag, both handles, no-op, cancel, Undo/Redo and valid/invalid timing.

[CI 40871166276](https://github.com/danhgold7979-cyber/fonesi-edit/actions/runs/40871166276) **SUCCESS on exact source/test SHA a6adf886**: **579 Linux PASS / 578 Windows PASS + 1 intentional POSIX fixture skip**. Plan validator, production app/native-host build and frozen packaged proof PASS both OS.

Still OPEN: multi-cue drag, composition trim/speed preview-export parity, long/high-FPS timeline interaction on end-user Windows/HiDPI, persistent Undo journal and [SQLite issue #6](https://github.com/danhgold7979-cyber/fonesi-edit/issues/6). Full P06 not accepted.

## P06-01 — Explicit lossy-style warning when importing ASS/SSA (29/10/2026)

[Plan](P06_IMPORT_STYLE_WARNING_PLAN.md) preceded [parser  b9ec674](https://github.com/danhgold7979-cyber/fonesi-edit/commit/b9ec674eaf1a94aefc535fc48150dc78aa7a2479), [Qt integration 2a4b852](https://github.com/danhgold7979-cyber/fonesi-edit/commit/2a4b8526503b32d8c83a15ea1bd51fc8939531c6), [tests f734e39/235e225](https://github.com/danhgold7979-cyber/fonesi-edit/commit/235e225d1d5e5f565a3c52e61147e8a08d08af5c) and [Qt tests 67c8d01](https://github.com/danhgold7979-cyber/fonesi-edit/commit/67c8d01590b80d1b4cb8d13f2c71a64b5852e38e). `read_captions_with_warnings` retains existing normalized cue/time behavior while warning that ASS/SSA style, position, effects and karaoke may not roundtrip through the plain cue model. Inline ASS override tags in other formats also trigger a caution. Import source bytes are unchanged; clean SRT does not get a false warning. The existing background Open action shows recognized diagnostic strings alongside cue timing warnings and persists them with the draft through edit/Undo/reopen, resetting them when a plain document is loaded. Original `read_captions` worker/render interface is preserved.

[CI 40872415258](https://github.com/danhgold7979-cyber/fonesi-edit/actions/runs/40872415258) **SUCCESS on exact code/test SHA 67c8d015**: **582 Linux PASS / 581 Windows PASS + 1 intentional POSIX-only skip**, plan checker, production desktop/native-host and synthetic/localhost frozen application proof PASS both runners; a Windows development artifact was uploaded.

**P06 still IN PROGRESS:** this is an explicit warning, **not** a style-preserving ASS roundtrip. Live translation/provider quality, large media corpus, composition trim/speed parity, physical Windows user hardware/IME/HiDPI/fonts, real Chrome/auth, GPU, non-NTFS hard-link/ACL and power-loss acceptance remain OPEN; intermittent SQLite [#6](https://github.com/danhgold7979-cyber/fonesi-edit/issues/6) unresolved.
