"""Reference FFmpeg composition for P02, with actual output validation."""
from dataclasses import asdict, dataclass
from fractions import Fraction
from pathlib import Path
from threading import Event
from typing import Callable
import json
import math
import os
import shutil
import struct
import subprocess
import tempfile
import time
import zlib

from .subtitles import load_srt
from .tools import locate_tool


class MediaError(RuntimeError):
    pass


@dataclass(frozen=True)
class MediaInfo:
    width: int
    height: int
    duration: float
    fps: str
    video_codec: str
    audio_codec: str | None
    # Container Display Matrix rotation applied automatically by FFmpeg input.
    # Optional trailing field keeps existing six-argument fixture calls valid.
    display_rotation: float = 0.0


@dataclass(frozen=True)
class RenderSpec:
    title: str = "Fonesi Edit • Kiểm chứng P02"
    font_size: int = 28
    x: float = 0.05
    y: float = 0.08
    speed_px_s: float = 0
    mask: bool = True
    subtitles: Path | None = None
    logo: Path | None = None
    font: Path | None = None

    def __post_init__(self):
        numbers = (self.x, self.y, self.speed_px_s)
        if not all(math.isfinite(n) for n in numbers):
            raise ValueError("Transform values must be finite")
        if not 0 <= self.x <= 1 or not 0 <= self.y <= 1:
            raise ValueError("Normalized position must be in [0, 1]")
        if not 8 <= self.font_size <= 200 or abs(self.speed_px_s) > 2000:
            raise ValueError("Prototype font/speed outside allowed range")


def run_checked(args: list[str], *, cwd: Path | None = None, timeout: float = 30) -> subprocess.CompletedProcess:
    if args[0] in {"ffmpeg", "ffprobe"}:
        executable = locate_tool(args[0])
        if not executable:
            raise MediaError(f"Thiếu công cụ: {args[0]}")
        args = [executable, *args[1:]]
    try:
        completed = subprocess.run(args, cwd=cwd, capture_output=True, text=True,
                                   errors="replace", timeout=timeout)
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise MediaError(f"{Path(args[0]).name}: {type(exc).__name__}") from None
    if completed.returncode:
        raise MediaError(f"{Path(args[0]).name} exit {completed.returncode}: {completed.stderr[-1800:]}")
    return completed


def probe(path: Path, ffprobe: str = "ffprobe") -> MediaInfo:
    path = path.resolve(strict=True)
    data = json.loads(run_checked([ffprobe, "-v", "error", "-show_streams", "-show_format",
                                   "-of", "json", str(path)]).stdout)
    videos = [s for s in data["streams"] if s["codec_type"] == "video"]
    if not videos:
        raise MediaError("Không có video track")
    video = videos[0]
    audio = next((s for s in data["streams"] if s["codec_type"] == "audio"), None)
    duration = float(data.get("format", {}).get("duration", video.get("duration", 0)))
    if not math.isfinite(duration) or duration <= 0:
        raise MediaError("Thời lượng không hợp lệ")
    rate = video.get("avg_frame_rate", "0/0")
    if rate in {"0/0", "0/1"}:
        rate = video.get("r_frame_rate", "25/1")
    if Fraction(rate) <= 0:
        raise MediaError("FPS không hợp lệ")
    # FFmpeg autorotates decoded frames before passing them into filter graphs.
    # Keep encoded dimensions, but report Display Matrix rotation separately so
    # callers using source-normalized coordinates can transform them reliably.
    matrix = next((entry for entry in video.get("side_data_list", [])
                   if isinstance(entry, dict)
                   and entry.get("side_data_type") == "Display Matrix"
                   and "rotation" in entry), None)
    rotation_value = (matrix["rotation"] if matrix is not None else
                      video.get("tags", {}).get("rotate", 0))
    try:
        rotation = float(rotation_value)
    except (ValueError, TypeError, OverflowError):
        raise MediaError("Invalid video display rotation metadata") from None
    if not math.isfinite(rotation):
        raise MediaError("Invalid video display rotation metadata")
    return MediaInfo(int(video["width"]), int(video["height"]), duration, rate,
                     video["codec_name"], audio["codec_name"] if audio else None,
                     rotation)


def find_font() -> Path:
    candidates = [Path("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"),
                  Path(os.environ.get("WINDIR", "C:/Windows")) / "Fonts/arial.ttf",
                  Path("/System/Library/Fonts/Supplemental/Arial.ttf")]
    for path in candidates:
        if path.is_file():
            return path
    raise MediaError("Chưa có font phù hợp; truyền font TTF bằng --font")


def _publish(staged: Path, destination: Path):
    # Atomic no-replace: a competing writer cannot cause source/output overwrite.
    try:
        if os.name=='nt':os.rename(staged,destination)  # Windows rename is atomic and refuses existing destinations, including exFAT.
        else:os.link(staged, destination)
    except FileExistsError:
        raise FileExistsError(f"Đầu ra đã tồn tại: {destination}") from None
    except OSError as exc:
        raise MediaError(f"Filesystem chưa hỗ trợ publish no-replace: {type(exc).__name__}") from None


def render(source: Path, destination: Path, spec: RenderSpec,
           progress: Callable[[float], None] | None = None, cancel: Event | None = None,
           ffmpeg: str = "ffmpeg", ffprobe: str = "ffprobe") -> dict:
    source = source.resolve(strict=True)
    destination = destination.resolve()
    if destination.exists() or source == destination:
        raise FileExistsError("Giữ nguyên nguồn và không ghi đè đầu ra có sẵn")
    if destination.suffix.lower() != ".mp4":
        raise ValueError("P02 chỉ xuất MP4")
    info = probe(source, ffprobe)
    if ffmpeg == "ffmpeg":
        ffmpeg = locate_tool("ffmpeg")
        if not ffmpeg:
            raise MediaError("Thiếu FFmpeg")
    if info.width < 64 or info.height < 64:
        raise MediaError("P02 cần khung hình ít nhất 64x64")
    if spec.subtitles:
        load_srt(spec.subtitles)  # Fail before rendering malformed cues.
    destination.parent.mkdir(parents=True, exist_ok=True)
    started = time.monotonic()
    with tempfile.TemporaryDirectory(prefix=".fonesi-p02-", dir=destination.parent) as temp:
        stage = Path(temp)
        font = spec.font or find_font()
        shutil.copyfile(font, stage / "font.ttf")
        (stage / "title.txt").write_text(spec.title, encoding="utf-8")
        inputs = ["-i", str(source)]
        if spec.logo:
            shutil.copyfile(spec.logo, stage / "logo.png")
            inputs += ["-i", "logo.png"]
        graph = []
        current = "0:v:0"
        if spec.mask:
            width, height = max(16, info.width * 4 // 5), max(16, info.height // 9)
            x, y = (info.width - width) // 2, info.height * 3 // 4
            y = min(y, info.height - height)
            graph += [f"[{current}]split=2[base][masksrc]",
                      f"[masksrc]crop={width}:{height}:{x}:{y},boxblur=8:1[blur]",
                      f"[base][blur]overlay={x}:{y}[masked]"]
            current = "masked"
        if spec.logo:
            graph += ["[1:v]scale=64:64[logo]", f"[{current}][logo]overlay=W-w-12:12[branded]"]
            current = "branded"
        xexpr = f"min(max(0,{spec.x:.6f}*w+{spec.speed_px_s:.6f}*t),max(0,w-text_w))"
        graph += [f"[{current}]drawtext=fontfile=font.ttf:textfile=title.txt:expansion=none:"
                  f"fontsize={spec.font_size}:fontcolor=white:borderw=2:bordercolor=black:"
                  f"x='{xexpr}':y='min({spec.y:.6f}*h,max(0,h-text_h))'[titled]"]
        current = "titled"
        if spec.subtitles:
            shutil.copyfile(spec.subtitles, stage / "captions.srt")
            graph += [f"[{current}]subtitles=filename=captions.srt:fontsdir=.:"
                      "force_style='FontName=DejaVu Sans,FontSize=22,Outline=1,MarginV=18'[captioned]"]
            current = "captioned"
        graph += [f"[{current}]scale=trunc(iw/2)*2:trunc(ih/2)*2,format=yuv420p[outv]"]
        command = [ffmpeg, "-hide_banner", "-nostdin", "-n", *inputs,
                   "-filter_complex_threads", "1", "-filter_complex", ";".join(graph),
                   "-map", "[outv]", "-map", "0:a:0?", "-c:v", "libx264", "-threads", "2",
                   "-preset", "veryfast", "-crf", "22", "-c:a", "aac", "-movflags", "+faststart",
                   "-progress", "pipe:1", "-nostats", "output.mp4"]
        with (stage / "progress.txt").open("w+", encoding="utf-8") as log, (stage / "stderr.txt").open("w+", encoding="utf-8") as errors:
            process = subprocess.Popen(command, cwd=stage, stdout=log, stderr=errors)
            try:
                while process.poll() is None:
                    if cancel and cancel.is_set():
                        raise MediaError("Đã hủy render")
                    if time.monotonic() - started > max(120, info.duration * 30):
                        raise MediaError("Render quá thời gian giới hạn P02")
                    if progress:
                        log.flush()
                        text = (stage / "progress.txt").read_text(encoding="utf-8")
                        times = [int(line.split("=", 1)[1]) for line in text.splitlines() if line.startswith("out_time_us=") and line[12:].lstrip("-").isdigit()]
                        if times:
                            progress(min(0.99, max(0, times[-1] / 1_000_000 / info.duration)))
                    time.sleep(0.1)
                if process.returncode:
                    errors.seek(0)
                    raise MediaError(f"FFmpeg exit {process.returncode}: {errors.read()[-2000:]}")
            finally:
                if process.poll() is None:
                    process.terminate()
                    try:
                        process.wait(timeout=3)
                    except subprocess.TimeoutExpired:
                        process.kill()
                        process.wait()
        staged = stage / "output.mp4"
        output = probe(staged, ffprobe)
        tolerance = max(0.15, 2 / float(Fraction(info.fps)))
        if abs(output.duration - info.duration) > tolerance:
            raise MediaError("Thời lượng output không khớp input")
        if info.audio_codec and not output.audio_codec:
            raise MediaError("Mất audio track")
        run_checked([ffmpeg, "-v", "error", "-nostdin", "-i", str(staged), "-f", "null", "-"], timeout=max(30, info.duration * 5))
        _publish(staged, destination)
    if progress:
        progress(1.0)
    return {"output": str(destination), "media": asdict(output), "elapsed_seconds": round(time.monotonic() - started, 3),
            "validated": True, "validation": ["probe", "duration", "audio-preserved", "full-decode"]}


def extract_frame(source: Path, destination: Path, second: float = 0, ffmpeg: str = "ffmpeg"):
    if second < 0 or not math.isfinite(second) or destination.exists():
        raise ValueError("Invalid timestamp or existing frame output")
    destination.parent.mkdir(parents=True, exist_ok=True)
    run_checked([ffmpeg, "-v", "error", "-nostdin", "-n", "-ss", str(second), "-i", str(source.resolve()),
                 "-frames:v", "1", "-threads", "1", str(destination)])


def create_fixture(folder: Path, duration: float = 3, portrait: bool = False) -> dict[str, Path]:
    if not 0.5 <= duration <= 10:
        raise ValueError("Fixture duration must be 0.5–10 seconds")
    folder.mkdir(parents=True, exist_ok=True)
    source, sub, logo = folder / "nguồn 视频.mp4", folder / "phụ đề.srt", folder / "logo.png"
    if any(p.exists() for p in (source, sub, logo)):
        raise FileExistsError("Fixture folder must not contain existing fixture files")
    size = "360x640" if portrait else "640x360"
    run_checked(["ffmpeg", "-v", "error", "-nostdin", "-n", "-f", "lavfi", "-i", f"testsrc2=size={size}:rate=25",
                 "-f", "lavfi", "-i", "sine=frequency=440:sample_rate=48000", "-t", str(duration),
                 "-c:v", "libx264", "-threads", "2", "-pix_fmt", "yuv420p", "-c:a", "aac", str(source)])
    # Generated RGBA fixture: transparent border, visible semi-transparent center.
    # Drawing onto a fully transparent FFmpeg color source can retain alpha=0.
    def chunk(kind, payload):
        return struct.pack(">I", len(payload)) + kind + payload + struct.pack(">I", zlib.crc32(kind + payload) & 0xffffffff)
    pixels = b"".join(b"\x00" + b"".join(bytes((255, 200, 32, 220 if 8 <= x < 56 and 8 <= y < 56 else 0))
                    for x in range(64)) for y in range(64))
    logo.write_bytes(b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", struct.pack(">IIBBBBB", 64, 64, 8, 6, 0, 0, 0))
                     + chunk(b"IDAT", zlib.compress(pixels)) + chunk(b"IEND", b""))
    # Keep cue within even the smallest supported fixture.
    sub.write_text("1\n00:00:00,100 --> 00:00:00,400\nKiểm chứng phụ đề tiếng Việt\n", encoding="utf-8")
    return {"source": source, "subtitles": sub, "logo": logo}
