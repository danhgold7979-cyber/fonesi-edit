# Rebuild tool provenance

The Windows x64 FFmpeg manifest pins **9.0.2** and SHA-256 `60f467265b1e312373dbcd92200c2618a74850f98d3d078e94296bb3fa2047ba` from the publisher checksum. The download is versioned, HTTPS is retained, archives are path/size checked, and binaries are self-tested before activation. This is an artifact trust pin, not proof of Windows functional acceptance.

Sources checked 2026-10-28:
- [FFmpeg's official download page links the Windows build provider](https://ffmpeg.org/download.html).
- [Gyan Windows builds and version information](https://www.gyan.dev/ffmpeg/builds/).
- [Publisher checksum for 9.0.2 ZIP](https://www.gyan.dev/ffmpeg/builds/packages/ffmpeg-9.0.2-essentials_build.zip.sha256).
- [Provider release/source information](https://github.com/GyanD/codexffmpeg/releases/tag/9.0.2).

No dynamic download of a new checksum silently changes the committed trust pin. A mismatch blocks installation and retains the previous tool. Installer UI is explicit user action; no driver changes or system PATH mutation occur. CI writes only its ephemeral GITHUB_PATH.

## Frozen Linux isolation
Qt multimedia's FFmpeg libraries and the media toolchain must not shadow each other. Media binaries and their linked libraries are isolated under `media/bin` and `media/lib`; external subprocess library paths are restored. The executor's stdlib TLS policy adjunct is bundled if present, preserving rather than disabling its certificate policy.

## Distribution status
These are personal/developer builds, not a public release or licensing certification. Third-party notices remain under `packaging/`; the build records FFmpeg configuration, source hashes, dependency lock hash and whether its working tree was dirty. Public redistribution requires exact applicable license texts and source obligations to be completed first.
