"""Explicit same-content relink commands; never silently replace source content."""
from pathlib import Path
import stat
from typing import Callable,Literal
from fonesi_edit.domain.composition import CompositionPlan
from fonesi_edit.media.probe import fingerprint,ProbeCanceled
from .projects import Project,StorageError
from .autosave import CompletedCommand


class RelinkMismatch(StorageError):pass


def relink(project:Project, collection:Literal['assets','fonts'], reference_id:str,
           candidate:Path|str, *, cancel:Callable[[],bool]=lambda:False)->CompletedCommand:
    """Read-only source observation; caller commits explicitly and revalidates at use."""
    if collection not in ('assets','fonts'):raise StorageError('Unknown reference collection')
    plan=project.plan.to_dict()
    matches=[item for item in plan[collection] if item['id']==reference_id]
    if len(matches)!=1:raise StorageError('Unknown or ambiguous reference identity')
    if cancel():raise ProbeCanceled('Relink canceled')
    path=Path(candidate).absolute()
    info=path.lstat()
    if not stat.S_ISREG(info.st_mode) or getattr(info,'st_file_attributes',0)&0x400:
        raise StorageError('Relink candidate must be a regular non-reparse file')
    digest=fingerprint(path,cancel)
    if cancel():raise ProbeCanceled('Relink canceled')
    item=matches[0]
    if digest!=item['sha256'] or digest!=item['path_ref']['asset_hash']:
        raise RelinkMismatch('Different content requires explicit replacement/re-import, not relink')
    item['path_ref']={'base':'absolute','path':str(path),'asset_hash':digest}
    revision=plan['revision'];plan['revision']=revision+1
    updated=Project(project.id,project.name,CompositionPlan.parse(plan))
    return CompletedCommand(updated,revision)


def relink_root(project:Project, original_root:Path|str, new_root:Path|str, *,
                project_base:Path|str,
                cancel:Callable[[],bool]=lambda:False,
                progress:Callable[[int,int],None]=lambda done,total:None)->CompletedCommand:
    """Verify an explicit root remap atomically in memory; external references stay put."""
    import os
    from pathlib import PureWindowsPath
    old=Path(original_root);new=Path(new_root);base=Path(project_base)
    if not old.is_absolute() or not new.is_absolute() or not base.is_absolute():
        raise StorageError('Both explicitly chosen roots must be absolute')
    old=Path(os.path.normpath(str(old)));new=Path(os.path.normpath(str(new)))
    info=new.lstat()
    if not stat.S_ISDIR(info.st_mode) or getattr(info,'st_file_attributes',0)&0x400:
        raise StorageError('New root must be an existing non-reparse directory')
    plan=project.plan.to_dict();mapped=[]
    for collection in ('assets','fonts'):
        for item in plan[collection]:
            ref=item['path_ref'];value=ref['path'];windows=PureWindowsPath(value)
            if '\x00' in value:raise StorageError('Invalid reference path')
            if ref['base']=='project':
                if Path(value).is_absolute() or windows.drive or windows.root:
                    raise StorageError('Ambiguous project-relative reference')
                source=Path(os.path.normpath(str(base/value)))
            else:
                source=Path(value)
                if not source.is_absolute():raise StorageError('Absolute reference not native to this platform')
                source=Path(os.path.normpath(str(source)))
            try:relative=source.relative_to(old)
            except ValueError:continue
            mapped.append((item,new/relative))
    if not mapped:raise RelinkMismatch('No references belong to the chosen original root')
    total=len(mapped);progress(0,total)
    for done,(item,candidate) in enumerate(mapped,1):
        if cancel():raise ProbeCanceled('Root relink canceled')
        info=candidate.lstat()
        if not stat.S_ISREG(info.st_mode) or getattr(info,'st_file_attributes',0)&0x400:
            raise StorageError('Mapped candidate must be a regular non-reparse file')
        digest=fingerprint(candidate,cancel)
        if digest!=item['sha256'] or digest!=item['path_ref']['asset_hash']:
            raise RelinkMismatch('Mapped content differs; no partial relink is applied')
        item['path_ref']={'base':'absolute','path':str(candidate),'asset_hash':digest}
        progress(done,total)
    if cancel():raise ProbeCanceled('Root relink canceled')
    revision=plan['revision'];plan['revision']+=1
    return CompletedCommand(Project(project.id,project.name,CompositionPlan.parse(plan)),revision)
