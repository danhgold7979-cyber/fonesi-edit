"""Check phase references before work; no application readiness is implied."""
from pathlib import Path
import re


REQUIREMENT_PATTERN = re.compile(
    r"^\|\s*((?:SRC|SUB|ED|BAT|AUD|MAT|AUTO|OPS|WIN|TOL|AUTH)-\d+)\s*\|"
)
TASK_PATTERN = re.compile(r"\bP\d{2}-\d{2}\b")
PLACEHOLDERS = {"", "-", "—", "TBD", "TODO", "N/A"}


def validate_traceability(content: str, known_tasks, expected_count=95):
    """Validate requirement coverage structure, not feature implementation."""
    errors = []
    requirements = []
    for line in content.splitlines():
        match = REQUIREMENT_PATTERN.match(line)
        if not match:
            continue
        identifier = match.group(1)
        requirements.append(identifier)
        cells = [part.strip() for part in line.strip().strip("|").split("|")]
        if len(cells) != 5:
            errors.append(f"{identifier}: expected five columns (ID/requirement/source/task/acceptance)")
            continue
        for field, value in zip(("ID", "requirement", "source", "task", "acceptance"), cells):
            if value in PLACEHOLDERS:
                errors.append(f"{identifier}: missing {field}")
        mappings = TASK_PATTERN.findall(cells[3])
        if not mappings:
            errors.append(f"{identifier}: no phase task mapping")
        for task in mappings:
            if task not in known_tasks:
                errors.append(f"{identifier}: unknown phase task {task}")
    if expected_count is not None and len(requirements) != expected_count:
        errors.append(f"Expected {expected_count} requirement groups, found {len(requirements)}")
    if len(requirements) != len(set(requirements)):
        errors.append("Duplicate requirement ID")
    return requirements, errors


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    files = [root / "README.md", *sorted((root / "docs").rglob("*.md"))]
    plan = (root / "docs/IMPLEMENTATION_PLAN.md").read_text(encoding="utf-8")
    tasks = re.findall(r"^- \[[ x]\] (P\d{2}-\d{2}):", plan, re.M)
    phases = re.findall(r"^## \d+\. (P\d{2}) —", plan, re.M)
    errors = []
    if len(tasks) != len(set(tasks)):
        errors.append("Duplicate task ID")
    if phases != [f"P{i:02}" for i in range(1, 13)]:
        errors.append("Master plan must define P01 through P12")
    for file in files:
        content = file.read_text(encoding="utf-8")
        if content.count("```") % 2:
            errors.append(f"Unclosed fence: {file.relative_to(root)}")
        for link in re.findall(r"\]\(([^)]+)\)", content):
            if "://" not in link and not (file.parent / link.split("#", 1)[0]).exists():
                errors.append(f"Broken link: {file.relative_to(root)} -> {link}")
        unknown = set(re.findall(r"\bP\d{2}-\d{2}\b", content)) - set(tasks)
        if unknown:
            errors.append(f"Unknown tasks: {file.name}: {sorted(unknown)}")
    trace = (root / "docs/REQUIREMENTS_TRACEABILITY.md").read_text(encoding="utf-8")
    requirements, trace_errors = validate_traceability(trace, set(tasks))
    errors.extend(trace_errors)
    print(f"{len(phases)} phases; {len(tasks)} tasks; {len(requirements)} requirement groups; {len(files)} documents")
    if errors:
        print("\n".join(errors))
        return 1
    print("Plan references and local document links: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
