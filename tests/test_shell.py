import os
os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')
from PySide6.QtWidgets import QApplication
import pytest
from fonesi_edit.ui.shell import MainWindow, AREAS
from fonesi_edit.storage.projects import ProjectStore, Project, save_project_file
from fonesi_edit.domain.composition import CompositionPlan
from fonesi_edit.__main__ import main
import uuid

@pytest.fixture(scope='module')
def app():
    return QApplication.instance() or QApplication([])

def test_eight_real_empty_areas_and_shared_project(app, tmp_path, empty_plan):
    with ProjectStore(tmp_path/'user'/'projects.sqlite3') as store:
        window = MainWindow(store)
        assert window.navigation.count() == window.pages.count() == len(AREAS) == 8
        assert window.project is None
        project = Project(str(uuid.uuid4()), 'Dự án 中文', CompositionPlan.parse(empty_plan))
        path = tmp_path/'dự án.json'
        save_project_file(path, project)
        assert window.open_project(path) == project
        for i in range(8):
            window.navigation.setCurrentRow(i)
            assert window.pages.currentIndex() == i
            assert window.project == project
        broken = tmp_path/'bad.json'; broken.write_text('{}')
        with pytest.raises(RuntimeError): window.open_project(broken)
        assert window.project == project
        window.close()

def test_headless_validation(tmp_path, empty_plan, capsys):
    import json
    path = tmp_path/'plan.json'; path.write_text(json.dumps(empty_plan))
    assert main(['--validate-plan', str(path)]) == 0
    assert 'No media/render verification' in capsys.readouterr().out
    path.write_text('{}')
    assert main(['--validate-plan', str(path)]) == 2
    assert not list(tmp_path.glob('*.sqlite3'))

def test_oversized_open_preserves_current_and_cli_bounded(app,tmp_path,empty_plan,monkeypatch):
    import fonesi_edit.storage.projects as storage
    import fonesi_edit.domain.composition as composition
    import json
    with ProjectStore(tmp_path/'db') as store:
        window=MainWindow(store)
        project=Project(str(uuid.uuid4()),'Original',CompositionPlan.parse(empty_plan))
        valid=tmp_path/'valid.json';save_project_file(valid,project);window.open_project(valid)
        oversized=tmp_path/'oversized.json';oversized.write_bytes(b'x'*100)
        monkeypatch.setattr(storage,'MAX_PROJECT_BYTES',10)
        with pytest.raises(RuntimeError,match='exceeds'):window.open_project(oversized)
        assert window.project==project
        monkeypatch.setattr(composition,'MAX_PLAN_BYTES',10)
        assert main(['--validate-plan',str(oversized)])==2
        window.close()
