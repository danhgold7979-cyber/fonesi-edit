"""Structural contract checks; passing does not establish feature acceptance."""
from pathlib import Path
import re

from scripts.check_plan import validate_traceability


def test_complete_requirement_traceability_matches_master_plan():
    root = Path(__file__).resolve().parents[1]
    trace = (root / "docs/REQUIREMENTS_TRACEABILITY.md").read_text(encoding="utf-8")
    plan = (root / "docs/IMPLEMENTATION_PLAN.md").read_text(encoding="utf-8")
    tasks = set(re.findall(r"^- \\[[ x]\\] (P\\d{2}-\\d{2}):", plan, re.M))
    requirements, errors = validate_traceability(trace, tasks, expected_count=95)
    assert len(requirements) == len(set(requirements)) == 95
    assert not errors, errors


def test_unmapped_or_missing_acceptance_is_rejected():
    tasks = {"P05-01"}
    row = "| SRC-01 | URL item | PR 3 | P05-01 | URL canonical works |"
    requirements, errors = validate_traceability(row, tasks, expected_count=1)
    assert requirements == ["SRC-01"] and not errors

    _, errors = validate_traceability(row.replace("P05-01", "—"), tasks, expected_count=1)
    assert any("no phase task mapping" in error for error in errors)

    _, errors = validate_traceability(row.replace("URL canonical works", ""), tasks, expected_count=1)
    assert any("missing acceptance" in error for error in errors)

    _, errors = validate_traceability(row.replace("P05-01", "P19-99"), tasks, expected_count=1)
    assert any("unknown phase task P19-99" in error for error in errors)


def test_duplicate_or_missing_group_is_rejected():
    row = "| SRC-01 | Source URL | PR 3 | P05-01 | URL validated |"
    _, duplicates = validate_traceability(row + "\n" + row, {"P05-01"}, expected_count=2)
    assert "Duplicate requirement ID" in duplicates
    _, missing = validate_traceability(row, {"P05-01"}, expected_count=95)
    assert any("Expected 95 requirement groups" in error for error in missing)
