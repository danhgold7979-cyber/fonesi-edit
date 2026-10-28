"""Lazy bounded scene solver. No implicit relaxation of W/K or unique history."""
from dataclasses import dataclass
from pathlib import Path
from collections import Counter
import csv
import math
import random
import re
import time
from ..core.model import digest,Project,Clip
from ..core.paths import content_hash
from .batch import VIDEO_EXT,allocate_durations,fit_duration
from .media import inspect_asset


def natural(value):return [int(x) if x.isdigit() else x.casefold() for x in re.split(r'(\d+)',str(value))]


def scan_scenes(root:Path):
    scenes=[]
    for folder in sorted((p for p in Path(root).iterdir() if p.is_dir() and not p.is_symlink()),key=lambda p:natural(p.name)):
        angles=[];hashes=set()
        for file in sorted(folder.iterdir(),key=lambda p:natural(p.name)):
            if file.is_file() and not file.is_symlink() and file.suffix.lower() in VIDEO_EXT:
                fingerprint=content_hash(file)
                if fingerprint in hashes:continue
                hashes.add(fingerprint);angles.append({'id':fingerprint,'path':str(file),'label':f'G{len(angles)+1}'})
        if not angles:raise ValueError(f'Scene has no valid candidates: {folder.name}')
        scenes.append({'id':digest({'angles':sorted(hashes)}),'name':folder.name,'label':f'C{len(scenes)+1}','angles':angles})
    if not scenes:raise ValueError('No scene folders')
    return scenes


@dataclass(frozen=True)
class Rules:
    window:int=0
    different:int=0
    compare:str='previous'
    unique:bool=True
    seed:int=0
    timeout:float=3


def valid_row(row,previous,rules:Rules,history=()):
    if rules.unique and tuple(row) in {tuple(x) for x in [*history,*previous]}:return False
    recent=previous[-rules.window:] if rules.window else []
    if any(any(a==b for a,b in zip(row,p)) for p in recent):return False
    comparisons=previous[-1:] if rules.compare=='previous' else recent
    return all(sum(a!=b for a,b in zip(row,p))>=rules.different for p in comparisons)


def validate_rows(rows,rules,history=()):
    previous=list(history)
    for index,row in enumerate(rows):
        if not valid_row(row,previous,rules):return index
        previous.append(row)
    return None


def generate(sizes:list[int],count:int,rules:Rules,history=(),locked:dict|None=None,cancel=lambda:False):
    if not sizes or any(n<=0 for n in sizes) or count<0:raise ValueError('Empty scene or negative count')
    if rules.window<0 or not 0<=rules.different<=len(sizes) or rules.compare not in {'previous','window'}:raise ValueError('Invalid W/K rules')
    total=math.prod(sizes);rng=random.Random(rules.seed);started=time.monotonic();history=[tuple(r) for r in history];locked=locked or {}
    if rules.unique and count>total-len(set(history)):
        return {'rows':[],'status':'proven_impossible','reason':'Requested unique rows exceed remaining product','theoretical':total}
    if count>rules.window and rules.window and any(n<=rules.window for n in sizes):
        return {'rows':[],'status':'proven_impossible','reason':'Strict W requires at least W+1 distinct angles in every scene for this sequence length','theoretical':total}
    rows=[];best=[];visits=0;usage=Counter((i,a) for r in history for i,a in enumerate(r));exhaustive=total<=4096
    def unpack(index):
        row=[]
        for n in reversed(sizes):row.append(index%n);index//=n
        return tuple(reversed(row))
    def candidates(depth):
        if exhaustive:
            ids=list(range(total));rng.shuffle(ids);values=[unpack(i) for i in ids]
            values.sort(key=lambda r:sum(usage[i,a] for i,a in enumerate(r)))
        else:
            # Bounded candidate sample, not the Cartesian product.
            values=list(dict.fromkeys(tuple(rng.randrange(n) for n in sizes) for _ in range(min(512,max(32,count*8)))))
            values.sort(key=lambda r:sum(usage[i,a] for i,a in enumerate(r)))
        fixed=locked.get(depth,{})
        return (r for r in values if all(r[int(i)]==a for i,a in fixed.items()))
    status='complete'
    def search():
        nonlocal visits,best,status
        if len(rows)>len(best):best=list(rows)
        if len(rows)==count:return True
        for row in candidates(len(rows)):
            if cancel():status='canceled';return False
            if time.monotonic()-started>rules.timeout:status='timeout';return False
            visits+=1
            if not valid_row(row,history+rows,rules):continue
            rows.append(row)
            for i,a in enumerate(row):usage[i,a]+=1
            if search():return True
            for i,a in enumerate(row):usage[i,a]-=1
            rows.pop()
            if status in {'timeout','canceled'}:return False
        return False
    solved=search()
    if not solved and status=='complete':status='proven_impossible' if exhaustive else 'search_exhausted'
    return {'rows':[list(r) for r in rows if solved] if solved else [list(r) for r in best], 'status':status,'theoretical':total,'visits':visits,'elapsed':time.monotonic()-started,'seed':rules.seed}


def reserve(store,project_id,combination,job_id):
    key=digest(combination)
    with store.connection() as db:
        db.execute('BEGIN IMMEDIATE');row=db.execute('SELECT state FROM matrix_history WHERE project=? AND combination=?',(project_id,key)).fetchone()
        if row and row['state'] in {'reserved','running','succeeded'}:raise ValueError('Combination already reserved or successful')
        db.execute('INSERT INTO matrix_history VALUES(?,?,?,?,NULL) ON CONFLICT(project,combination) DO UPDATE SET state=excluded.state,job_id=excluded.job_id,artifact=NULL',(project_id,key,'reserved',job_id))
    return key


def commit_history(store,project_id,key,job_id,result):
    if not result.get('validated'):raise ValueError('Matrix history requires validated artifact')
    with store.connection() as db:
        cursor=db.execute("UPDATE matrix_history SET state='succeeded',artifact=? WHERE project=? AND combination=? AND job_id=? AND state IN ('reserved','running')",(result['path'],project_id,key,job_id))
        if cursor.rowcount!=1:raise ValueError('Reservation ownership mismatch')


def export_csv(scenes,rows,path):
    with Path(path).open('w',encoding='utf-8-sig',newline='') as f:
        writer=csv.writer(f);writer.writerow(['Output',*[s['label'] for s in scenes],'Combination'])
        for i,row in enumerate(rows):
            labels=[f"{s['label']}{s['angles'][a]['label']}" for s,a in zip(scenes,row)]
            writer.writerow([i+1,*[s['angles'][a]['label'] for s,a in zip(scenes,row)],'+'.join(labels)])


def row_project(scenes,row,template:Project,target_duration=None,mode='equal',policy='speed'):
    if len(row)!=len(scenes):raise ValueError('Row must include every scene')
    project=Project.from_dict(template.to_dict());project.assets=[];project.clips=[]
    assets=[inspect_asset(Path(s['angles'][a]['path'])) for s,a in zip(scenes,row)]
    durations=allocate_durations([a.duration for a in assets],target_duration,mode) if target_duration else [a.duration for a in assets]
    offset=0
    for asset,duration in zip(assets,durations):
        project.assets.append(asset);clip=Clip(asset.id,0,asset.duration,offset=offset)
        parts=fit_duration(clip,duration,policy,fps=project.fps);project.clips.extend(parts);offset+=duration
    return project
