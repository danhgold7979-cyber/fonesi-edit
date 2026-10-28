from pathlib import Path
import json,re
root=Path(__file__).resolve().parents[1];docs=root/'docs';plan=(docs/'IMPLEMENTATION_PLAN.md').read_text(encoding='utf-8');coverage=json.loads((docs/'rebuild/coverage.json').read_text(encoding='utf-8'))
tasks=set(re.findall(r'P\d{2}-\d{2}(?=:)',plan));assert len(tasks)==94,len(tasks)
assert len(coverage)==95 and len({r['id'] for r in coverage})==95
for r in coverage:
 for task in re.findall(r'P\d{2}-\d{2}',r['tasks']):assert task in tasks,(r['id'],task)
for phase in range(1,13):
 p=f'P{phase:02}';text=(docs/'phases'/f'{p}_PLAN.md').read_text(encoding='utf-8')
 for task in tasks:
  if task.startswith(p):assert task in text,(p,task)
 for heading in ['Deliverables','Tests','Acceptance gate','blockers']:assert heading.lower() in text.lower()
print('PASS: 12 phase plans, 94 task IDs, 95 requirement groups, all task references valid')
