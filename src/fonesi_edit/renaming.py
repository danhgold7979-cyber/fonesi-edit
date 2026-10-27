"""Explicit, journaled scene-angle renaming. Media bytes are never rewritten."""
from pathlib import Path
import json
import time
from .domain import fingerprint,atomic_json,identifier
from .prototypes.media import _publish


def _move(source,target):
    _publish(source,target)
    if source.exists():
        if not source.samefile(target):raise RuntimeError('Nguồn vừa được tiến trình khác thay thế; giữ cả hai tệp để kiểm tra')
        source.unlink()


def scene_rename_plan(scenes):
    operations=[]
    for scene in scenes:
        for angle in scene:
            source=Path(angle.path);target=source.with_name(f'C{angle.scene}G{angle.index}'+source.suffix.lower())
            if source==target:continue
            operations.append({'source':str(source),'target':str(target),'sha256':angle.hash})
            for sidecar in source.parent.glob(source.stem+'*'):
                if sidecar.is_file() and not sidecar.is_symlink() and sidecar.suffix.lower() in {'.srt','.vtt','.ass'} and (sidecar.stem==source.stem or sidecar.name.startswith(source.stem+'.')):
                    operations.append({'source':str(sidecar),'target':str(target.with_name(target.stem+sidecar.name[len(source.stem):])),'sha256':fingerprint(sidecar)})
    return operations


def apply_rename(root,operations,cancel=None):
    root=Path(root).resolve();sources={Path(op['source']) for op in operations};targets={Path(op['target']) for op in operations}
    if len(sources)!=len(operations) or len(targets)!=len(operations):raise ValueError('Duplicate rename source/target')
    if not operations:raise ValueError('Tên đã đúng, không có tệp cần đổi')
    for op in operations:
        source,target=Path(op['source']),Path(op['target'])
        if source.is_symlink() or not source.is_file() or source.resolve()!=source or not source.is_relative_to(root):raise ValueError('Nguồn không hợp lệ hoặc đã di chuyển')
        if target.parent!=source.parent or target.is_symlink():raise ValueError('Đổi tên chỉ trong cùng folder')
        if target.exists() and target not in sources:raise FileExistsError('Tên đích đã có: '+target.name)
        if fingerprint(source)!=op['sha256']:raise ValueError('Nguồn đã thay đổi sau quét: '+source.name)
    key=identifier();journal=root/'.fonesi-renames'/(str(time.time_ns())+'-'+key+'.json')
    records=[{**op,'temporary':str(Path(op['source']).with_name('.fonesi-rename-'+key+'-'+str(i))),'state':'source'} for i,op in enumerate(operations)]
    data={'version':1,'root':str(root),'state':'prepared','operations':records};atomic_json(journal,data)
    try:
        for op in records:
            if cancel and cancel.is_set():raise RuntimeError('Rename canceled')
            _move(Path(op['source']),Path(op['temporary']));op['state']='temporary';atomic_json(journal,data)
        for op in records:
            if cancel and cancel.is_set():raise RuntimeError('Rename canceled')
            _move(Path(op['temporary']),Path(op['target']));op['state']='target';atomic_json(journal,data)
        data['state']='completed';atomic_json(journal,data)
    except BaseException:
        # Roll back through distinct temporary names, including source/target cycles.
        try:
            for op in records:
                if op['state']=='target':_move(Path(op['target']),Path(op['temporary']));op['state']='temporary'
            for op in records:
                if op['state']=='temporary':_move(Path(op['temporary']),Path(op['source']));op['state']='source'
            data['state']='rolled_back'
        except Exception:data['state']='recovery_required'
        atomic_json(journal,data);raise
    return {'journal':str(journal),'mapping':{op['source']:op['target'] for op in operations},'count':len(operations)}


def undo_rename(journal,cancel=None):
    journal=Path(journal);data=json.loads(journal.read_text(encoding='utf-8'))
    if data.get('state')!='completed':raise ValueError('Mapping này chưa hoàn tất hoặc đã hoàn tác')
    result=apply_rename(data['root'],[{'source':op['target'],'target':op['source'],'sha256':op['sha256']} for op in data['operations']],cancel)
    data['state']='undone';data['undo_journal']=result['journal'];atomic_json(journal,data);return result


def recover_rename(journal,cancel=None):
    journal=Path(journal);data=json.loads(journal.read_text(encoding='utf-8'));operations=[]
    if data.get('state') not in {'prepared','recovery_required'}:raise ValueError('Journal không có thao tác dở cần phục hồi')
    for op in data['operations']:
        candidates=[Path(op[key]) for key in ('source','temporary','target') if Path(op[key]).is_file() and fingerprint(Path(op[key]))==op['sha256']]
        candidates=list(dict.fromkeys(candidates))
        if len(candidates)!=1:raise ValueError('Không xác định được duy nhất tệp gốc; giữ nguyên journal để kiểm tra')
        if str(candidates[0])!=op['source']:operations.append({'source':str(candidates[0]),'target':op['source'],'sha256':op['sha256']})
    result=apply_rename(data['root'],operations,cancel) if operations else {'journal':str(journal),'mapping':{},'count':0}
    data['state']='recovered';atomic_json(journal,data);return result
