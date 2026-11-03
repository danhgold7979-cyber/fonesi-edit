"""Read-only last-known browser/account metadata view; never launches Chrome or reads secrets."""
from datetime import datetime, timezone
from pathlib import Path

from PySide6.QtCore import QThread, Signal, QTimer, Qt
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTableWidget, QTableWidgetItem, QAbstractItemView,
)

from fonesi_edit.accounts.store import AccountStore, AccountStoreError


def _utc(value):
    if type(value) is not int or value < 0:
        return "Chưa ghi"
    try:
        return datetime.fromtimestamp(value, timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    except (OverflowError, OSError, ValueError):
        return "Timestamp không hợp lệ"


class AccountMetadataWorker(QThread):
    """One bounded immutable snapshot of an already-existing owned account store."""
    def __init__(self, path, parent=None):
        super().__init__(parent)
        self.path = Path(path)
        self.result = None
        self.failed = False
        self.canceled = False

    def run(self):
        try:
            if self.isInterruptionRequested():
                self.canceled = True
                return
            self.result = AccountStore.read_snapshot(
                self.path, profile_limit=100, binding_limit=200
            )
            if self.isInterruptionRequested():
                self.result = None
                self.canceled = True
        except AccountStoreError:
            self.failed = True
        except BaseException:
            # Never surface SQLite paths, payloads or exception details in the UI.
            self.failed = True


class AccountMetadataPanel(QWidget):
    """Truthful read-only view of saved metadata; no live browser/auth assertions."""
    idle = Signal()

    def __init__(self, store_path, parent=None):
        super().__init__(parent)
        self.store_path = Path(store_path).absolute()
        self.worker = None
        self.stopping = False
        self.first_open_attempted = False

        layout = QVBoxLayout(self)
        notice = QLabel(
            "Hồ sơ và tài khoản bên dưới chỉ là metadata/trạng thái đã ghi nhận lần cuối. "
            "Màn hình này KHÔNG mở Chrome, không đọc cookie/mật khẩu, không xác minh phiên đăng nhập "
            "hoặc connector đang hoạt động và không thay đổi hồ sơ/tài khoản."
        )
        notice.setWordWrap(True)
        layout.addWidget(notice)

        actions = QHBoxLayout()
        self.refresh_button = QPushButton("Làm mới snapshot metadata")
        self.refresh_button.clicked.connect(self.refresh)
        actions.addWidget(self.refresh_button)
        actions.addStretch()
        layout.addLayout(actions)

        self.status = QLabel("Chưa đọc snapshot. Mở trang này để đọc metadata đã lưu nếu có.")
        self.status.setWordWrap(True)
        layout.addWidget(self.status)

        layout.addWidget(QLabel("Hồ sơ trình duyệt — trạng thái đã ghi nhận"))
        self.profile_table = QTableWidget(0, 5)
        self.profile_table.setHorizontalHeaderLabels(
            ["Tên hồ sơ", "Profile ID", "Sở hữu", "Browser state", "Ghi nhận (UTC)"]
        )
        self._configure_table(self.profile_table)
        layout.addWidget(self.profile_table)

        layout.addWidget(QLabel("Binding nền tảng — website/bridge là quan sát độc lập"))
        self.binding_table = QTableWidget(0, 7)
        self.binding_table.setHorizontalHeaderLabels(
            ["Nền tảng", "Danh tính", "Hồ sơ", "Website (last-known)",
             "Bridge (last-known)", "Mặc định", "Ghi nhận (UTC)"]
        )
        self._configure_table(self.binding_table)
        layout.addWidget(self.binding_table)

        self.update_actions()

    @staticmethod
    def _configure_table(table):
        table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        table.setAlternatingRowColors(True)
        table.setWordWrap(False)
        table.setMinimumHeight(130)

    @property
    def busy(self):
        return self.worker is not None

    def update_actions(self):
        self.refresh_button.setEnabled(not self.busy and not self.stopping)

    def first_open(self):
        if self.first_open_attempted or self.stopping:
            return
        self.first_open_attempted = True
        self.refresh()

    def refresh(self):
        if self.busy or self.stopping:
            return
        worker = AccountMetadataWorker(self.store_path, self)
        self.worker = worker
        worker.finished.connect(lambda: self._finished(worker))
        self.status.setText(
            "Đang đọc snapshot chỉ-đọc; không tạo store nếu chưa có và không khởi chạy Chrome."
        )
        self.update_actions()
        worker.start()

    def _finished(self, worker):
        if self.worker is not worker:
            return
        if not worker.wait(0):
            QTimer.singleShot(10, lambda: self._finished(worker))
            return

        if self.stopping or worker.canceled:
            self.status.setText("Đã dừng yêu cầu đọc snapshot; dữ liệu không bị thay đổi.")
        elif worker.failed:
            self._clear_tables()
            self.status.setText(
                "Không thể đọc account metadata store (không thuộc sở hữu, đang bận, sai schema "
                "hoặc dữ liệu không hợp lệ). Store được giữ nguyên; không tự tạo, migrate hay reset."
            )
        elif worker.result is None:
            self._clear_tables()
            self.status.setText(
                "Chưa có account metadata store. Không tạo database/receipt và không tự khởi tạo hồ sơ."
            )
        else:
            self._populate(worker.result)

        self.worker = None
        worker.deleteLater()
        self.update_actions()
        self.idle.emit()

    def _clear_tables(self):
        self.profile_table.setRowCount(0)
        self.binding_table.setRowCount(0)

    @staticmethod
    def _set_cell(table, row, column, value):
        item = QTableWidgetItem(str(value))
        item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)
        table.setItem(row, column, item)

    def _populate(self, snapshot):
        self.profile_table.setRowCount(len(snapshot.profiles))
        profile_labels = {}
        for row, observation in enumerate(snapshot.profiles):
            profile = observation.value
            profile_labels[profile.id] = profile.label
            values = (
                profile.label, profile.id, profile.ownership,
                profile.state.value, _utc(observation.observed_at),
            )
            for column, value in enumerate(values):
                self._set_cell(self.profile_table, row, column, value)

        defaults = dict(snapshot.defaults)
        self.binding_table.setRowCount(len(snapshot.bindings))
        for row, observation in enumerate(snapshot.bindings):
            binding = observation.value
            identity = binding.display_name or binding.identity or "Chưa xác minh danh tính"
            profile_label = profile_labels.get(binding.profile_id, binding.profile_id)
            web = f"{binding.web.value} · {_utc(binding.web_checked_at)}"
            bridge = f"{binding.bridge.value} · {_utc(binding.bridge_checked_at)}"
            values = (
                binding.platform, identity, profile_label, web, bridge,
                "Có" if defaults.get(binding.platform) == binding.id else "Không",
                _utc(observation.observed_at),
            )
            for column, value in enumerate(values):
                self._set_cell(self.binding_table, row, column, value)

        profile_count = f"{len(snapshot.profiles)}/{snapshot.profile_total}"
        binding_count = f"{len(snapshot.bindings)}/{snapshot.binding_total}"
        capped = (
            " (đã chạm giới hạn hiển thị)" if
            snapshot.profile_total > len(snapshot.profiles) or
            snapshot.binding_total > len(snapshot.bindings) else ""
        )
        self.status.setText(
            f"Snapshot chỉ-đọc hoàn tất: {profile_count} hồ sơ, {binding_count} binding{capped}. "
            "Website, bridge và browser state là last-known observations, KHÔNG phải kiểm tra live "
            "hoặc bằng chứng có thể dùng phiên Chrome."
        )

    def request_stop(self):
        self.stopping = True
        if self.worker is not None:
            self.worker.requestInterruption()
            self.status.setText("Đã yêu cầu dừng; đang chờ worker đọc store kết thúc.")
        self.update_actions()

    def closeEvent(self, event):
        self.request_stop()
        if self.busy:
            event.ignore()
        else:
            super().closeEvent(event)
