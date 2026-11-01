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
    clause_ids = {c['id'] for c in clauses}
    criterion_ids = {c['id'] for c in criteria}
    assert len(clause_ids) == len(clauses), 'Duplicate source clause ID'
    for c in criteria:
        assert c['source_clause_ids'] and set(c['source_clause_ids']) <= clause_ids, c['id']
        assert c['planned_case_id'] and c['test_implementation_status']
        assert set(c['source_clause_ids']) == {x['id'] for x in clauses if c['id'] in x['criterion_ids']}, c['id']
    for clause in clauses:
        assert clause['criterion_ids'] and set(clause['criterion_ids']) <= criterion_ids, clause['id']
        data = (ROOT / 'docs' / clause['file']).read_bytes()
        assert hashlib.sha256(data).hexdigest() == clause['source_sha256']
        assert data.decode().splitlines()[clause['line'] - 1] == clause['verbatim']
    graph = json.loads((ROOT / 'docs/requirements/dependencies.json').read_text())
    assert set(graph['task_acceptance']) == expected
    nodes = graph['nodes']; active = set(); done = set()
    def visit(name):
        assert name in nodes, ('unknown dependency', name)
        assert name not in active, ('dependency cycle', name)
        if name in done: return
        active.add(name)
        for dep in nodes[name]['dependencies']: visit(dep)
        active.remove(name); done.add(name)
    for name in nodes: visit(name)
    for gate in graph['task_acceptance'].values():
        assert all(dep in nodes for dep in gate['requires'])
    excluded = json.loads((ROOT / 'docs/requirements/source_exclusions.json').read_text())
    for alias, file in [('PR','PRODUCT_REQUIREMENTS.md'),('ED','EDITOR_SPEC.md'),('SB','SETTINGS_AND_BROWSER_SPEC.md')]:
        in_fence = False
        for line_no, line in enumerate((ROOT/'docs'/file).read_text().splitlines(),1):
            if line.startswith('```'): in_fence = not in_fence; continue
            if in_fence or not line.strip() or line.startswith('#') or re.match(r'^\|\s*[-:]+', line): continue
            sid = f'{alias}-L{line_no:03}'
            assert sid in clause_ids or sid in excluded, ('unmapped source prose/table/bullet', sid)
    for name in ['COMPOSITION', 'JOBS', 'PRESET', 'PLANNING', 'UX', 'VERIFICATION']:
        assert (ROOT / f'docs/contracts/{name}.md').is_file()
    for e in evidence:
        assert e['generation'] == 'clean-2026-11-01'
        assert e['commit'] and e['command'] and e['environment']
    current = '\n'.join((ROOT / p).read_text() for p in ['docs/CURRENT_STATUS.md', 'docs/IMPLEMENTATION_PLAN.md', 'docs/REQUIREMENTS_TRACEABILITY.md'])
    assert not re.search(r'actions/runs/\d+', current), 'Old CI in current evidence'
    return {'task_count': len(tasks), 'phase_counts': expected_counts, 'requirement_groups': len(groups), 'child_assertions': len(criteria), 'source_clauses': len(clauses), 'artifact_milestones': len(nodes), 'dependency_graph': 'ACYCLIC', 'evidence_records': len(evidence), 'runtime_feature_evidence_records': sum(bool(e.get('criterion_ids')) for e in evidence), 'scoped_experiment_records': sum(e.get('acceptance_scope','').startswith('synthetic') for e in evidence), 'integrity': 'PASS', 'semantic_coverage': 'ACCEPTED_DESIGN_DBC3F30' if all(c['mapping_review'].startswith('INDEPENDENT_DESIGN_REVIEW_DBC3F30') for c in clauses) else 'PENDING_INDEPENDENT_REVIEW', 'runtime_assertions_passed': sum(c['status'] == 'PASS' for c in criteria), 'runtime_assertions_total': len(criteria), 'runtime_acceptance': 'PARTIAL' if any(c['status'] == 'PASS' for c in criteria) else 'NOT_RUN'}

if __name__ == '__main__':
    print(json.dumps(check(), indent=2))
