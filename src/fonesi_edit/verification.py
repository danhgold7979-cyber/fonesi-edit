"""Same end-to-end proof executes from source and frozen app. Fixtures explicitly synthetic/local."""
from pathlib import Path
from functools import partial
from http.server import ThreadingHTTPServer,SimpleHTTPRequestHandler
from threading import Thread
import json
import os
import platform
import sys
import time
from PIL import Image
from . import __version__
from .core.model import Project,Clip,Layer,Cue,US
from .core.paths import content_hash,atomic_write
from .core.process import run
from .core.storage import Store,save_project,load_project
from .core.jobs import Scheduler
from .services.media import tool,inspect_asset,validate_media,validate_image
from .services.matrix import generate,Rules,row_project,scan_scenes,reserve


def verify(directory:Path):
    directory=directory.resolve()
    if directory.exists() and any(directory.iterdir()):raise ValueError('Verification requires a new empty output directory')
    directory.mkdir(parents=True,exist_ok=True);source=directory/'nguồn 中文.mp4';image=directory/'ảnh.png'
    os.environ.setdefault('QT_QPA_PLATFORM','offscreen');os.environ['FONESI_DATA_DIR']=str(directory/'appdata')
    run([tool('ffmpeg'),'-v','error','-f','lavfi','-i','testsrc2=size=320x180:rate=25','-f','lavfi','-i','sine=frequency=440:sample_rate=48000','-t','1','-c:v','libx264','-c:a','aac',str(source)])
    Image.new('RGB',(80,60),'#26b8a0').save(image);source_hash=content_hash(source)
    a=inspect_asset(source);project=Project(width=320,height=180,assets=[a],clips=[Clip(a.id,0,a.duration)],
        layers=[Layer(text='Fonesi — kiểm tra',x=.05,y=.1,width=.9,height=.25,end=a.duration,style={'font_size':22,'fill':'#ffffff','overflow':'shrink'})],cues=[Cue(0,a.duration,'Phụ đề tiếng Việt')])
    save_project(project,directory/'project.json');assert load_project(directory/'project.json').to_dict()==project.to_dict()
    store=Store(directory/'state.db');scheduler=Scheduler(store,limit=2);jobs=[]
    jobs.append(store.enqueue('render',{'project':project.to_dict(),'output':str(directory/'output'/'batch.mp4')}))
    # Two real scene files from synthetic source; retain every scene.
    scene_root=directory/'scenes'
    for index,color in enumerate(['blue','green'],1):
        folder=scene_root/f'C{index}';folder.mkdir(parents=True)
        run([tool('ffmpeg'),'-v','error','-f','lavfi','-i',f'color={color}:size=320x180:rate=25','-t','0.4','-c:v','libx264',str(folder/'G1.mp4')])
    scenes=scan_scenes(scene_root);generated=generate([1,1],1,Rules(seed=42));matrix=row_project(scenes,generated['rows'][0],Project(width=320,height=180))
    jobs.append(store.enqueue('render',{'project':matrix.to_dict(),'output':str(directory/'output'/'matrix.mp4')}))
    handler=partial(SimpleHTTPRequestHandler,directory=str(directory));server=ThreadingHTTPServer(('127.0.0.1',0),handler);thread=Thread(target=server.serve_forever,daemon=True);thread.start()
    from urllib.parse import quote
    for path,kind,adapter in [(source,'video','yt-dlp'),(image,'image','gallery-dl')]:
        jobs.append(store.enqueue('download',{'url':f'http://127.0.0.1:{server.server_port}/'+quote(path.name),'output_root':str(directory/'downloads'),'media_kind':kind,'adapter':adapter}))
    try:
        deadline=time.monotonic()+180
        while time.monotonic()<deadline:
            scheduler.tick();states=[store.get(j)['state'] for j in jobs]
            if all(s in {'succeeded','succeeded_with_warnings','failed','blocked_configuration','canceled'} for s in states):break
            time.sleep(.1)
        records=[store.get(j) for j in jobs];success=all(j['state'] in {'succeeded','succeeded_with_warnings'} for j in records)
    finally:
        server.shutdown();server.server_close();thread.join();scheduler.shutdown(cancel=True)
    from PySide6.QtWidgets import QApplication
    from .ui.window import MainWindow
    app=QApplication.instance() or QApplication([]);original=MainWindow.scan_tools_async;MainWindow.scan_tools_async=lambda self:None
    window=MainWindow(directory/'ui');window.project.__dict__.update(project.__dict__);window.editor.refresh();window.tabs.setCurrentIndex(3);window.show();app.processEvents();window.grab().save(str(directory/'desktop.png'));ui=window.isVisible();window.close();app.processEvents();MainWindow.scan_tools_async=original
    report={'version':__version__,'frozen':bool(getattr(sys,'frozen',False)),'os':platform.platform(),'ui_opened':ui,'source_preserved':content_hash(source)==source_hash,
            'jobs':[{'id':r['id'],'kind':r['kind'],'state':r['state'],'error':r['error'],'result':json.loads(r['result'] or '{}')} for r in records],
            'tool_paths':{'ffmpeg':tool('ffmpeg'),'ffprobe':tool('ffprobe')},'external_acceptance':{k:'NOT RUN' for k in ['Windows','GPU','Chrome real sessions','live social full channels','live translation quality']}}
    if getattr(sys,'frozen',False):
        bundle=Path(sys._MEIPASS);manifest=json.loads((bundle/'metadata/build-source-manifest.json').read_text());mismatch=[]
        for relative,expected in manifest['source_hashes'].items():
            bundled=bundle/'source'/Path(relative).relative_to('src')
            if not bundled.is_file() or content_hash(bundled)!=expected:mismatch.append(relative)
        report['source_bundle_match']={'checked':len(manifest['source_hashes']),'mismatch':mismatch,'build_dirty':manifest['dirty']}
        success=success and not mismatch
    report['passed']=success and ui and report['source_preserved'];atomic_write(directory/'proof.json',json.dumps(report,ensure_ascii=False,indent=2))
    print(json.dumps(report,ensure_ascii=False,indent=2));return 0 if report['passed'] else 1
