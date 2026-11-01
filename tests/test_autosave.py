from dataclasses import replace
import pytest
from fonesi_edit.domain.composition import CompositionPlan
from fonesi_edit.storage.projects import Project, ProjectStore, ConflictError, save_project_file, load_project_file
from fonesi_edit.storage.autosave import (CompletedCommand, prepare_open, ReconciliationRequired,
                                        RelinkRequired)


def model(plan, name='original'):
    return Project('00000000-0000-4000-8000-000000000002', name, CompositionPlan.parse(plan))


def edit(project):
    plan = project.plan.to_dict()
    plan['revision'] += 1
    return replace(project, name='edited', plan=CompositionPlan.parse(plan))


@pytest.fixture
def opened(tmp_path, empty_plan):
    project = model(empty_plan)
    path = tmp_path/'project.json'
    save_project_file(path, project)
    with ProjectStore(tmp_path/'local.db') as store:
        yield store, path, project, prepare_open(store, path).choose(store, 'file')


def test_completed_autosave_recovery_explicit_cancel_and_save(opened):
    store, path, original, session = opened
    changed = edit(original)
    session.commit(CompletedCommand(changed, 0))
    assert load_project_file(path)[0].name == 'original'
    offer = prepare_open(store, path)
    assert offer.differs
    before = store.load(original.id)
    assert offer.choose(store, 'cancel') is None
    assert store.load(original.id).version == before.version
    recovered = offer.choose(store, 'recovery')
    assert recovered.project.to_json() == changed.to_json()
    recovered.save()
    assert load_project_file(path)[0].to_json() == changed.to_json()
    assert list(path.parent.glob('project.json.backup-*'))


def test_open_and_choose_file_do_not_autosave(opened):
    store, path, original, session = opened
    with pytest.raises(KeyError): store.load(original.id)
    store.save(edit(original))
    chosen = prepare_open(store, path).choose(store, 'file')
    assert chosen.project.name == 'original'
    assert store.load(original.id).project.name == 'edited'


def test_stale_memory_and_database_versions_refuse(opened):
    store, path, original, session = opened
    other = prepare_open(store, path).choose(store, 'file')
    session.commit(CompletedCommand(edit(original), 0))
    with pytest.raises(ConflictError): session.commit(CompletedCommand(edit(original), 0))
    with pytest.raises(ConflictError): other.commit(CompletedCommand(edit(original), 0))
    assert other.project == original and not other.reconciliation_required


def test_stale_recovery_offer_refuses(opened):
    store, path, original, session = opened
    offer = prepare_open(store, path)
    store.save(edit(original))
    with pytest.raises(ConflictError): offer.choose(store, 'file')


def test_changed_file_offer_and_save_refuse(opened):
    store, path, original, session = opened
    offer = prepare_open(store, path)
    save_project_file(path, edit(original), expected_digest=offer.file_digest)
    with pytest.raises(ConflictError): offer.choose(store, 'file')
    with pytest.raises(ConflictError): session.save()
    assert not session.reconciliation_required


@pytest.mark.parametrize('after_commit', [False, True])
def test_autosave_unknown_outcome_preserves_model_and_blocks_replay(opened, monkeypatch, after_commit):
    store, path, original, session = opened
    real = store.save
    def fail(*args, **kwargs):
        if after_commit: real(*args, **kwargs)
        raise OSError('injected uncertain return')
    monkeypatch.setattr(store, 'save', fail)
    with pytest.raises(ReconciliationRequired): session.commit(CompletedCommand(edit(original), 0))
    assert session.project == original
    with pytest.raises(ReconciliationRequired): session.save()
    with pytest.raises(ReconciliationRequired): session.commit(CompletedCommand(edit(original), 0))
    assert session.reconciliation_required


def test_file_postpublication_failure_unknown_no_replay(opened, monkeypatch):
    import fonesi_edit.storage.autosave as module
    store, path, original, session = opened
    session.commit(CompletedCommand(edit(original), 0))
    real = module.save_project_file
    def fail(*args, **kwargs):
        real(*args, **kwargs)
        raise OSError('response lost after save')
    monkeypatch.setattr(module, 'save_project_file', fail)
    with pytest.raises(ReconciliationRequired): session.save()
    assert load_project_file(path)[0].name == 'edited'
    assert session.project.name == 'edited'
    with pytest.raises(ReconciliationRequired): session.save()


def test_save_as_never_overwrites_unobserved_target(opened, tmp_path):
    store, path, original, session = opened
    target = tmp_path/'other.json'
    target.write_bytes(b'foreign')
    with pytest.raises(ConflictError): session.save(target)
    assert target.read_bytes() == b'foreign'
    target.unlink()
    session.save(target)
    assert load_project_file(target)[0].to_json() == original.to_json()


def test_relative_recovery_and_save_elsewhere_require_relink(tmp_path, multi_plan):
    project = model(multi_plan)
    path = tmp_path/'project.json'
    save_project_file(path, project)
    with ProjectStore(tmp_path/'local.db') as store:
        session = prepare_open(store, path).choose(store, 'file')
        session.commit(CompletedCommand(edit(project), project.plan.to_dict()['revision']))
        with pytest.raises(RelinkRequired): session.save(tmp_path/'elsewhere'/'p.json')
        assert not (tmp_path/'elsewhere').exists()
        recovered=prepare_open(store, path).choose(store, 'recovery')
        assert all(item['path_ref']['base']=='absolute' for key in ('assets','fonts') for item in recovered.project.plan.to_dict()[key])
        session.save()  # Known same base is still usable.


def test_noncommand_and_wrong_identity_refused_without_writes(opened):
    store, path, original, session = opened
    with pytest.raises(Exception, match='completed typed'): session.commit(edit(original))
    wrong = replace(edit(original), id='00000000-0000-4000-8000-000000000003')
    with pytest.raises(ConflictError): session.commit(CompletedCommand(wrong, 0))
    with pytest.raises(KeyError): store.load(original.id)


def test_explicit_save_refuses_changed_local_observation(opened):
    store, path, original, session = opened
    old_bytes = path.read_bytes()
    store.save(edit(original))
    with pytest.raises(ConflictError): session.save()
    assert path.read_bytes() == old_bytes


@pytest.mark.parametrize('error', [PermissionError, BlockingIOError])
def test_actual_postpublish_permission_failure_is_unknown(opened, monkeypatch, error):
    import fonesi_edit.storage.autosave as module
    store, path, original, session = opened
    session.commit(CompletedCommand(edit(original), 0))
    real = module.save_project_file
    calls=[]
    def fault(point):
        if point=='after_publish':raise error('injected after native replacement')
    def save(*args,**kwargs):
        calls.append(1)
        return real(*args,**kwargs,fault=fault)
    monkeypatch.setattr(module,'save_project_file',save)
    with pytest.raises(ReconciliationRequired):session.save()
    assert load_project_file(path)[0].name=='edited'
    assert session.reconciliation_required
    with pytest.raises(ReconciliationRequired):session.save()
    assert calls==[1]
