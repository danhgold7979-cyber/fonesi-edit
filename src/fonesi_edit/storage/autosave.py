"""Explicit project recovery and completed-command persistence (no UI/timer)."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path, PureWindowsPath
from typing import Literal
from fonesi_edit.domain.composition import CompositionPlan

from .projects import (ConflictError, Project, ProjectStore, StorageError,
                       StoredProject, load_project_file, save_project_file)


class ReconciliationRequired(StorageError):
    """A write may have completed; this session cannot issue another write."""


class RelinkRequired(StorageError):
    """The original base for project-relative media/fonts is not established."""


def _relative(project: Project) -> bool:
    plan = project.plan.to_dict()
    return any(item['path_ref']['base'] == 'project'
               for key in ('assets', 'fonts') for item in plan[key])


def _observation(store: ProjectStore, project_id: str) -> StoredProject | None:
    try:
        return store.load(project_id)
    except KeyError:
        return None


def _same(left: StoredProject | None, right: StoredProject | None) -> bool:
    if left is None or right is None:
        return left is right
    return (left.version == right.version and left.origin_base == right.origin_base and
            left.project.to_json() == right.project.to_json())


@dataclass(frozen=True)
class CompletedCommand:
    """Final validated model only; previews/gestures must not submit this object."""
    project: Project
    expected_revision: int

    def __post_init__(self):
        if not isinstance(self.project, Project):
            raise StorageError('Completed command requires a typed Project')
        if type(self.expected_revision) is not int or self.expected_revision < 0:
            raise StorageError('Invalid command revision')


@dataclass(frozen=True)
class RecoveryOffer:
    path: Path
    file_project: Project
    file_digest: str
    local: StoredProject | None

    @property
    def differs(self) -> bool:
        return self.local is not None and (
            self.local.project.to_json() != self.file_project.to_json() or
            (_relative(self.local.project) and self.local.origin_base is not None and
             Path(self.local.origin_base)!=self.path.parent))

    def choose(self, store: ProjectStore,
               choice: Literal['file', 'recovery', 'cancel']) -> ProjectSession | None:
        # Cancellation deliberately does not even re-read disk/SQLite.
        if choice == 'cancel':
            return None
        if choice not in ('file', 'recovery'):
            raise StorageError('Explicit file/recovery/cancel choice required')
        project, digest = load_project_file(self.path)
        if digest != self.file_digest or project.to_json() != self.file_project.to_json():
            raise ConflictError('Project file changed while recovery choice was open')
        if not _same(_observation(store, project.id), self.local):
            raise ConflictError('Local recovery observation changed; reopen the choice')
        selected = project
        if choice == 'recovery':
            if self.local is None:
                raise StorageError('No local recovery observation exists')
            selected = self.local.project
            # Legacy rows lack an origin. Never infer it from a newly chosen file.
            if _relative(selected):
                if self.local.origin_base is None:
                    raise RelinkRequired('Recovery needs explicit original asset/font base or relink')
                plan=selected.plan.to_dict()
                for collection in ('assets','fonts'):
                    for item in plan[collection]:
                        ref=item['path_ref']
                        if ref['base']=='project':
                            value=ref['path'];windows=PureWindowsPath(value)
                            if '\x00' in value or Path(value).is_absolute() or windows.drive or windows.root:
                                raise RelinkRequired('Project-relative reference has ambiguous absolute/drive syntax')
                            ref['path']=str(Path(self.local.origin_base)/value)
                            ref['base']='absolute'
                selected=Project(selected.id,selected.name,CompositionPlan.parse(plan))
        return ProjectSession(store, selected, self.path, digest,
                              self.local)


def prepare_open(store: ProjectStore, path: Path | str) -> RecoveryOffer:
    path = Path(path).absolute()
    project, digest = load_project_file(path)
    return RecoveryOffer(path, project, digest, _observation(store, project.id))


class ProjectSession:
    """Single-thread model owner; store lifetime belongs to caller.

    Open through prepare_open().choose(). Revision is the CompositionPlan revision;
    every completed edit must advance it exactly once. No callbacks run during commit.
    """
    def __init__(self, store: ProjectStore, project: Project, path: Path,
                 digest: str, observation: StoredProject | None):
        self._store = store
        self._project = project
        self._path = path
        self._digest = digest
        self._observation = observation
        self._store_version = None if observation is None else observation.version
        self._uncertain = False

    @property
    def project(self) -> Project:
        return self._project

    @property
    def project_base(self) -> Path:
        return self._path.parent

    @property
    def revision(self) -> int:
        return self._project.plan.to_dict()['revision']

    @property
    def reconciliation_required(self) -> bool:
        return self._uncertain

    def _ready(self):
        if self._uncertain:
            raise ReconciliationRequired('Prior write outcome unknown; inspect and reopen explicitly')

    def commit(self, command: CompletedCommand) -> Project:
        self._ready()
        if not isinstance(command, CompletedCommand):
            raise StorageError('Only completed typed commands may autosave')
        candidate = Project.parse(command.project.to_json())
        old = self._project.plan.to_dict()
        new = candidate.plan.to_dict()
        if (command.expected_revision != self.revision or candidate.id != self._project.id
                or new['id'] != old['id'] or new['revision'] != self.revision + 1):
            raise ConflictError('Command identity/revision is stale or not the next completed edit')
        try:
            stored = self._store.save(candidate, expected_version=self._store_version,
                                      origin_base=self._path.parent)
        except ConflictError:
            raise  # Repository CAS refusal is known to occur before mutation.
        except BaseException as exc:
            self._uncertain = True
            raise ReconciliationRequired('Autosave outcome unknown; no command replay') from exc
        self._project = stored.project
        self._store_version = stored.version
        self._observation = stored
        return self._project

    def save(self, path: Path | str | None = None) -> str:
        self._ready()
        if not _same(_observation(self._store, self._project.id), self._observation):
            raise ConflictError('Local autosave changed; reopen before explicit save')
        target = self._path if path is None else Path(path).absolute()
        if target.parent.resolve() != self._path.parent.resolve() and _relative(self._project):
            raise RelinkRequired('Save elsewhere would change asset/font base; relink first')
        # Only the opened/current path has explicit matched-overwrite authority.
        expected = self._digest if target == self._path else None
        try:
            digest = save_project_file(target, self._project, expected_digest=expected)
        except ConflictError:
            raise
        except BaseException as exc:
            self._uncertain = True
            raise ReconciliationRequired('File save outcome unknown; inspect file before reopening') from exc
        self._path, self._digest = target, digest
        return digest
