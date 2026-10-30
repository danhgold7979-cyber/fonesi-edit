"""Run owned frozen proof with no media PATH; inspect fixed startup evidence."""

import json
import os
import sys
from pathlib import Path

from fonesi_edit.process import run_bounded

executable = Path(sys.argv[1]).resolve(strict=True)
# The frozen app must start without discovering FFmpeg/Python through PATH.
old_path = os.environ.get("PATH")
os.environ["PATH"] = ""
try:
    result = run_bounded([str(executable), "--smoke-test"], timeout=60, limit=16384)
finally:
    if old_path is None:
        os.environ.pop("PATH", None)
    else:
        os.environ["PATH"] = old_path
if result.status != "OK":
    raise SystemExit("FROZEN_STARTUP_" + result.status)
lines = result.stdout.decode("utf-8").splitlines()
if len(lines) != 1:
    raise SystemExit("UNEXPECTED_STARTUP_OUTPUT")
evidence = json.loads(lines[0])
expected = {
    "main_visible",
    "subtitle_visible",
    "batch_visible",
    "empty_export_disabled",
    "empty_batch_disabled",
    "workers_idle",
}
if (
    set(evidence) != {"kind", "frozen", "checks", "passed"}
    or evidence["kind"] != "fonesi-startup-smoke"
    or evidence["frozen"] is not True
    or evidence["passed"] is not True
    or set(evidence["checks"]) != expected
    or any(value is not True for value in evidence["checks"].values())
):
    raise SystemExit("INVALID_FROZEN_STARTUP_EVIDENCE")
print(json.dumps(evidence, sort_keys=True))
print("PASS: frozen startup only; no installer, media or user-machine acceptance")
