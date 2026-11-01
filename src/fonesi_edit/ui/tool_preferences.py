"""Worker-local preference IO; no executable discovery or trust grant."""
from PySide6.QtCore import QThread
from fonesi_edit.dependencies.preferences import load_preferences, save_preferences, PreferencesUnknown

class PreferenceWorker(QThread):
    def __init__(self,path,*,value=None,expected=None,parent=None):
        super().__init__(parent);self.path=path;self.value=value;self.expected=expected
        self.result=None;self.failed=False;self.unknown=False
    def run(self):
        try:
            if self.value is None:self.result=load_preferences(self.path,cancel=self.isInterruptionRequested)
            else:self.result=save_preferences(self.path,self.value,self.expected,cancel=self.isInterruptionRequested)
        except PreferencesUnknown:self.failed=True;self.unknown=True
        except Exception:self.failed=True # no arbitrary paths/SQLite text in UI diagnostics


def reconciles(observed, expected, intended):
    """Explicit reload can resolve only this exact old/new owned snapshot."""
    return (expected.token is not None and observed.token==expected.token and
        ((observed.version==expected.version and observed.value==expected.value) or
         (observed.version==expected.version+1 and observed.value==intended)))
