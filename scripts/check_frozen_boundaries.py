"""Owned frozen CLI integration; no GUI, media-tool execution or provider claims."""
from pathlib import Path
from hashlib import sha256
import argparse
import json
import os
import tempfile
from fonesi_edit.jobs.process import run_owned


def verify_license(bundle:Path,expected:Path):
    packaged=bundle/'_internal'/'fonesi_edit'/'licenses'/'pysubs2-LICENSE.txt'
    if packaged.read_bytes()!=expected.read_bytes():raise AssertionError('Packaged MIT notice differs or is missing')
    return sha256(packaged.read_bytes()).hexdigest()


def run_case(binary,args,expected_code,*,contains=None):
    result=run_owned([str(binary),*map(str,args)],timeout=30,max_output_bytes=256*1024)
    stdout=result.stdout.decode('utf-8');stderr=result.stderr.decode('utf-8')
    if result.returncode!=expected_code:raise AssertionError('Frozen CLI returned unexpected status')
    if contains is not None and contains not in stdout:raise AssertionError('Frozen CLI expected output missing')
    return {'expected_returncode':expected_code,'actual_returncode':result.returncode,
            'stdout':stdout,'stderr':stderr}


def main(argv=None):
    parser=argparse.ArgumentParser();parser.add_argument('--binary',type=Path,required=True)
    parser.add_argument('--report',type=Path,required=True);args=parser.parse_args(argv)
    if args.report.exists():raise AssertionError('Never overwrite frozen evidence')
    root=Path(__file__).resolve().parents[1];binary=args.binary.absolute()
    report={'source_sha':os.environ.get('EXPECTED_SOURCE_SHA'),
            'scope':'Frozen schema/subtitle parser/read-only tool discovery/license only; not GUI/media/Windows release acceptance',
            'cases':[],'status':'FAIL'}
    try:
        if not report['source_sha']:raise AssertionError('Exact reviewed source identity required')
        report['binary_sha256']=sha256(binary.read_bytes()).hexdigest()
        report['license_sha256']=verify_license(binary.parent,root/'src/fonesi_edit/licenses/pysubs2-LICENSE.txt')
        # Retain small owned fixtures for CI diagnostics. Never cleanup after unknown retirement.
        work=Path(tempfile.mkdtemp(prefix='fonesi-frozen-'))
        source=work/'Dự án 中文.json';source.write_bytes((root/'docs/schemas/examples/multi-stream-composition.json').read_bytes())
        subtitle=work/'Phụ đề 中文.srt';subtitle.write_bytes('1\n00:00:00,000 --> 00:00:01,000\nXin chào 中文\n'.encode())
        invalid=work/'invalid.srt';invalid.write_bytes(b'1\n00:00:70,000 --> 00:00:71,000\nPRIVATE_FIXTURE_TEXT\n')
        inputs={path:sha256(path.read_bytes()).hexdigest() for path in (source,subtitle,invalid)}
        data=work/'must-not-be-created'
        cases=[('schema',['--validate-plan',source,'--data-dir',data],0,'Valid CompositionPlan;'),
               ('subtitle',['--validate-subtitles',subtitle,'--subtitle-format','srt','--data-dir',data],0,'Parsed subtitles; 1 cue(s).'),
               ('subtitle-invalid',['--validate-subtitles',invalid,'--subtitle-format','srt','--data-dir',data],2,None),
               ('subtitle-empty-encoding',['--validate-subtitles',subtitle,'--subtitle-format','srt','--subtitle-encoding','','--data-dir',data],2,None)]
        for name,arguments,code,contains in cases:
            case=run_case(binary,arguments,code,contains=contains);case['name']=name
            if 'PRIVATE_FIXTURE_TEXT' in case['stdout']+case['stderr']:raise AssertionError('Subtitle content leaked')
            report['cases'].append(case)
        saved=dict(os.environ)
        try:
            empty=work/'empty-tools';empty.mkdir();os.environ['PATH']=str(empty)
            # Narrow test-process search hints, not a promise that Windows
            # child startup cannot expose host candidates; never machine PATH.
            for key in ('PROGRAMFILES','PROGRAMFILES(X86)','LOCALAPPDATA'):
                os.environ[key]=str(empty)
            case=run_case(binary,['--scan-tools','--tool-path','chrome='+str(work/'missing-chrome'),'--data-dir',data],0)
        finally:
            os.environ.clear();os.environ.update(saved) # Test process only; no machine/user PATH mutation.
        payload=json.loads(case['stdout'])
        chrome=next(x for x in payload['selections'] if x['tool']=='chrome')
        if (payload['status']!='COMPLETE' or any(x['readiness']!='UNCHECKED' for x in payload['candidates']) or
            chrome['state']!='INVALID_EXPLICIT_PATH' or chrome['candidate'] is not None or
            any(x['state'] not in {'MISSING','NEEDS_CHECK','INVALID_EXPLICIT_PATH'} for x in payload['selections'])):
            raise AssertionError('Frozen candidate-only boundary failed')
        case['name']='read-only-tool-discovery';report['cases'].append(case)
        if data.exists() or any(sha256(path.read_bytes()).hexdigest()!=digest for path,digest in inputs.items()):
            raise AssertionError('Frozen read-only command mutated inputs/application data')
        report['fixture_sha256']={path.name:digest for path,digest in inputs.items()};report['status']='PASS'
    except Exception as exc:
        report['failure_type']=type(exc).__name__
    with args.report.open('x',encoding='utf-8') as stream:json.dump(report,stream,indent=2,ensure_ascii=True)
    print(json.dumps({'status':report['status'],'completed_cases':len(report['cases']),'scope':report['scope']}))
    return 0 if report['status']=='PASS' else 1

if __name__=='__main__':raise SystemExit(main())
