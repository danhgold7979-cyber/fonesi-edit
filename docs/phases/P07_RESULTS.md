# P07 — Compositor local

Đã có normalize/trim/speed/fit/crop/blur nền/concat/xfade/audio mix, ASS font/style/alpha/rotation/scale, image alpha, mask, motion AST dùng chung, reference render, GPU capability probe và manifest/hash/no-overwrite/reuse. 14 test compositor/motion đã qua với render thực nhiều clip/text/logo/mask/sub/audio và crossfade/crop/reference.

Đây không phải nghiệm thu mọi tổ hợp font/Windows/GPU hoặc mọi lựa chọn UI. Những thuộc tính chưa có kiểm tra/render chính xác phải tiếp tục theo dõi ở P11, không đánh dấu đủ toàn bộ P07.

Vòng tích hợp thêm subtitle layer kéo được với cue track chung, font collection TTC/OTC, style/line spacing/padding/background và font riêng trong canvas; motion/feather/rotation/mosaic, video random zoom, solo âm thanh thực và giữ flip/rotation trong fit blur. Xem [báo cáo local cuối](../LOCAL_VERIFICATION.md).
