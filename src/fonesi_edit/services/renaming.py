"""Explicit two-stage rename with collision preview and content-checked undo."""
from pathlib import Path
import os
from ..core.model import uid
from ..core.paths import safe_name,content_hash,atomic_write
import json


def plan_rename(paths:list[Path],pattern:str):
    if '{n}' not in pattern and len(paths)>1:raise ValueError('Multiple files require {n} to avoid implicit collisions')
    plan=[];sources={Path(p).resolve() for p in paths};targets=set()
    for index,source in enumerate(paths,1):
        source=Path(source).resolve();name=pattern.replace('{n}',str(index)).replace('{stem}',source.stem)
        if name!=safe_name(name,180):raise ValueError('Unsafe Windows filename')
        target=source.with_name(name+source.suffix)
        if target in targets or target.exists() and target not in sources:raise FileExistsError('Rename target collision: '+str(target))
        targets.add(target);plan.append({'source':str(source),'target':str(target),'sha256':content_hash(source)})
    return plan


def apply_rename(plan:list[dict],journal:Path):
    if journal.exists():raise FileExistsError('Use a new rename journal')
    staged=[];published=[]
    atomic_write(journal,json.dumps({'state':'prepared','entries':plan},ensure_ascii=False,indent=2))
    try:
        for row in plan:
            source=Path(row['source']);target=Path(row['target'])
            if content_hash(source)!=row['sha256']:raise ValueError('Source changed since preview')
            if source==target:continue
            temp=source.with_name('.fonesi-rename-'+uid()+source.suffix)
            os.link(source,temp);source.unlink();staged.append((row,temp))
        atomic_write(journal,json.dumps({'state':'staged','entries':plan,'staging':[{'entry':r,'temp':str(t)} for r,t in staged]},ensure_ascii=False,indent=2))
        for row,temp in staged:
            os.link(temp,Path(row['target']));published.append(row)
        for _,temp in staged:temp.unlink()
        atomic_write(journal,json.dumps({'state':'complete','entries':plan},ensure_ascii=False,indent=2))
    except Exception:
        for row in published:
            p=Path(row['target'])
            if p.exists() and content_hash(p)==row['sha256']:p.unlink()
        for row,temp in staged:
            source=Path(row['source'])
            if temp.exists() and not source.exists():os.link(temp,source);temp.unlink()
        raise


def undo_rename(journal:Path,undo_journal:Path):
    data=json.loads(journal.read_text())
    if data['state']!='complete':raise ValueError('Incomplete rename requires journal recovery, not blind undo')
    inverse=[{'source':r['target'],'target':r['source'],'sha256':r['sha256']} for r in data['entries']]
    apply_rename(inverse,undo_journal)
