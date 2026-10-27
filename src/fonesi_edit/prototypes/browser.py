"""Open authentic Chrome profiles; does not pretend session handoff is verified."""
from dataclasses import dataclass
from pathlib import Path
import json
import subprocess
from uuid import uuid4

from .tools import check_tool, find_chrome

PLATFORMS = {
    "YouTube": "https://accounts.google.com/ServiceLogin?service=youtube",
    "Facebook": "https://www.facebook.com/login/",
    "TikTok": "https://www.tiktok.com/login",
    "Instagram": "https://www.instagram.com/accounts/login/",
    "Threads": "https://www.threads.com/",
    "X": "https://x.com/i/flow/login",
    "Bilibili": "https://passport.bilibili.com/login",
    "Douyin": "https://www.douyin.com/",
    "Xiaohongshu": "https://www.xiaohongshu.com/explore",
    "Kuaishou": "https://www.kuaishou.com/",
}


@dataclass(frozen=True)
class Profile:
    id: str
    label: str
    directory: Path


def create_profile(root: Path, label: str) -> Profile:
    if not label.strip() or len(label) > 80:
        raise ValueError("Tên hồ sơ cần 1–80 ký tự")
    profile = Profile(uuid4().hex, label.strip(), Path())
    directory = root.resolve() / profile.id
    directory.mkdir(parents=True, exist_ok=False)
    (directory / "fonesi-profile.json").write_text(
        json.dumps({"id": profile.id, "label": profile.label, "owner": "fonesi-p02"}, ensure_ascii=False), encoding="utf-8")
    return Profile(profile.id, profile.label, directory)


def list_profiles(root: Path) -> list[Profile]:
    if not root.is_dir():
        return []
    profiles = []
    for file in sorted(root.glob("*/fonesi-profile.json")):
        try:
            data = json.loads(file.read_text(encoding="utf-8"))
            if data.get("owner") == "fonesi-p02" and data["id"] == file.parent.name:
                profiles.append(Profile(data["id"], data["label"], file.parent.resolve()))
        except (OSError, ValueError, KeyError):
            continue
    return profiles


def chrome_command(profile: Profile, platform: str, chrome: str | None = None) -> list[str]:
    if platform not in PLATFORMS:
        raise ValueError("Nền tảng không được hỗ trợ trong prototype")
    status = check_tool("Google Chrome", chrome or find_chrome())
    if status.status != "ready":
        raise RuntimeError("Chưa có Google Chrome chính thức dùng được; không thay bằng Chromium")
    if not (profile.directory / "fonesi-profile.json").is_file():
        raise ValueError("Không xác nhận hồ sơ do app quản lý")
    return [status.path, f"--user-data-dir={profile.directory}", "--new-window", PLATFORMS[platform]]


def open_login(profile: Profile, platform: str, chrome: str | None = None):
    # Normal visible Chrome; no remote debugging or extraction of private cookie databases.
    return subprocess.Popen(chrome_command(profile, platform, chrome))
