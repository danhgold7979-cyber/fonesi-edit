# P04 — Kế hoạch chi tiết editor/timeline: vòng hoàn thiện tương tác

**Cập nhật:** 28/10/2026. **Nhánh duy nhất:** `develop/fonesi-full`. **Tình trạng:** kế hoạch trước khi sửa mã P04; P03 đã có code và chạy CI, cổng máy Windows thật vẫn tách riêng.

## 1. Đối chiếu master plan

Đã đọc `docs/IMPLEMENTATION_PLAN.md` (P04-01 đến P04-08), `docs/EDITOR_SPEC.md`, `docs/REQUIREMENTS_TRACEABILITY.md`, `docs/IMPLEMENTATION_COVERAGE.md`, `docs/CURRENT_STATUS.md`, P03_RESULTS và P04_RESULTS. Kiểm tra mã hiện có trong `ui/canvas.py`, `ui/editor.py`, `ui/timeline.py` và `tests/test_editor.py`.

Nền hiện có: Qt/PySide6, canvas/inspector, lựa chọn nhiều layer, undo/redo, timeline clip/audio, in/out, split, waveforms và playback. **Không viết lại app, không đổi định dạng project**; tất cả chỉnh sửa đều trên một nhánh chung và một binary Windows.

## 2. Những sai lệch được xác định

- P04-02: snap hiện tại so `x/y` góc trên trái với 0.5, không phải tâm hình; kéo các layer chọn cùng nhau có thể làm hỏng khoảng cách tương đối khi chạm ranh giới vì mỗi layer bị clamp độc lập.
- P04-02/P04-04: thao tác kéo/resize có thể cho khung chạy khỏi canvas, phụ thuộc tọa độ không chuẩn; cần kiểm thử nhóm và undo.
- P04-01/P04-02: hiển thị safe-area có sẵn nhưng chưa có lưới căn chỉnh tùy chọn/lưu trạng thái trong project.
- P04-05: timeline cần bảo vệ chống trim âm và kiểm chứng tương tác khi zoom; hiện tại UI layer kéo/thay đổi đã có.
- P04-06: proxy đa mức, thumbnail strip, playback loop đoạn, HiDPI/seek parity còn mở; **không giả làm đã đạt** nếu lát cắt chưa thực hiện.

## 3. Lát cắt triển khai trước mắt

1. Tạo hàm tọa độ độc lập kiểm thử được: snap **trung tâm lớp** vào trung tâm canvas, snap rìa vào safe area khi gần, tắt snap tạm bằng Alt; giới hạn vị trí theo kích thước layer.
2. Với multi-select/nhóm, tính delta chung và clamp theo bounding box tập lựa chọn để giữ khoảng cách giữa các layer; giữ đúng một undo cho một cử chỉ kéo.
3. Thêm bật/tắt lưới hình học trên canvas, dùng `Composition.adjustments` để giữ trạng thái khi save/open, không đưa đường lưới vào FFmpeg export. Bật/tắt có undo.
4. Tạo regression tests cho tọa độ trung tâm/rìa, Alt tắt snap, group bounds, thao tác undo, serialization trạng thái lưới và invariant không thay file nguồn.
5. Chạy `scripts/check_plan.py`, full `pytest`, build và packaged proof Linux/Windows qua CI; đọc kết quả thực, sửa lỗi chứ không bỏ test.

## 4. Cổng đóng lát cắt

- [ ] Snap đến **tâm** canvas (tính cả width/height), không nhầm góc trên trái.
- [ ] Nhiều layer giữ khoảng cách khi kéo sát mép; không lệch nhóm; undo khôi phục nguyên vị trí.
- [ ] Alt tạm tắt snap; grid on/off hiển thị đúng và lưu/khôi phục qua project.
- [ ] Test regression tự động qua Linux/Windows.
- [ ] Proof binary thực tế vẫn đạt trên CI hai hệ; giữ bản Windows review.
- [ ] P04_RESULTS và CURRENT_STATUS ghi đúng phần đạt/chưa đạt.

## 5. Phạm vi còn mở, không tự đổi thành PASS

Crop bằng tay nắm và tương tác đủ chín điểm neo, proxy chất lượng, timeline thumbnail strip, preview loop đoạn, mọi phím tắt, benchmark trên Windows/HiDPI và đối chiếu từng hiệu ứng với exporter còn phải theo dõi trong `IMPLEMENTATION_COVERAGE.md`. Tiếp tục mã P05–P12 theo master plan sau khi phần P04 có test mà không chờ live platform/API/GPU không liên quan.

## 6. Vòng triển khai tiếp — ED-17/18: thumbnail timeline và loop đoạn (28/10/2026)

Đã đối chiếu lại master `IMPLEMENTATION_PLAN.md` P04-05/P04-06, `EDITOR_SPEC.md` mục timeline/preview, `REQUIREMENTS_TRACEABILITY.md`, `ui/editor.py`, `ui/timeline.py`, `app.py` (playback preview dựng qua compositor), `prototypes/media.py`, `waveform.py` và tests. `P04_RESULTS`/coverage xác nhận thumbnail strip và preview loop đoạn vẫn mở.

**Lát cắt triển khai:**

1. Loop In–Out có bật/tắt trong Editor, chỉ thực hiện seek vòng khi player đang phát **bản preview đã render bằng chính compositor** của composition hiện tại. Không đưa người dùng tới thời điểm sai của file nguồn nếu clip đã trim/speed/transition. Kiểm tra In/Out dương, `out > in`, nằm trong độ dài composition; không thay đổi nguồn, project hay output. Preview sau chỉnh sửa được đánh dấu stale; yêu cầu dựng lại, không chạy loop âm thầm trên bản cũ.
2. Timeline thumbnail là tính năng tùy chọn, checkbox menu bật/tắt lưu trong `Composition.adjustments`. Khi bật, tạo tối đa một số frame/clip (3) qua FFmpeg, theo `clip.start/end`, chỉ với file nguồn local; scale nhỏ, cache theo path/stat/trim/speed, publish atomic, kiểm tra đầu ra, cancel/time budget. Tạo trong task nền, chỉ xếp tối đa số clip đang hiển thị để tránh queue vô hạn; không thay đổi input media hoặc FFmpeg output graph.
3. Timeline vẽ các thumbnail lên clip row từ cache; không truy cập FFmpeg trên UI thread. Khi trim/nguồn thay đổi, cache identity thay đổi. Làm rõ đây là source thumbnail trước transform/compositor, **không** gọi là preview/export parity.
4. Test unit giới hạn loop, thumbnail time-map/identity, PNG thật/không đổi nguồn, Qt offscreen thumbnail tiles/toggle undo và không tạo thumbnail khi tắt. CI full regressions + frozen proof Linux/Windows, chỉ ghi PASS phần có evidence.

**Cổng còn mở:** proxy Nhanh/Cân bằng/Cao và cancellation/invalidation đủ chiến lược, long timeline 4K/HiDPI trên máy người dùng, audio/video sync trong các trường hợp VFR và crop handles/safe areas chưa đủ.

## 7. P04-06 — Proxy phát nguồn local có ba mức (cùng đợt)

Tách rõ **proxy nguồn** và **rendered composition preview**: proxy chỉ tăng tốc phát media gốc ở tab Playback, không thay thế compositor/FFmpeg export hoặc được công bố đã có hiệu ứng đầy đủ. Ba mức Nhanh (cạnh dài ≤640), Cân bằng (≤1280), Cao (≤1920), ngoài chế độ Tắt. FFmpeg transcode h264/aac bảo toàn thứ tự thời gian, không sửa nguồn. Cache trên user workspace, key path/stat/quality, viết tệp tạm + probe/kiểm tra duration + atomic publish, hủy/timeout, giữ bản cũ khi không hợp lệ. UI menu chọn mức, lưu trong project; khi switching clips chỉ tạo một proxy cần thiết qua background và không lạm dụng queue; dùng đúng bản proxy khi người dùng chọn, không áp dụng trên rendered preview. Test cache/invalidations/no source mutation, UI picker, actual media decode. Cổng Windows real-time performance và proxy long media vẫn cần nghiệm thu riêng.


### Kết quả lát cắt P04-05/06 (28/10/2026)

- [x] Loop In–Out chỉ dùng rendered preview theo fingerprint; không dùng file nguồn raw cho thời gian composition.
- [x] Thumbnail 3 ảnh/clip, cache/validation/cancel, tạo nền theo viewport, undo bật/tắt.
- [x] Source proxy Off/Nhanh/Cân bằng/Cao, không upscale, validated/no source overwrite.
- [x] Full source/packaged Linux/Windows CI [run 40649687637](https://github.com/danhgold7979-cyber/fonesi-edit/actions/runs/40649687637) PASS.
- [ ] Crop handles/anchor, HiDPI/4K/VFR/seek/audio sync/phím tắt đầy đủ và nghiệm thu PC Windows người dùng còn mở. Không tick toàn bộ P04 trong master.


## 8. P04-02 — Neo nhanh 9 vị trí cho layer/nhóm (28/10/2026)

**Lý do:** ED-02/ED-04 trong `REQUIREMENTS_TRACEABILITY.md` yêu cầu neo đối tượng; mục 4 `EDITOR_SPEC.md` quy định chín vị trí nhanh và lề. `docs/IMPLEMENTATION_COVERAGE.md` vẫn ghi thao tác neo/crop chưa đầy đủ. Canvas hiện có kéo, resize, xoay và căn giữa riêng trục, nhưng chưa có bộ neo 3×3.

**Phạm vi lát cắt này:**
1. Thêm helper thuần để tính delta từ bounding box hợp của một hay nhiều layer đến neo trái/giữa/phải × trên/giữa/dưới; mặc định lề an toàn 5% mỗi cạnh, giảm lề tự động khi nhóm quá lớn nhưng vẫn vừa canvas, từ chối nếu nhóm vượt kích thước canvas.
2. Thêm submenu “Đặt neo 9 vị trí” trong Editor. Hành động áp dụng cho layer đã chọn và các thành viên không khóa thuộc cùng group, dùng một delta chung để giữ khoảng cách tương đối; không di chuyển layer khóa.
3. Một thao tác neo là một undo/redo nguyên tử; cập nhật canvas/inspector bằng đường refresh hiện có. Không đổi schema project, tọa độ xuất, hoặc tệp nguồn.
4. Test helper cho đủ chín vị trí, lề, group-size biên và anchor không hợp lệ; test Qt cho group/locked layer, một bước undo/redo và menu.

**Kiểm tra:** `uv run python scripts/check_plan.py`, `uv run pytest -q`, sau đó CI source + frozen proof Linux/Windows. Không ghi pass cho đến khi đọc kết quả của commit mới.

**Không thuộc lát cắt:** crop bằng tay nắm và preview/export crop parity; các mục này tiếp tục mở trong coverage/master cho phase kế tiếp.


## 9. P04-02 — Crop thủ công theo nguồn video (28/10/2026)

**Đối chiếu trước code:** `EDITOR_SPEC.md` yêu cầu khung crop có tay nắm, tỷ lệ khóa và xác nhận/hủy; `REQUIREMENTS_TRACEABILITY.md` ED-02/ED-16 yêu cầu crop có thể lặp lại ở các độ phân giải. Hiện `Clip` chỉ có trim/speed/flip/rotation, `ClipDialog` chưa lưu vùng crop và `compile_graph` chỉ có fit/crop toàn khung.

**Phạm vi lát cắt:**
1. Thêm vùng crop chuẩn hóa theo nguồn video `x/y/width/height` (0–1), mặc định toàn khung để giữ tương thích project cũ. Validate hữu hạn, dương, không vượt khung; không thay đổi đường trim/time map.
2. Thêm `CropDialog` với frame nguồn thật, lớp phủ tối bên ngoài vùng crop, tay nắm 8 cạnh/góc, kéo cả vùng, lưới căn chỉnh và checkbox khóa tỷ lệ theo tỷ lệ pixel của crop hiện tại. Hủy không sửa project; OK chỉ cập nhật bản nháp ClipDialog.
3. Thêm filter FFmpeg crop trước flip/rotate/fit, đổi vùng chuẩn hóa sang pixel theo kích thước nguồn đã probe, bảo đảm tọa độ/kích thước chẵn an toàn cho yuv420p. Giữ output size, audio, subtitle timing và nguồn nguyên vẹn.
4. Thêm test domain cho crop thiếu/biên/sai, helper hình học cho kéo/resize/khóa tỷ lệ, UI round-trip/cancel và render thật có crop. Project cũ không có trường crop phải tiếp tục load.
5. Chạy check-plan, toàn bộ pytest, build + frozen proof Linux/Windows. Chỉ ghi kết quả sau khi CI hoàn tất.

**Ngoài phạm vi lát cắt:** crop từng layer ảnh/logo và crop export preview parity cho mọi tổ hợp rotation/VFR; nếu còn thiếu sẽ ghi rõ ở coverage thay vì đánh dấu ED-02/ED-16 đã hoàn tất.


## 10. P04-03 — Interactive crop dialog (28/10/2026)

Crop engine P04-02 đã được đưa vào `Clip` và compositor; CI lần đầu bắt được sai kỳ vọng pixel lẻ và test hard-code kích thước nguồn. Hai lỗi đã được sửa ở các commit test kế tiếp; không được coi crop engine là pass cho đến khi CI mới nhất xác nhận.

Phạm vi giao diện tiếp theo: hiển thị frame nguồn, overlay ngoài vùng crop, kéo vùng/tám cạnh, lưới 3×3, checkbox khóa tỷ lệ, reset và center; thao tác dialog chỉ sửa bản nháp và Cancel không thay đổi project. Sau code phải bổ sung test Qt, chạy `scripts/check_plan.py`, toàn bộ suite và packaged proof Linux/Windows.


## 11. P04-04 — Keyboard shortcut focus policy (28/10/2026)

**Rà soát master plan trước code:** P04-07 yêu cầu shortcut theo focus, remap/xung đột/trợ giúp và không để nhập tiếng Việt/Trung kích hoạt player/canvas. `app.py` đã có action menu và remap, nhưng hiện chỉ nhường shortcut cho ba lớp text cơ bản; spin box, combo box, item view, checkbox và editor con có thể nhận shortcut toàn cửa sổ không đúng ngữ cảnh. Remap hiện cho phép gửi JSON thiếu key nhưng lưu trực tiếp map một phần, khiến action runtime và thiết lập sau khi mở lại có thể khác nhau.

**Phạm vi lát cắt:**
1. Thêm policy thuần nhận diện focus widget qua chuỗi parent: text editor (QLineEdit/QPlainTextEdit/QTextEdit), input/control (spin box, combo box, item view, slider, button) và focus thường.
2. Khi focus ở text editor: Undo/Redo đi vào lịch sử cục bộ của control; các action editor như Play/Marker/In/Out/Split/Group/Lock/Render không chạy. Khi focus ở control khác, các action editor tương tự phải nhường cho control. Các action app-level Open/Save/Settings/Help/Scan giữ nguyên.
3. Chuẩn hóa và xác thực shortcut: chỉ nhận chuỗi hợp lệ, cho phép giá trị rỗng để tắt, chặn shortcut trùng sau chuẩn hóa, báo lỗi nếu chuỗi không hợp lệ; remap từng phần phải merge với cấu hình hiện tại rồi lưu đầy đủ để runtime và restart nhất quán.
4. Test Qt cho line edit/IME-style editing, spin box, combo box, item view, focus canvas, Undo/Redo cục bộ, conflict và partial remap. Không mô phỏng đăng nhập hoặc gửi network.
5. Chạy `scripts/check_plan.py`, toàn bộ pytest, build và frozen proof Linux/Windows; chỉ ghi kết quả sau CI.

**Ngoài phạm vi:** remap theo từng workspace/profile, tổ hợp nhiều bước và các phím tùy biến theo thiết bị. Không đổi phím mặc định nếu không cần thiết.


### Kết quả P04-02/P04-03 — Crop source (28/10/2026)

CI [40686663256](https://github.com/danhgold7979-cyber/fonesi-edit/actions/runs/40686663256) PASS: 262 Linux, 261 Windows + 1 skip; packaged proof hai hệ PASS. Test có crop geometry/pixel bounds, render FFmpeg thật, preview pixel, drag Qt, cancel và Undo. Tách riêng các cổng crop ratio/rotation metadata/VFR/HiDPI/4K/Windows máy người dùng; không đánh dấu hoàn tất toàn bộ P04.


## 12. P04-05 — Shortcut remap failure handling (28/10/2026)

Bổ sung bước hardening: JSON người dùng nhập sai phải trả lỗi có kiểm soát, không làm văng slot UI; remap từng phần phải merge với map hiện tại; lưu map đầy đủ trước khi cập nhật QAction để tránh runtime/settings lệch nhau khi storage ghi thất bại. Test helper parser JSON và giữ nguyên hành vi merge/conflict. Chạy full source/packaged CI hai hệ; nếu storage lỗi ngoài các exception dự kiến, giữ nguyên runtime state và ghi blocker.


## 13. P04-06 — Explicit shortcut dispatch policy (28/10/2026)

Tách điều kiện dispatch editor shortcut thành helper thuần, để test ma trận action × focus mà không cần giả lập bàn phím/IME của hệ điều hành. Editor actions nhường cho text/control; app-level actions không bị chặn; global/canvas focus vẫn cho phép editor shortcuts. CI mới xác nhận hành vi code, còn IME/HiDPI/Windows user acceptance giữ riêng.


## 14. P04-07 — Save As project and shortcut-table parity (28/10/2026)

**Master alignment:** `EDITOR_SPEC.md` §9 defines Ctrl+Shift+S as Save As. The current menu has Ctrl+O/Ctrl+S but no Save As action, leaving a documented keyboard path unavailable.

**Implementation slice:**
1. Add `save_project_as` with a native save dialog and `.fonesi` extension normalization.
2. Preserve the current project record before branching to a new project ID; write the selected project file atomically and register the new project in the local Store.
3. If the dialog is cancelled, leave project ID/path and project list unchanged. If the chosen path is the current project file, use normal Save instead of creating a duplicate ID.
4. Expose the action in the shortcut menu with Ctrl+Shift+S; keep remapping and focus-policy behavior from P04-05/P04-06.
5. Add integration tests for independent IDs/files, cancel semantics, same-path save behavior and the registered shortcut.
6. Run plan validation, full source suite and frozen Linux/Windows proof. Do not mark Save As accepted until the new CI run passes.

**Failure handling:** do not change the active project pointer until the destination file and Store record have been written. If Store indexing fails after the file was written, keep the prior project active and report that the standalone file exists but internal indexing did not complete. No secrets or media are copied by Save As.

## 15. P04-07 — Canvas copy/paste/cut and focus-aware Select All (28/10/2026)

**Master alignment:** `EDITOR_SPEC.md` §9 documents Ctrl+A/C/V/X with behavior determined by the focused widget. Existing shortcuts already protect Undo/Redo in text fields, but canvas layer clipboard and the remaining focus-aware editing actions are not yet wired.

**Implementation slice:**
1. Add editor-local layer clipboard for selected layers; copy does not mutate the project or source media.
2. Paste cloned layers with new IDs and remapped group IDs, a small bounded offset, and preserved clip references/style/keyframes. Keep a copied group internally consistent and unrelated groups unchanged.
3. Cut copies first, then removes only unlocked selected layers through one existing undo snapshot; locked layers must remain.
4. Add Select All, Copy, Paste and Cut actions with Ctrl+A/C/V/X. In canvas focus they operate on layers; in text focus the shortcut dispatcher must call the native widget's `selectAll/copy/paste/cut` rather than consuming the keystroke. Controls/list views keep their own selection behavior.
5. Test copy/paste IDs, group mapping, bounded placement, one-step Undo/Redo, cut respecting locks, and focus routing. Do not use the OS clipboard for serialized project data.
6. Run plan validation, focused tests, full suite and frozen Linux/Windows proof. Keep real IME and Windows keyboard acceptance separate.

**Safety:** no source files are deleted or changed; cut only removes layers from the project model. No project schema change and no new dependency.

## 16. P04-02 — Cancel an in-progress canvas drag with Escape (28/10/2026)

**Gap:** the canvas currently rebuilds on Escape, but an in-progress drag mutates the composition model before mouse release. Escape must restore the pre-gesture snapshot rather than merely redraw the mutated state.

**Implementation slice:**
1. Add an editor cancellation path that restores the pending `_before` composition snapshot without pushing an undo command or invalidating the rendered preview fingerprint.
2. On canvas Escape, cancel the active gesture, clear peer-snap guide overlays, and rebuild the canvas. When no edit is pending, preserve the existing Escape behavior.
3. Ensure a later mouse release after cancellation cannot commit the cancelled gesture.
4. Add a Qt mouse-drag regression: move a layer, press Escape before release, release the mouse, then assert the original geometry and unchanged undo count.
5. Run full source suite and Linux/Windows packaged proof; keep OS-level focus/IME acceptance separate.

**Safety:** cancel restores the exact pre-gesture model snapshot; it does not modify source media, project files, or export output.

## 16. P04-07 — Shortcut focus completeness and layer clipboard invariants (28/10/2026)

**Baseline verified before changes:** CI run [40721462280](https://github.com/danhgold7979-cyber/fonesi-edit/actions/runs/40721462280) passed 362 Linux tests and 361 Windows tests plus one intentional POSIX-fixture skip; plan validation, production app/native-host builds and frozen packaged proof passed on both runners.

**Code review findings:**
- `Thêm video` is an editor-scoped action with shortcut `Ctrl+Shift+O`, but is missing from `_EDITOR_SHORTCUT_ACTIONS`. It can therefore fire while a text editor/control owns focus, contrary to P04-07.
- Clipboard tests currently cover basic copy/paste/cut and native text routing, but do not lock down cloned IDs, group remapping, payload preservation, one-step Undo/Redo, locked-layer protection, bounded placement, or isolation from the OS clipboard.

**Implementation plan:**
1. Add `Thêm video` to the editor-scoped focus policy and add regression tests proving it yields to text/control focus but dispatches with canvas/global focus.
2. Expand layer clipboard integration tests for fresh layer IDs, copied-group internal consistency with new group IDs, unchanged unrelated groups, preserved style/keyframes/clip references, bounded placement, and OS clipboard isolation.
3. Verify Cut removes only unlocked selected layers, keeps locked layers intact, and Undo/Redo restores the entire cut as one atomic history operation.
4. Run `scripts/check_plan.py`, the full test suite, production desktop/native-host build and frozen proof on Linux/Windows through CI.
5. Update P04_RESULTS, CURRENT_STATUS, IMPLEMENTATION_COVERAGE and PHASE_EXECUTION_LEDGER only from the resulting CI evidence. Real IME, physical Windows keyboard, HiDPI, live sources, GPU and user-machine acceptance remain separate gates.

**Safety:** no media source is modified/deleted, no project schema change, no serialized layer payload is written to the system clipboard, and no unrelated phase is marked complete.
