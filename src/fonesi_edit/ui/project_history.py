"""Bounded session-local undo/redo shared by Editor and Timeline project commands."""
from copy import deepcopy
from dataclasses import dataclass

from PySide6.QtCore import QObject, Signal

from fonesi_edit.domain.composition import CompositionPlan
from fonesi_edit.storage.autosave import CompletedCommand


@dataclass(frozen=True)
class ProjectHistoryEntry:
    before: dict
    after: dict
    label: str


class ProjectCommandHistory(QObject):
    """One CAS-guarded history for every currently integrated project editor.

    History is deliberately session-local. It never rewinds revisions, serializes
    snapshots into project files, retries unknown commits, or edits source media.
    """

    changed = Signal()

    def __init__(self, get_session, parent=None, *, max_entries=200):
        super().__init__(parent)
        if not callable(get_session):
            raise TypeError("A session provider is required")
        if type(max_entries) is not int or not 1 <= max_entries <= 1000:
            raise ValueError("History bound must be an integer from 1 to 1000")
        self.get_session = get_session
        self.max_entries = max_entries
        self.undo_stack = []
        self.redo_stack = []
        self._session = None
        self._revision = None

    def _clear(self, session=None):
        self.undo_stack.clear()
        self.redo_stack.clear()
        self._session = session
        self._revision = None if session is None else session.revision
        self.changed.emit()

    def sync(self):
        """Invalidate snapshots after project replacement or an untracked revision."""
        session = self.get_session()
        if session is None:
            if self._session is not None or self.undo_stack or self.redo_stack:
                self._clear()
            return
        if self._session is None:
            self._session = session
            self._revision = session.revision
            return
        if self._session is not session or self._revision != session.revision:
            self._clear(session)

    def record(self, before, session, expected_revision, label):
        """Record only after the exact completed command has committed."""
        if (session is None or self.get_session() is not session
                or session.reconciliation_required
                or type(expected_revision) is not int
                or session.revision != expected_revision + 1):
            self._clear(session if self.get_session() is session else None)
            return False
        if self._session is not session or self._revision != expected_revision:
            self._clear(session)
        after = session.project.plan.to_dict()
        self.undo_stack.append(ProjectHistoryEntry(
            deepcopy(before), deepcopy(after), str(label)))
        if len(self.undo_stack) > self.max_entries:
            del self.undo_stack[:len(self.undo_stack) - self.max_entries]
        self.redo_stack.clear()
        self._session = session
        self._revision = session.revision
        self.changed.emit()
        return True

    def _restore(self, snapshot, session):
        expected = session.revision
        restored = deepcopy(snapshot)
        restored["revision"] = expected + 1
        restored["provenance"]["project_revision"] = expected + 1
        plan = CompositionPlan.parse(restored)
        session.commit(CompletedCommand(
            session.project.with_plan(plan), expected))

    def undo(self):
        self.sync()
        session = self.get_session()
        if (session is None or session.reconciliation_required
                or not self.undo_stack):
            return False
        entry = self.undo_stack[-1]
        try:
            self._restore(entry.before, session)
        except Exception:
            # The commit outcome may be unknown. Never replay or retain stale history.
            self._clear(session if self.get_session() is session else None)
            return False
        self.undo_stack.pop()
        self.redo_stack.append(entry)
        self._session = session
        self._revision = session.revision
        self.changed.emit()
        return True

    def redo(self):
        self.sync()
        session = self.get_session()
        if (session is None or session.reconciliation_required
                or not self.redo_stack):
            return False
        entry = self.redo_stack[-1]
        try:
            self._restore(entry.after, session)
        except Exception:
            self._clear(session if self.get_session() is session else None)
            return False
        self.redo_stack.pop()
        self.undo_stack.append(entry)
        self._session = session
        self._revision = session.revision
        self.changed.emit()
        return True

    def can_undo(self):
        self.sync()
        session = self.get_session()
        return bool(session is not None and not session.reconciliation_required
                    and self.undo_stack)

    def can_redo(self):
        self.sync()
        session = self.get_session()
        return bool(session is not None and not session.reconciliation_required
                    and self.redo_stack)
