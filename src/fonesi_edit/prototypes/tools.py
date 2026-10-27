"""Read-only discovery. No hidden installs or browser credential access."""
from dataclasses import asdict, dataclass
from pathlib import Path
import os
import shutil
import subprocess
import sys

_OVERRIDES={}

def configure_tools(overrides):
    _OVERRIDES.clear()
    _OVERRIDES.update({name:str(path) for name,path in overrides.items() if name in {'ffmpeg','ffprobe','Google Chrome','node'}})


@dataclass(frozen=True)
class ToolStatus:
    name: str
    path: str | None
    status: str
    version: str = ""
    detail: str = ""

    def to_dict(self):
        return asdict(self)


def find_chrome() -> str | None:
    candidates = [shutil.which("google-chrome"), shutil.which("google-chrome-stable")]
    for variable in ("LOCALAPPDATA", "PROGRAMFILES", "PROGRAMFILES(X86)"):
        if os.environ.get(variable):
            candidates.append(str(Path(os.environ[variable]) / "Google/Chrome/Application/chrome.exe"))
    candidates.append("/Applications/Google Chrome.app/Contents/MacOS/Google Chrome")
    return next((str(Path(p).resolve()) for p in candidates if p and Path(p).is_file()), None)


def check_tool(name: str, path: str | None) -> ToolStatus:
    if not path or not Path(path).is_file():
        return ToolStatus(name, path, "missing", detail="Chưa tìm thấy công cụ")
    try:
        if name == "Google Chrome" and os.name == "nt":
            # chrome.exe --version can launch a browser instead of returning text on Windows.
            # Read PE version resources without opening an existing user's browser profile.
            import ctypes
            from ctypes import wintypes
            version = ctypes.WinDLL("version", use_last_error=True)
            size_fn = version.GetFileVersionInfoSizeW
            size_fn.argtypes = [wintypes.LPCWSTR, ctypes.POINTER(wintypes.DWORD)]
            size_fn.restype = wintypes.DWORD
            ignored = wintypes.DWORD()
            size = size_fn(path, ctypes.byref(ignored))
            if not size:
                raise OSError("No version resource")
            buffer = ctypes.create_string_buffer(size)
            info_fn = version.GetFileVersionInfoW
            info_fn.argtypes = [wintypes.LPCWSTR, wintypes.DWORD, wintypes.DWORD, ctypes.c_void_p]
            if not info_fn(path, 0, size, buffer):
                raise OSError("Cannot read version resource")
            query = version.VerQueryValueW
            query.argtypes = [ctypes.c_void_p, wintypes.LPCWSTR, ctypes.POINTER(ctypes.c_void_p), ctypes.POINTER(wintypes.UINT)]
            address, length = ctypes.c_void_p(), wintypes.UINT()
            translation = "040904b0"
            if query(buffer, "\\VarFileInfo\\Translation", ctypes.byref(address), ctypes.byref(length)) and length.value >= 4:
                pair = ctypes.cast(address, ctypes.POINTER(wintypes.WORD))
                translation = f"{pair[0]:04x}{pair[1]:04x}"
            values = []
            for field in ("ProductName", "ProductVersion"):
                if not query(buffer, f"\\StringFileInfo\\{translation}\\{field}", ctypes.byref(address), ctypes.byref(length)):
                    raise OSError("Missing product metadata")
                values.append(ctypes.wstring_at(address.value))
            if values[0] != "Google Chrome":
                return ToolStatus(name, path, "incompatible", " ".join(values), "Không xác nhận Google Chrome")
            return ToolStatus(name, str(Path(path).resolve()), "ready", " ".join(values), "PE metadata; chữ ký/phiên Windows cần nghiệm thu riêng")
        flag = "-version" if name in {"ffmpeg", "ffprobe"} else "--version"
        completed = subprocess.run([path, flag], capture_output=True, text=True,
                                   errors="replace", timeout=10)
        lines = (completed.stdout + completed.stderr).strip().splitlines()
        first = lines[0] if lines else ""
        if completed.returncode:
            return ToolStatus(name, path, "error", first[:240], f"Exit {completed.returncode}")
        if name == "Google Chrome" and not first.startswith("Google Chrome "):
            return ToolStatus(name, path, "incompatible", first[:240], "Không xác nhận Google Chrome chính thức")
        if name=='node':
            import re
            match=re.match(r'v(\d+)',first)
            if not match or int(match[1])<20:return ToolStatus(name,path,'incompatible',first,'YouTube JS runtime cần Node 20 trở lên')
        return ToolStatus(name, str(Path(path).resolve()), "ready", first[:240])
    except (OSError, subprocess.TimeoutExpired) as exc:
        return ToolStatus(name, path, "error", detail=type(exc).__name__)


def locate_tool(name: str) -> str | None:
    if name in _OVERRIDES:return _OVERRIDES[name]
    scripts = Path(sys.executable).parent
    if name == "Google Chrome":
        return find_chrome()
    bundled = Path(getattr(sys, "_MEIPASS", scripts)) / "tools" / (name + (".exe" if os.name == "nt" else ""))
    local = scripts / (name + (".exe" if os.name == "nt" else ""))
    return str(bundled) if bundled.is_file() else str(local) if local.is_file() else shutil.which(name)


def scan_tools(overrides: dict[str, str] | None = None) -> list[ToolStatus]:
    overrides = overrides or {}
    result = []
    for name in ("ffmpeg", "ffprobe", "yt-dlp", "gallery-dl", "Google Chrome", "node"):
        if name in overrides:
            path = overrides[name]  # An explicit broken override must not silently fall back.
        else:
            path = locate_tool(name)
        result.append(check_tool(name, path))
    return result
