from contextlib import ExitStack
from hashlib import sha256
from pathlib import Path
import json
import os
import pytest
from fonesi_edit.artifacts.filesystem import Destination,PublicationConflict,PublicationUnknown
from fonesi_edit.jobs.admission import NamespaceAdmission
from fonesi_edit.jobs.output_manifest import RequiredOutput,RequiredOutputs
from fonesi_edit.jobs.publication import PublicationSession
from fonesi_edit.jobs.repository import JobRepository
from fonesi_edit.jobs.ownership import CoordinatorOwnership
from fonesi_edit.domain.composition import CompositionPlan

RAW=b'1\n00:00:00,000 --> 00:00:01,000\nCaption'


def output(root):
    return RequiredOutputs((RequiredOutput('subtitle','subtitle',str(root),'final.srt',
        subtitle_format='srt',subtitle_encoding='utf-8',subtitle_sha256=sha256(RAW).hexdigest()),))


def source_record(path):return {'path_ref':{'base':'absolute','path':str(path)}}


def test_source_and_font_pins_reject_replacement_and_never_revive(tmp_path):
    source=tmp_path/'source';source.mkdir();root=tmp_path/'output';root.mkdir()
    file=source/'font.ttf';file.write_bytes(b'font')
    with Destination(root) as dest,NamespaceAdmission({'assets':[],'fonts':[source_record(file)]},{str(root):dest},output(root)) as admission:
        try:file.rename(source/'old.ttf')
        except PermissionError:
            if os.name!='nt':raise
            admission.guard();return # Native pin prevented mutation, not an injected replacement.
        file.write_bytes(b'font')
        with pytest.raises(PublicationUnknown):admission.guard()
        file.unlink();(source/'old.ttf').rename(file)
        with pytest.raises(PublicationUnknown,match='revoked'):admission.guard()


def test_unresolved_source_and_cache_output_refused_without_stage(tmp_path):
    root=tmp_path/'root';root.mkdir();cache=tmp_path/'cache';cache.mkdir()
    with Destination(root) as dest:
        with pytest.raises(PublicationConflict,match='Resolve'):
            NamespaceAdmission({'assets':[{'path_ref':{'base':'project','path':'input.mp4'}}],'fonts':[]},{str(root):dest},output(root))
        with pytest.raises(PublicationConflict,match='cache'):
            NamespaceAdmission({'assets':[],'fonts':[]},{str(root):dest},output(root),cache_roots=(tmp_path,))
    assert not list(root.iterdir())


def test_exact_hardlink_source_final_collision_is_never_modified(tmp_path):
    root=tmp_path/'output';root.mkdir();source=tmp_path/'input';source.write_bytes(b'original')
    with Destination(root) as dest,NamespaceAdmission({'assets':[source_record(source)],'fonts':[]},{str(root):dest},output(root)) as admission:
        os.link(source,root/'final.srt')
        # Linking changes ctime; guard remains conservative, never unlinks either name.
        with pytest.raises((PublicationConflict,PublicationUnknown)):admission.guard_final(output(root).items[0])
    assert source.read_bytes()==(root/'final.srt').read_bytes()==b'original'


@pytest.fixture
def session(tmp_path,empty_plan):
    source=tmp_path/'sources';source.mkdir();root=source/'output';root.mkdir();cache=source/'cache';cache.mkdir()
    (source/'input.mp4').write_bytes(b'source');(cache/'cached.mp4').write_bytes(b'cache');(root/'prior.mp4').write_bytes(b'prior')
    with ExitStack() as stack:
        repo=JobRepository(tmp_path/'jobs.db');stack.callback(repo.close)
        job=repo.submit('one',CompositionPlan.parse(empty_plan),0,outputs=output(root));job=repo.claim(job);job=repo.worker_transition(job,job.lease_token,'validating')
        owner=stack.enter_context(CoordinatorOwnership(repo));live=stack.enter_context(PublicationSession(repo,owner,job,cache_roots=(cache,)))
        yield live,source,root,cache


def test_manifest_and_configured_cache_are_automatic_scan_exclusions(session):
    live,source,root,cache=session
    result=live.scan_sources(source)
    assert result.status=='COMPLETE' and result.paths==(source/'input.mp4',)
    assert (root/'prior.mp4').read_bytes()==b'prior' and (cache/'cached.mp4').read_bytes()==b'cache'


def test_final_created_after_admission_refused_before_stage(session):
    live,source,root,cache=session
    (root/'final.srt').write_bytes(RAW)
    with pytest.raises(PublicationConflict):live.stage_subtitle('subtitle',RAW)
    assert not list(root.glob('.fonesi-stage-*'))


def test_snapshot_source_change_after_hash_prevents_link(tmp_path,empty_plan,monkeypatch):
    root=tmp_path/'output';root.mkdir();source=tmp_path/'source.bin';source.write_bytes(b'original')
    example=json.loads(Path('docs/schemas/examples/multi-stream-composition.json').read_text())
    empty_plan['assets']=[example['assets'][0]]
    empty_plan['assets'][0]['path_ref'].update(base='absolute',path=str(source))
    with ExitStack() as stack:
        repo=JobRepository(tmp_path/'jobs.db');stack.callback(repo.close)
        job=repo.submit('one',CompositionPlan.parse(empty_plan),0,outputs=output(root));job=repo.claim(job);job=repo.worker_transition(job,job.lease_token,'validating')
        owner=stack.enter_context(CoordinatorOwnership(repo));live=stack.enter_context(PublicationSession(repo,owner,job))
        live.stage_subtitle('subtitle',RAW);live.prepare();live.claim()
        dest=live._destinations[str(root)];verify=dest._verify
        def change(*args,**kwargs):
            verify(*args,**kwargs);source.write_bytes(b'changed size and content')
        monkeypatch.setattr(dest,'_verify',change)
        with pytest.raises(PublicationUnknown):live.publish_member('subtitle')
        assert not (root/'final.srt').exists()
        assert repo.db.execute('SELECT count(*) FROM artifacts').fetchone()[0]==0


def test_named_and_descriptor_timestamp_precision_separate_but_mutation_rejected(tmp_path,monkeypatch):
    from types import SimpleNamespace
    import fonesi_edit.jobs.admission as module
    root=tmp_path/'out';root.mkdir();source=tmp_path/'input';source.write_bytes(b'original')
    real=os.fstat
    def coarse(fd):
        info=real(fd)
        if not __import__('stat').S_ISREG(info.st_mode):return info
        values={name:getattr(info,name) for name in dir(info) if name.startswith('st_')}
        values['st_mtime_ns']+=1;values['st_ctime_ns']+=1
        return SimpleNamespace(**values)
    monkeypatch.setattr(module.os,'fstat',coarse)
    with Destination(root) as dest,NamespaceAdmission({'assets':[source_record(source)],'fonts':[]},{str(root):dest},output(root)) as admission:
        admission.guard() # Same physical object, different API timestamp precision.
        source.write_bytes(b'changed size and content')
        with pytest.raises(PublicationUnknown):admission.guard()
