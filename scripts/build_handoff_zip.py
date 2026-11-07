#!/usr/bin/env python3
"""Build a complete Fonesi Edit handoff ZIP including Git history.

The package contains the checked-out repository, its .git directory, a precise
handoff checkpoint and a continuation prompt. It refuses to package Git config
that appears to contain credentials.
"""
from __future__ import annotations

import argparse
import hashlib
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import zipfile


REPOSITORY = "danhgold7979-cyber/fonesi-edit"
BRANCH = "develop/fonesi-full"
PHASE = "P04 / 12 — Workspace, Preview và Timeline"
PROGRESS = "56%"
CREDENTIAL_MARKERS = (
    "x-access-token",
    "github_pat_",
    "ghp_",
    "authorization:",
    "oauth2:",
)


def git(root: Path, *args: str) -> str:
    return subprocess.check_output(
        ["git", *args], cwd=root, text=True, encoding="utf-8"
    ).strip()


def assert_safe_git_config(root: Path) -> None:
    config = git(root, "config", "--local", "--list", "--show-origin").casefold()
    if any(marker in config for marker in CREDENTIAL_MARKERS):
        raise RuntimeError("Credential-like data found in local Git config")


def continuation_prompt(head: str) -> str:
    return f"""# PROMPT TIẾP TỤC FONESI EDIT

Tiếp tục triển khai dự án Fonesi Edit theo đúng source, Git history, kế hoạch và
checkpoint trong gói này.

- Repository bắt buộc: `{REPOSITORY}`
- Nhánh tích hợp duy nhất: `{BRANCH}`
- HEAD trong gói: `{head}`
- Phase hiện tại: **{PHASE}**
- Tiến độ code ước lượng theo checkpoint: **{PROGRESS}**
- Không tự merge vào `main`, không force-push và không tạo ứng dụng/nhánh phase riêng.

Thực hiện ngay khi người dùng nói “Tiếp tục”:

1. Đọc `AGENTS.md`, `README.md`, `docs/IMPLEMENTATION_PLAN.md`,
   `docs/PRODUCT_REQUIREMENTS.md`, `docs/CURRENT_STATUS.md`,
   `docs/phases/P04_PLAN.md`, `docs/phases/P04_RESULTS.md` và code/test liên quan.
2. Xác minh trực tiếp repository, HEAD, pull request và GitHub Actions Linux/Windows
   của đúng commit; không mặc định trạng thái CI trong gói vẫn mới nhất.
3. Nếu CI lỗi, sửa nguyên nhân thật; không bỏ assertion hoặc test để làm xanh giả.
4. Tiếp tục task P04 chưa hoàn thành theo dependency: hoàn thiện P04-05, sau đó
   P04-06, P04-07 và P04-08. Giữ rõ các cổng Windows/Chrome/GPU/media thật chưa đạt.
5. Viết test, chạy kiểm tra phù hợp, cập nhật tài liệu bằng bằng chứng thật,
   commit/push lên `{BRANCH}` và không đổi `main`.
6. Cuối lượt, tạo lại `Tải Zip.zip` chứa toàn bộ source, `.git`, lịch sử commit,
   plans, README, tests, checkpoint và prompt tiếp tục.

Không hỏi lại khi có thể tiến hành an toàn.
"""


def checkpoint(root: Path, head: str, branch: str) -> str:
    recent = git(
        root,
        "log",
        "-n",
        "30",
        "--date=iso-strict",
        "--pretty=format:%H | %ad | %s",
    )
    return f"""# FONESI EDIT — HANDOFF CHECKPOINT

- Repository: `{REPOSITORY}`
- Branch: `{branch or BRANCH}`
- Packaged HEAD: `{head}`
- Phase: {PHASE}
- Code progress estimate: {PROGRESS} — không phải tỷ lệ nghiệm thu
- Release branch `main`: không được tự merge
- Nội dung gói: source, `.git`, lịch sử commit, tests, plans, README,
  checkpoint và prompt tiếp tục.

## Việc tiếp theo

1. Xác minh CI đúng HEAD đóng gói và sửa toàn bộ lỗi Linux/Windows còn lại.
2. Hoàn thiện P04-05; sau đó P04-06, P04-07 và P04-08 theo master plan.
3. Không tuyên bố phase hoàn thành khi tiêu chí bắt buộc hoặc cổng ngoài chưa đạt.

## 30 commit gần nhất

```text
{recent}
```
"""


def build(output: Path) -> tuple[Path, str]:
    root = Path(__file__).resolve().parents[1]
    if not (root / ".git").is_dir():
        raise RuntimeError("Repository .git directory is required")
    assert_safe_git_config(root)

    head = git(root, "rev-parse", "HEAD")
    branch = git(root, "branch", "--show-current")
    output = output.expanduser().resolve()
    output.parent.mkdir(parents=True, exist_ok=True)

    with tempfile.TemporaryDirectory(prefix="fonesi-edit-handoff-") as temp_name:
        stage_root = Path(temp_name)
        stage = stage_root / "fonesi-edit"
        shutil.copytree(
            root,
            stage,
            symlinks=True,
            ignore=shutil.ignore_patterns(
                "__pycache__",
                ".pytest_cache",
                ".mypy_cache",
                ".ruff_cache",
                "*.pyc",
                output.name,
            ),
        )
        (stage / "NEXT_PROMPT.md").write_text(
            continuation_prompt(head), encoding="utf-8"
        )
        (stage / "HANDOFF_STATUS.md").write_text(
            checkpoint(root, head, branch), encoding="utf-8"
        )

        temporary_output = output.with_suffix(output.suffix + ".partial")
        if temporary_output.exists():
            temporary_output.unlink()
        with zipfile.ZipFile(
            temporary_output,
            "w",
            compression=zipfile.ZIP_DEFLATED,
            compresslevel=6,
            allowZip64=True,
        ) as archive:
            for path in sorted(stage.rglob("*")):
                if path.is_dir():
                    continue
                archive.write(path, path.relative_to(stage_root))
        os.replace(temporary_output, output)

    digest = hashlib.sha256(output.read_bytes()).hexdigest()
    checksum = output.with_name(output.name + ".sha256.txt")
    checksum.write_text(f"{digest}  {output.name}\n", encoding="utf-8")
    return output, digest


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    output, digest = build(args.output)
    print(f"Created: {output}")
    print(f"Size: {output.stat().st_size} bytes")
    print(f"SHA256: {digest}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
