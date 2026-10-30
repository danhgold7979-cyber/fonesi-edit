"""Validate current rebuild task traceability, not product acceptance."""

import re
from pathlib import Path

root = Path(__file__).resolve().parents[1]
master = (root / "docs/IMPLEMENTATION_PLAN.md").read_text(encoding="utf-8")
trace = (root / "docs/REQUIREMENTS_TRACEABILITY.md").read_text(encoding="utf-8")
tasks = re.findall(r"^- \[[ x]\] (P\d{2}-\d{2}):", master, re.MULTILINE)
errors = []
if len(tasks) != len(set(tasks)) or len(tasks) != 94:
    errors.append("Master task set changed without reviewed migration")
for phase in range(1, 13):
    prefix = f"P{phase:02}"
    path = root / f"docs/phases/{prefix}_PLAN.md"
    current = path.read_text(encoding="utf-8").split(
        "## Hồ sơ thực hiện trước rebuild"
    )[0]
    actual = re.findall(r"^### (P\d{2}-\d{2})$", current, re.MULTILINE)
    expected = [t for t in tasks if t.startswith(prefix + "-")]
    if actual != expected:
        errors.append(f"{prefix}: missing, duplicate or out-of-order task sections")
requirements = re.findall(
    r"^\| ((?:SRC|SUB|ED|BAT|AUD|MAT|AUTO|OPS|WIN|TOL|AUTH)-\d+) \|",
    trace,
    re.MULTILINE,
)
if len(requirements) != 95 or len(set(requirements)) != 95:
    errors.append("Expected 95 unique requirement groups")
for line in trace.splitlines():
    if re.match(r"^\| (SRC|SUB|ED|BAT|AUD|MAT|AUTO|OPS|WIN|TOL|AUTH)-\d+ \|", line):
        refs = re.findall(r"P\d{2}-\d{2}", line)
        if not refs or any(t not in tasks for t in refs):
            errors.append("Invalid requirement task mapping")
print(f"12 phases / {len(tasks)} tasks / {len(requirements)} groups; structure only")
if errors:
    raise SystemExit("\n".join(errors))
print("PASS; no runtime or feature acceptance implied")
