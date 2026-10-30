"""Cooperative Qt worker with sanitized error reporting."""

import threading

from PySide6.QtCore import QThread, Signal


class Worker(QThread):
    result = Signal(object)
    failure = Signal(str)

    def __init__(self, operation):
        super().__init__()
        self.operation = operation
        self.cancel = threading.Event()

    def run(self):
        try:
            self.result.emit(self.operation(self.cancel))
        except Exception as exc:  # noqa: BLE001 - Qt worker boundary reports sanitized failure, never success.
            # No raw exception/path/provider data in the diagnostic status.
            code = (
                str(exc)
                if isinstance(exc, ValueError) and str(exc).replace("_", "").isalnum()
                else type(exc).__name__
            )
            self.failure.emit(code[:100])
