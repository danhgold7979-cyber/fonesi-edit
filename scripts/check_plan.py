"""Check phase references before work; no application readiness is implied."""
from pathlib import Path
import re


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
    requirements = re.findall(r"^\| ((?:SRC|SUB|ED|BAT|AUD|MAT|AUTO|OPS|WIN|TOL|AUTH)-\d+) \|", trace, re.M)
    if len(requirements) != len(set(requirements)):
        errors.append("Duplicate requirement ID")
    print(f"{len(phases)} phases; {len(tasks)} tasks; {len(requirements)} requirement groups; {len(files)} documents")
    if errors:
        print("\n".join(errors))
        return 1
    print("Plan references and local document links: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
