from copy import deepcopy
from dataclasses import dataclass,asdict
from pathlib import Path
import hashlib
import math
import random
import time

from .batch import VIDEO_EXTENSIONS,natural_key,fit_duration,bind_source_subtitles,configured_clip
from .domain import Clip,Composition,canonical,fingerprint,identifier,checked_payload
from .prototypes.media import probe
from .render import audio_duration


@dataclass(frozen=True)
class Angle:
    scene:int
    index:int
    path:str
    hash:str


def scan_scenes(root:Path,selected=None):
    directories=sorted([p for p in root.iterdir() if p.is_dir() and not p.is_symlink() and not p.is_junction() and not p.name.startswith('.') and not p.name.casefold().endswith(' edit')],key=lambda p:natural_key(p.name))
    scenes=[]
    for directory in directories:
        if selected is not None and str(directory) not in selected:continue
        paths=sorted([p for p in directory.iterdir() if p.is_file() and not p.is_symlink() and p.suffix.lower() in VIDEO_EXTENSIONS],key=lambda p:natural_key(p.name))
        if not paths:raise ValueError('Cảnh không có video: '+directory.name)
        angles=[];seen=set()
        for index,path in enumerate(paths,1):
            digest=fingerprint(path)
            if digest in seen:continue
            seen.add(digest);angles.append(Angle(len(scenes)+1,index,str(path.resolve()),digest))
        scenes.append(angles)
    if not scenes:raise ValueError('Không tìm thấy folder cảnh')
    return scenes


def combination(row):return canonical([angle.hash for angle in row])


def valid_against(row,previous,window=0,different=0,compare_window=False):
    values=[a.hash if isinstance(a,Angle) else a for a in row]
    for old in previous[-window:] if window else []:
        if any(a==b for a,b in zip(values,old)):return False
    for old in previous[-window:] if compare_window and window else previous[-1:]:
        if sum(a!=b for a,b in zip(values,old))<different:return False
    return True


def generate(scenes,count,seed=0,window=0,different=0,compare_window=False,history=(),seconds=10,locks=None,cancel=None):
    if count<1 or window<0 or not 0<=different<=len(scenes):raise ValueError('Invalid N/W/K')
    if any(not scene for scene in scenes):raise ValueError('Empty scene')
    capacity=math.prod(len(scene) for scene in scenes)
    previous=[list(item) for item in history];used={canonical(item) for item in previous}
    allowed_hashes=[{a.hash for a in scene} for scene in scenes]
    matching_history={
        canonical(old) for old in previous
        if len(old)==len(scenes)
        and all(value in allowed for value,allowed in zip(old,allowed_hashes))
    }
    possible_history=len(matching_history)
    if count>capacity-possible_history:raise ValueError(f'Chỉ còn tối đa {capacity-possible_history} tổ hợp chưa dùng')
    normalized_locks={}
    for raw_row,columns in (locks or {}).items():
        try:row_index=int(raw_row)
        except (TypeError,ValueError):raise ValueError('Invalid locked row index') from None
        if row_index<0 or row_index>=count or row_index in normalized_locks:
            raise ValueError('Locked row is outside the requested matrix or duplicated')
        if not isinstance(columns,dict):raise ValueError('Invalid locked scene map')
        normalized_locks[row_index]={}
        for raw_scene,angle_hash in columns.items():
            try:scene_index=int(raw_scene)
            except (TypeError,ValueError):raise ValueError('Invalid locked scene index') from None
            if scene_index<0 or scene_index>=len(scenes):
                raise ValueError('Locked scene index outside the matrix')
            if angle_hash not in allowed_hashes[scene_index]:
                raise ValueError('Locked angle missing from scene')
            normalized_locks[row_index][scene_index]=angle_hash
    rng=random.Random(seed);rows=[];frequency={};start=time.monotonic();attempts=0;locks=normalized_locks
    # Small spaces are enumerated as indices, never as a Cartesian list of media objects.
    order=rng.sample(range(capacity),capacity) if capacity<=10000 else None;cursor=0
    while len(rows)<count and time.monotonic()-start<seconds:
        if cancel and cancel.is_set():raise RuntimeError('Canceled')
        attempts+=1
        if order is not None:
            if cursor>=len(order):
                if not window and not different:break
                rng.shuffle(order);cursor=0
            index=order[cursor];cursor+=1;row=[]
            for scene in scenes:
                row.append(scene[index%len(scene)]);index//=len(scene)
        else:
            row=[]
            for i,scene in enumerate(scenes):
                available=[a for a in scene if not any(a.hash==old[i] for old in previous[-window:] if len(old)>i)] if window else list(scene)
                if not available:break
                row.append(rng.choices(available,weights=[1/(1+frequency.get(a.hash,0)) for a in available])[0])
            if len(row)!=len(scenes):break
        for scene_index,angle_hash in locks.get(len(rows),{}).items():
            scene_index=int(scene_index)
            match=next((a for a in scenes[scene_index] if a.hash==angle_hash),None)
            if not match:raise ValueError('Locked angle missing from scene')
            row[scene_index]=match
        key=combination(row)
        if key in used or not valid_against(row,previous,window,different,compare_window):continue
        rows.append(row);values=[a.hash for a in row];previous.append(values);used.add(key)
        for angle in row:frequency[angle.hash]=frequency.get(angle.hash,0)+1
    return {'rows':rows,'capacity':capacity,'complete':len(rows)==count,'requested':count,'seed':seed,'attempts':attempts,
            'reason':None if len(rows)==count else 'Chưa tìm đủ trong budget; không tự nới W/K hoặc kết luận vô nghiệm'}



def matrix_rows_valid(rows, history=(), window=0, different=0, compare_window=False):
    """Check unique combinations and every forward W/K constraint in row order."""
    if window < 0 or different < 0:
        raise ValueError('Invalid W/K')
    previous = [list(item) for item in history]
    used = {canonical(values) for values in previous}
    for row in rows:
        key = combination(row)
        if key in used or not valid_against(row, previous, window, different, compare_window):
            return False
        previous.append([angle.hash for angle in row])
        used.add(key)
    return True


def regenerate_row(scenes, rows, row_index, seed=0, window=0, different=0,
                   compare_window=False, history=(), locks=None,
                   seconds=5, cancel=None):
    """Change exactly one matrix row, preserving locked cells and all other rows.

    Candidate feasibility is checked against *all* rows, not only rows before
    the changed one. Small spaces are searched exhaustively; a large timed
    search raises an explicit budget error rather than pretending UNSAT.
    The input rows and locks are never mutated.
    """
    if not scenes or any(not scene for scene in scenes):
        raise ValueError('Empty matrix scenes')
    if type(row_index) is not int or not 0 <= row_index < len(rows):
        raise ValueError('Invalid matrix row index')
    if window < 0 or not 0 <= different <= len(scenes):
        raise ValueError('Invalid W/K')
    if not math.isfinite(seconds) or seconds <= 0:
        raise ValueError('Invalid regeneration time budget')
    if any(len(row) != len(scenes) for row in rows):
        raise ValueError('Invalid matrix row length')
    allowed = [{angle.hash for angle in scene} for scene in scenes]
    if any(any(angle.hash not in allowed[i] for i, angle in enumerate(row)) for row in rows):
        raise ValueError('Matrix references a missing angle')
    if not matrix_rows_valid(rows, history, window, different, compare_window):
        raise ValueError('Matrix is already invalid against history/W/K; regenerate the matrix')
    normalized_locks = {}
    for raw_index, angle_hash in (locks or {}).items():
        try:
            index = int(raw_index)
        except (TypeError, ValueError):
            raise ValueError('Invalid locked scene index') from None
        if index < 0 or index >= len(scenes) or index in normalized_locks:
            raise ValueError('Invalid or duplicated locked scene index')
        if angle_hash not in allowed[index] or angle_hash != rows[row_index][index].hash:
            raise ValueError('Locked angle does not match current matrix cell')
        normalized_locks[index] = angle_hash
    free = [i for i in range(len(scenes)) if i not in normalized_locks]
    capacity = math.prod(len(scenes[i]) for i in free)
    if capacity <= 1:
        raise ValueError('All angles are locked or no alternative exists')
    original_key = combination(rows[row_index])
    # Preserve the result for the same input/seed without polluting Python's
    # global randomness or relying on process-dependent hash randomization.
    rng = random.Random(f'{seed}:{row_index}:{original_key}')
    order = rng.sample(range(capacity), capacity) if capacity <= 10000 else None
    deadline = time.monotonic() + seconds
    attempts = 0
    while attempts < (capacity if order is not None else 100000):
        if cancel is not None and cancel.is_set():
            raise RuntimeError('Canceled')
        if time.monotonic() >= deadline:
            break
        if order is not None:
            sample = order[attempts]
        else:
            sample = rng.randrange(capacity)
        attempts += 1
        proposal = list(rows[row_index])
        for scene_index in free:
            scene = scenes[scene_index]
            proposal[scene_index] = scene[sample % len(scene)]
            sample //= len(scene)
        if combination(proposal) == original_key:
            continue
        updated = [list(row) for row in rows]
        updated[row_index] = proposal
        if matrix_rows_valid(updated, history, window, different, compare_window):
            return {
                'row': proposal, 'attempts': attempts, 'capacity': capacity,
                'exhaustive': order is not None,
            }
    if order is not None and attempts >= capacity:
        raise ValueError('Không có góc thay thế nào đáp ứng khóa ô, lịch sử và W/K')
    raise RuntimeError('Chưa tìm được góc khác trong ngân sách tìm; không tự nới W/K')


def history(store,scope):
    import json
    with store.connect() as conn:
        return [json.loads(r[0]) for r in conn.execute("SELECT combination FROM matrix_history WHERE scope=? AND state IN ('reserved','succeeded') ORDER BY created",(scope,))]


def row_composition(row,preset,audio=None,allocation='proportional',minimum=.5,maximum=2):
    c=deepcopy(preset);c.clips=[]
    c.seed=int(hashlib.sha256(f'{preset.seed}:{combination(row)}'.encode()).hexdigest()[:8],16)%2147483647
    for angle in row:
        info=probe(Path(angle.path));c.clips.append(configured_clip(angle.path,info,c,hashlib.sha256(f'{angle.scene}:{angle.hash}'.encode()).hexdigest()[:32]))
    for layer in c.layers:layer.clip_ids=[]
    if audio:
        c.audio=[{'path':str(Path(audio).resolve()),'mode':'main','volume':1}]+[a for a in c.audio if a.get('mode')!='main']
        c=fit_duration(c,audio_duration(audio),minimum=minimum,maximum=maximum,allocation=allocation)
    bind_source_subtitles(c)
    return c


def enqueue_rows(store,scope,rows,preset,output_root,audio=None,allocation='proportional',minimum=.5,maximum=2,window=0,different=0,compare_window=False):
    jobs=[];plans=[]
    for row in rows:
        comp=row_composition(row,preset,audio,allocation,minimum,maximum)
        key=combination(row);digest=hashlib.sha256(key.encode()).hexdigest()[:12]
        payload={'composition':comp.to_dict(),'output':str(Path(output_root)/f'video_{digest}.mp4'),'matrix_scope':scope,'matrix_combination':key}
        payload['_tools']=store.setting('tool_paths',{})
        plans.append((identifier(),key,payload))
    with store.connect() as conn:
        conn.execute('BEGIN IMMEDIATE')
        import json
        previous=[json.loads(r[0]) for r in conn.execute("SELECT combination FROM matrix_history WHERE scope=? AND state IN ('reserved','succeeded') ORDER BY created",(scope,))]
        sequence=conn.execute('SELECT COUNT(*) FROM matrix_history WHERE scope=?',(scope,)).fetchone()[0]
        for job_id,key,data in plans:
            existing=conn.execute('SELECT state FROM matrix_history WHERE scope=? AND combination=?',(scope,key)).fetchone()
            if existing and existing[0] in {'reserved','succeeded'}:raise ValueError('Tổ hợp đã được dùng/đặt chỗ; hãy sinh lại')
            values=json.loads(key)
            if not valid_against(values,previous,window,different,compare_window):raise ValueError('Lịch sử vừa thay đổi hoặc hàng vi phạm W/K; hãy sinh lại ma trận')
            previous.append(values);sequence+=1
            output=Path(data['output']);data['output']=str(output.with_name(f'video_{sequence:06d}_'+output.name.removeprefix('video_')))
            now=time.time()
            conn.execute("INSERT INTO jobs(id,kind,state,payload,created,updated) VALUES(?,'render','pending',?,?,?)",(job_id,canonical(checked_payload(data)),now,now))
            conn.execute("INSERT INTO matrix_history VALUES(?,?,'reserved',?,?) ON CONFLICT(scope,combination) DO UPDATE SET state='reserved',job_id=excluded.job_id,created=excluded.created",(scope,key,job_id,now));jobs.append(job_id)
    return jobs
