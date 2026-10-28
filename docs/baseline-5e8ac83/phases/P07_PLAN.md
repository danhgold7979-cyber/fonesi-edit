# P07 — Compositor dùng chung

Đã đọc master P07, ED 3–7, domain và P06_RESULTS. Backend tạo CompositionPlan thật cho mọi render/batch/matrix/reference; canvas draft không được dùng làm bằng chứng parity.

1. Normalize clip trim/speed/fit/crop/rotation/FPS; concat/transition và audio; kiểm tra duration trước xuất.
2. Font metadata/glyph, ASS text/subtitles với style/alpha/rotation/scale, đúng thứ tự layer; file text/path không đi vào biểu thức shell.
3. Motion expression AST chung có đánh giá Python và FFmpeg, keyframes/easing/preset/seed; mọi giá trị người dùng được validate numeric.
4. Image alpha/scale/rotate/overlay; mask blur/mosaic/color, interval/opacity. Không nhận unsupported feature như đã render.
5. FFmpeg worker progress/cancel/validation/no-replace, source/config hash và manifest artifact; preview frame dùng chính backend.
6. Test render thực nhiều clip/layer/cue/audio, motion AST/time, CPU fallback và output không ghi đè. Windows/GPU thực vẫn mở.
