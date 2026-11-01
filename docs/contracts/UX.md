# Eight-area desktop interaction contract

Vietnamese interface; native dense desktop. Historical references in `../reference/old-evidence/` are not new-app screenshots. Keep media left, preview center, inspector right, timeline bottom. Red circle identifies the Edit conversation, not a requested app redesign. Shared current Project/selection/undo and durable Job coordinator, no independently simulated pages.

| Area | Controls / units / model | States and recovery |
|---|---|---|
| Tổng quan | current jobs, recent projects, measured metrics+timestamp, workflow shortcuts | empty invites open/import; metrics unavailable=unknown; stale timestamp shown; click job navigates exact queue ID |
| Tải nội dung | URL list/import, platform/type, account/public, filters date/duration seconds/resolution/count, tree checkbox, destination/preset, scan/enqueue | invalid URL inline; scanning count not guessed%; partial cursor clear; auth→correct profile; unsupported capability reason; cancel retains already found selection labelled partial |
| Phụ đề | media/track/cue selection, original/translation, language/provider, glossary, find/replace, split/merge/lock, time ms, offset, style, export | missing/ambiguous requires select; provider absent disables translate with configure route; quota/unknown billing separate; locked edit survives repeated translate; invalid times shown not silently fixed |
| Editor | asset/layer tree; preview handles/anchor/grid/safe area/snap/zoom; inspector basic/advanced/search; timeline/playhead/tracks; undo/save/output region | empty import; missing resource relink; stale render badge; unsupported property blocks export; escaping drag/crop restores prior; focus text/IME suppresses canvas shortcuts |
| Edit hàng loạt | multi-root chooser/tree/filter/invert/exclude, preset scope, audio assignment/manual playlist, duration mode, output preview, sample/full enqueue | scan cancellation keeps draft selection; per-item warnings; ambiguous same-basename audio not guessed; mode change preflight; repeated submit same request id returns existing batch |
| Ghép theo cảnh | C/G natural order/drag/lock/exclude, N/W/K/scope/seed/budget, generate, editable rows, preview, CSV, reserve/render | empty scene invalid; contradiction exact; timeout partial not impossible; edit invalidates dependent constraints; regenerate never touches running row snapshot |
| Hàng đợi/Lịch sử | state+stage, real progress/time/ETA, priority/pending reorder, pause/cancel/retry, artifacts/errors | pending empty; queue pause stops admission; cancel confirmation per scope; late publish explains completed; crash recovery labelled; open output only verified artifact |
| Preset/Cài đặt | scoped preset import/export/version, tool inventory, Chrome/profile/account per ten platforms, provider, resources, shortcuts/layout/theme | missing tool leaves app open; explicit invalid path no fallback; install/download/cancel per component; independent tool/session/source axes and exact repair buttons |

All editable controls expose value/unit/reset and disabled reason; basic hides advanced detail but preserves values. Defaults from PR§10, COMPOSITION and PRESET. Scope always visible: current clip / selected clips / batch preset. Property editing affects one authoritative model, not widget-only values. Layout persistence stores panels/theme/font size, independent of project media content. Resize/zoom changes view only; coordinates in output pixels/normalized canvas. Focus/IME commits text before global actions; inherited ED§9 shortcut table remains normative and remapping detects conflicts.

## Flows and cancellation/repeated actions

1. Download: paste URL(1)→saved account/destination/preset review→Scan(2)→select items if needed→Enqueue(3). Preflight snapshots IDs; invalid source stays in Downloads with fix. Cancel scan never claims all-channel completion; second enqueue same request key does not duplicate.
2. Batch: select folder(s)(1)→preset(2)→sample/impact preview(3)→enqueue(4). No mandatory per-video interaction. Folder dialog cancel no change; newer filter invalidates old planning result; queued snapshot preserved on later edits.
3. Subtitle: select media/sub(1)→language/provider(2)→Translate(3)→review/edit/lock→preview/export(4). Font change never translation request. Cancel network request records unknown outcome if submitted; no false refund/success.
4. Logo: drag asset→canvas select→drag/resize/rotate→release(one undo command)→save. Esc aborts transient drag; crop has explicit apply/cancel; newer selection discards stale background preview without changing project.
5. Matrix: choose scene root(1)→review order/constraints/audio(2)→Generate(3)→review/edit/lock(4)→Enqueue(5). Cancel generation creates no reservations; edited row revalidates window; retry reuses same row/seed/assets.
6. Repair: queue blocked→open exact setting/profile/media ref(1)→repair and verify(2)→Resume(3). Account identity mismatch requires deliberate rebinding/new snapshot, not automatic resume as new user.

Counts are ordinary command counts excluding file-dialog navigation/first-time login and voluntary detailed edits; measured usability, not a permission to remove preflight.

## Tools and account tables

Tool row name/role/workflows/required status/origin/path/version/architecture/capabilities/check time; Scan/Path/Test/Install/Update/Repair/Rollback/Remove-owned. Initial background scan bounded; explicit path precedes Auto; busy installation lease blocks removal. Unknown-size download shows bytes, no invented percentage; group install tracks per-tool result. Driver/UAC installer opens only user-authorized flow and remains pending until verified.

Chrome profiles owned user-data-dir ID/name/installation/browser-state; create/name/open/default/check independent from website sign-in. Ten platform rows: YouTube,Bilibili,TikTok,Facebook,Instagram,Threads,X,Douyin,Xiaohongshu,Kuaishou. Each platform supports add account/open official login/check/relogin/default/unlink. No credential entry in app. Show web identity, connector bridge and source rights separately with checked timestamp; unknown never green ready. Profile A multiple platforms and profile B same-platform alternate identity are distinct. Unlink is not logout/delete-profile; destructive profile deletion separately confirmed. Ctrl+, settings; F5 scoped only tool table, not Chrome.
