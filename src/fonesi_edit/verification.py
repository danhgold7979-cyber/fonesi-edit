"""Offline packaged proof: real jobs and media, explicitly synthetic inputs."""
from argparse import ArgumentParser
from pathlib import Path
import json
import platform
import os
import sys
import time
import shutil
from functools import partial
from http.server import SimpleHTTPRequestHandler,ThreadingHTTPServer
from threading import Thread

from .domain import Composition,Layer,fingerprint
from .storage import Store
from .jobs import Scheduler
from .batch import batch_plan,enqueue_batch
from .matrix import Angle,enqueue_rows
from .prototypes.media import create_fixture,extract_frame
from .prototypes.tools import scan_tools


def run(folder:Path):
    folder=folder.resolve();folder.mkdir(parents=True,exist_ok=True)
    if (folder/'proof.json').exists():raise FileExistsError('Use a new verification folder')
    files=create_fixture(folder/'media',duration=1)
    other=create_fixture(folder/'portrait',duration=1,portrait=True)
    for media in (files,other):
        source=media['source'];source.with_name(source.stem+'.zh.srt').write_text('1\n00:00:00,100 --> 00:00:00,800\nOriginal\n',encoding='utf-8')
        source.with_name(source.stem+'.vi.srt').write_text('1\n00:00:00,100 --> 00:00:00,800\nSub Việt\n',encoding='utf-8')
    store=Store(folder/'state.db')
    preset=Composition(width=320,height=180,fps=25,encoder='cpu',subtitle_style={'font_size':18,'outline':1},adjustments={'bilingual_subtitles':True},layers=[
        Layer(text='Fonesi Edit • kiểm chứng',width=.8,height=.2,style={'font_size':18,'outline':1,'color':'#ffffff'}),
        Layer(kind='image',path=str(files['logo']),x=.8,y=.1,width=.12,height=.18),
        Layer(kind='mask',x=.1,y=.7,width=.8,height=.15,style={'mode':'blur','radius':3})])
    batch=batch_plan({str(files['source'].parent):[str(files['source'])]},preset)
    jobs=enqueue_batch(store,batch)
    row=[Angle(1,1,str(files['source']),fingerprint(files['source'])),Angle(2,1,str(other['source']),fingerprint(other['source']))]
    jobs+=enqueue_rows(store,'packaged-proof',[row],preset,folder/'matrix')
    served=folder/'media';(served/'movie.mp4').write_bytes(files['source'].read_bytes())
    class Handler(SimpleHTTPRequestHandler):
        def log_message(self,*args):pass
    server=ThreadingHTTPServer(('127.0.0.1',0),partial(Handler,directory=str(served)))
    thread=Thread(target=server.serve_forever,daemon=True);thread.start()
    os.environ['NO_PROXY']=','.join(filter(None,[os.environ.get('NO_PROXY',''),'127.0.0.1','localhost']))
    base=f'http://127.0.0.1:{server.server_port}'
    for engine,url,media in [('video',base+'/movie.mp4','videos'),('gallery',base+'/logo.png','images')]:
        jobs.append(store.submit('download',{'url':url,'engine':engine,'media':media,'folder':str(folder/'download 中文'),'subtitles':False}))
    scheduler=Scheduler(store,parallel=1);started=time.monotonic();deadline=started+90
    while time.monotonic()<deadline:
        scheduler.tick()
        if all(store.job(key)['state'] in {'succeeded','failed','canceled','blocked'} for key in jobs) and not scheduler.active:break
        time.sleep(.05)
    success=all(store.job(key)['state']=='succeeded' for key in jobs)
    if not success:
        scheduler.shutdown()
        while scheduler.active and time.monotonic()<deadline+5:scheduler.tick();time.sleep(.05)
    results=[store.job(key) for key in jobs]
    server.shutdown();server.server_close();thread.join(timeout=3);scheduler.shutdown()
    if success:
        for i,job in enumerate(results):
            if job['kind']=='render':extract_frame(Path(job['result']['output']),folder/f'frame-{i}.png',.2)
        from .renaming import scene_rename_plan,apply_rename,undo_rename
        rename_source=folder/'rename/C1/shot.mp4';rename_source.parent.mkdir(parents=True);shutil.copyfile(files['source'],rename_source)
        rename_plan=scene_rename_plan([[Angle(1,1,str(rename_source),fingerprint(rename_source))]])
        renamed=apply_rename(folder/'rename',rename_plan);undo_rename(renamed['journal'])
        if not rename_source.is_file() or fingerprint(rename_source)!=fingerprint(files['source']):raise RuntimeError('Packaged rename/undo failed')
    report={'platform':platform.platform(),'synthetic':True,'passed':success,'elapsed_seconds':round(time.monotonic()-started,3),
            'frozen':bool(getattr(sys,'frozen',False)),'toolchain':[tool.to_dict() for tool in scan_tools()],
            'jobs':results,'rename_undo_verified':success,'bilingual_render_verified':success,'not_verified':['live platforms','live translation','Chrome authentication','GPU','all requested editor interactions']}
    (folder/'proof.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
    return success


def main(argv=None):
    parser=ArgumentParser();parser.add_argument('folder',type=Path);args=parser.parse_args(argv)
    return 0 if run(args.folder) else 1


if __name__=='__main__':raise SystemExit(main())
