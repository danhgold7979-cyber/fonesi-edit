"""Clean-rebuild planning integrity check; NOT semantic or runtime acceptance."""
from pathlib import Path
import hashlib
import json
import re

ROOT = Path(__file__).resolve().parents[1]

def check() -> dict:
    tasks = json.loads((ROOT / 'docs/requirements/tasks.json').read_text())
    criteria = json.loads((ROOT / 'docs/requirements/criteria.json').read_text())
    clauses = json.loads((ROOT / 'docs/requirements/source_clauses.json').read_text())
    evidence = json.loads((ROOT / 'docs/evidence/records.json').read_text())
    expected_counts = [8, 10, 9, 8, 10, 6, 8, 7, 6, 7, 8, 7]
    expected = {f'P{phase:02}-{task:02}' for phase, count in enumerate(expected_counts, 1) for task in range(1, count + 1)}
    assert len(tasks) == 94 and {t['id'] for t in tasks} == expected, 'Task IDs/count changed'
    master = (ROOT / 'docs/IMPLEMENTATION_PLAN.md').read_text()
    assert set(re.findall(r'\*\*(P\d\d-\d\d)\*\*:', master)) == expected, 'Master task mismatch'
    for phase, count in enumerate(expected_counts, 1):
        plan = (ROOT / f'docs/phases/P{phase:02}_PLAN.md').read_text()
        headings = re.findall(r'^## (P\d\d-\d\d)\b', plan, re.M)
        assert len(headings) == count, (phase, headings)
        assert set(headings) == {x for x in expected if x.startswith(f'P{phase:02}-')}
        assert 'phiên bản yêu cầu và các hợp đồng domain liên quan đã khóa' not in plan, 'Old generic input'
    groups = set(re.findall(r'^\| ((?!FLOW)[A-Z]+-\d+) \|', (ROOT / 'docs/REQUIREMENTS_TRACEABILITY.md').read_text(), re.M))
    assert len(groups) == 95 and {c['group_id'] for c in criteria} == groups
    assert len({c['id'] for c in criteria}) == len(criteria), 'Duplicate child ID'
    for c in criteria:
        assert c['assertion'] and c['source_sections'] and c['task_ids']
        assert set(c['task_ids']) <= expected, c['id']
        assert c['status'] in {'NOT_RUN', 'BLOCKED', 'PASS', 'FAIL'}
        if c['status'] == 'PASS':
            assert c['evidence'], 'Unbacked PASS'
            assert all(ref in {e['id'] for e in evidence} for ref in c['evidence'])
    for clause in clauses:
        data = (ROOT / 'docs' / clause['file']).read_bytes()
        assert hashlib.sha256(data).hexdigest() == clause['source_sha256']
        assert data.decode().splitlines()[clause['line'] - 1] == clause['verbatim']
    for name in ['COMPOSITION', 'JOBS', 'PRESET', 'PLANNING', 'UX', 'VERIFICATION']:
        assert (ROOT / f'docs/contracts/{name}.md').is_file()
    for e in evidence:
        assert e['generation'] == 'clean-2026-11-01'
        assert e['commit'] and e['command'] and e['environment']
    current = '\n'.join((ROOT / p).read_text() for p in ['docs/CURRENT_STATUS.md', 'docs/IMPLEMENTATION_PLAN.md', 'docs/REQUIREMENTS_TRACEABILITY.md'])
    assert not re.search(r'actions/runs/\d+', current), 'Old CI in current evidence'
    return {'task_count': len(tasks), 'phase_counts': expected_counts, 'requirement_groups': len(groups), 'child_assertions': len(criteria), 'source_clauses': len(clauses), 'runtime_evidence_records': len(evidence), 'integrity': 'PASS', 'semantic_coverage': 'PENDING_INDEPENDENT_REVIEW', 'runtime_acceptance': 'NOT_RUN'}

if __name__ == '__main__':
    print(json.dumps(check(), indent=2))
