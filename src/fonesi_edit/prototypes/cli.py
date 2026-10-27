"""Developer proof commands. Unsupported product features are not simulated."""
from argparse import ArgumentParser
from dataclasses import asdict
from pathlib import Path
import json
import subprocess
import sys
from urllib.parse import urlsplit

from .media import RenderSpec, create_fixture, extract_frame, probe, render
from .subtitles import dump_srt, load_srt
from .tools import scan_tools


def main(argv=None) -> int:
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8")
    parser = ArgumentParser(description="Fonesi P02 prototype — chưa phải bản sản phẩm")
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("scan", help="Quét và chạy kiểm tra version công cụ")
    info = commands.add_parser("probe")
    info.add_argument("source", type=Path)
    demo = commands.add_parser("demo", help="Tạo fixture synthetic và render thật")
    demo.add_argument("folder", type=Path)
    demo.add_argument("--portrait", action="store_true")
    export = commands.add_parser("render")
    export.add_argument("source", type=Path)
    export.add_argument("output", type=Path)
    export.add_argument("--subtitles", type=Path)
    export.add_argument("--logo", type=Path)
    export.add_argument("--font", type=Path)
    export.add_argument("--title", default="Fonesi Edit • P02")
    export.add_argument("--font-size", type=int, default=28)
    export.add_argument("--x", type=float, default=0.05)
    export.add_argument("--y", type=float, default=0.08)
    export.add_argument("--speed", type=float, default=0)
    metadata = commands.add_parser("metadata", help="Live yt-dlp public metadata; không đọc cookie")
    metadata.add_argument("url")
    translated = commands.add_parser("translate", help="API thật khi cấu hình key; không mock")
    translated.add_argument("source", type=Path)
    translated.add_argument("output", type=Path)
    translated.add_argument("--source-language", default="zh")
    translated.add_argument("--target-language", default="vi")
    ui = commands.add_parser("ui")
    ui.add_argument("--smoke", action="store_true")
    ui.add_argument("--screenshot", type=Path)
    ui.add_argument("--source", type=Path)
    args = parser.parse_args(argv)
    try:
        if args.command == "scan":
            data = [tool.to_dict() for tool in scan_tools()]
        elif args.command == "probe":
            data = asdict(probe(args.source))
        elif args.command == "demo":
            files = create_fixture(args.folder, portrait=args.portrait)
            output = args.folder / "kết quả.mp4"
            data = render(files["source"], output, RenderSpec(subtitles=files["subtitles"], logo=files["logo"], speed_px_s=20))
            extract_frame(output, args.folder / "frame.png", 0.2)
            data["source_kind"] = "synthetic lavfi, not a live platform download"
            data["source"] = str(files["source"].resolve())
            (args.folder / "evidence.json").write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
        elif args.command == "render":
            data = render(args.source, args.output, RenderSpec(title=args.title, font_size=args.font_size,
                          x=args.x, y=args.y, speed_px_s=args.speed, subtitles=args.subtitles, logo=args.logo, font=args.font))
        elif args.command == "metadata":
            url = urlsplit(args.url)
            if url.scheme not in {"https", "http"} or not url.hostname or url.username or url.password:
                raise ValueError("Chỉ nhận URL HTTP(S) không chứa thông tin đăng nhập")
            result = subprocess.run([sys.executable, "-m", "yt_dlp", "--skip-download", "--dump-single-json",
                "--no-playlist", "--socket-timeout", "10", "--retries", "0", "--extractor-retries", "0", args.url],
                capture_output=True, text=True, errors="replace", timeout=50)
            if result.returncode:
                raise RuntimeError(f"yt-dlp exit {result.returncode}: {result.stderr[-1600:]}")
            raw = json.loads(result.stdout)
            data = {key: raw.get(key) for key in ("id", "title", "duration", "extractor", "webpage_url")}
        elif args.command == "translate":
            from .translation import translate
            if args.output.exists():
                raise FileExistsError("Không ghi đè sub có sẵn")
            cues = translate(load_srt(args.source), args.target_language, args.source_language)
            with args.output.open("x", encoding="utf-8") as stream:
                stream.write(dump_srt(cues))
            data = {"output": str(args.output), "cues": len(cues), "live_translation": True}
        else:
            from .gui import launch
            return launch(smoke=args.smoke, screenshot=args.screenshot, source=args.source)
        print(json.dumps(data, ensure_ascii=False, indent=2))
        return 0
    except (OSError, ValueError, RuntimeError, subprocess.TimeoutExpired) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
