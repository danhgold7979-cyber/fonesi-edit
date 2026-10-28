"""Desktop application and worker entry. External acceptance remains explicit."""
from argparse import ArgumentParser
from copy import deepcopy
from pathlib import Path
from uuid import uuid4
import json
import os
import sys
import tempfile
import time

from PySide6.QtCore import Qt,QTimer,QUrl
from PySide6.QtGui import QAction,QKeySequence,QDesktopServices
from PySide6.QtWidgets import (QApplication,QMainWindow,QWidget,QVBoxLayout,QHBoxLayout,QTabWidget,QLabel,QPushButton,
    QProgressBar,QFileDialog,QInputDialog,QListWidget,QLineEdit,QPlainTextEdit,QTextEdit,QSystemTrayIcon,QMenu,QStyle,
    QAbstractSpinBox,QComboBox,QAbstractItemView,QAbstractSlider,QAbstractButton)

from .domain import Composition,atomic_json,canonical
from .paths import data_directory
from .storage import Store
from .jobs import Scheduler
from .automation import Automation,metrics,recommended_parallel
from .cache import evict_proxy_cache
from .prototypes.tools import configure_tools
from .prototypes.media import extract_frame,probe
from .render import reference_frame,render_composition
from .ui.tasks import Task
from .ui.editor import Editor
from .ui.pages import DownloadsPage,SubtitlesPage,BatchPage,MatrixPage,QueuePage,SettingsPage


_TEXT_EDIT_WIDGETS = (QLineEdit, QPlainTextEdit, QTextEdit)
_INTERACTIVE_WIDGETS = (QAbstractSpinBox, QComboBox, QAbstractItemView, QAbstractSlider, QAbstractButton)
_EDITOR_SHORTCUT_ACTIONS = frozenset({
    "Undo", "Redo", "Nhân bản", "Split", "Đưa vào hàng đợi", "Phát/dừng",
    "Marker", "Đặt In", "Đặt Out", "Nhóm layer", "Bỏ nhóm", "Khóa layer",
})


def shortcut_focus_policy(focused):
    """Classify focus while respecting composite Qt controls such as spin boxes."""
    current = focused
    # QAbstractSpinBox embeds a QLineEdit named qt_spinbox_lineedit. That child
    # is an editing surface internally, but keyboard shortcuts must yield to
    # the owning spin box rather than being routed to a text editor.
    if isinstance(current, QLineEdit) and current.objectName() == "qt_spinbox_lineedit":
        parent = current.parentWidget()
        while parent is not None:
            if isinstance(parent, QAbstractSpinBox):
                return "control", parent
            parent = parent.parentWidget() if hasattr(parent, "parentWidget") else None
    while current is not None:
        if isinstance(current, _TEXT_EDIT_WIDGETS):
            return "text", current
        if isinstance(current, _INTERACTIVE_WIDGETS):
            return "control", current
        current = current.parentWidget() if hasattr(current, "parentWidget") else None
    return "global", None


def parse_shortcut_remap_json(text, current):
    """Parse user-edited shortcut JSON and validate it without mutating current state."""
    try:
        changes = json.loads(text)
    except (json.JSONDecodeError, TypeError) as exc:
        raise ValueError("JSON phím tắt không hợp lệ") from exc
    return normalize_shortcut_remap(changes, current)


def normalize_shortcut_remap(changes, current):
    """Merge partial shortcut edits, normalize them, and reject invalid/conflicting keys."""
    if not isinstance(changes, dict) or set(changes) - set(current):
        raise ValueError("Tên thao tác không hợp lệ")
    merged = dict(current)
    for name, value in changes.items():
        if not isinstance(value, str):
            raise ValueError(f"Phím tắt của {name} phải là chuỗi")
        if not value.strip():
            merged[name] = ""
            continue
        sequence = QKeySequence.fromString(value.strip(), QKeySequence.SequenceFormat.PortableText)
        normalized = sequence.toString(QKeySequence.SequenceFormat.PortableText)
        if sequence.isEmpty() or not normalized:
            raise ValueError(f"Phím tắt không hợp lệ: {name}")
        if sequence.count() != 1:
            raise ValueError(f"Chỉ hỗ trợ một tổ hợp phím cho {name}")
        merged[name] = normalized
    owners = {}
    for name, value in merged.items():
        if not value:
            continue
        sequence = QKeySequence.fromString(value, QKeySequence.SequenceFormat.PortableText)
        normalized = sequence.toString(QKeySequence.SequenceFormat.PortableText)
        if normalized in owners:
            raise ValueError(f"Phím tắt trùng nhau: {owners[normalized]} và {name}")
        owners[normalized] = name
    return merged


class MainWindow(QMainWindow):
    def __init__(self,data=None):
        super().__init__();self.setWindowTitle('Fonesi Edit • Desktop');self.resize(1500,1000)
        self.data=Path(data or data_directory());self.data.mkdir(parents=True,exist_ok=True)
        self.store=Store(self.data/'state.db');configure_tools(self.store.setting('tool_paths',{}))
        if os.name=='nt':
            from .browser import protect
            with self.store.connect() as conn:
                for row in conn.execute("SELECT key,value FROM secrets WHERE key LIKE 'api:%'"):
                    try:os.environ[row['key'][4:]]=protect(bytes(row['value']),decrypt=True).decode()
                    except PermissionError:pass
        self.workspace=tempfile.TemporaryDirectory(prefix='fonesi-desktop-');self.tasks=[];self.pending_tasks=[];self.failures=[];self.force_close=False;self._shutdown=False
        self._cache_cleanup_busy=False;self._last_cache_cleanup=time.monotonic()
        self.project_id=None;self.project_file=None;self._restoring=False
        self.scheduler=Scheduler(self.store,self.store.setting('parallel',2));self.automation=Automation(self.store)
        self.status=QLabel('Sẵn sàng • Nguồn live, tài khoản, Windows và GPU có trạng thái kiểm chứng riêng.');self.status.setWordWrap(True)
        root=QWidget();layout=QVBoxLayout(root)
        title=QLabel('FONESI EDIT');title.setObjectName('brand');layout.addWidget(title)
        toolbar=QHBoxLayout();layout.addLayout(toolbar)
        for label,callback in [('Project mới',self.new_project),('Mở project',self.open_project),('Lưu project',self.save_project),('Lưu preset',self.save_preset),('Nạp preset',self.load_preset),('Liên kết lại media',self.relink)]:
            button=QPushButton(label);button.clicked.connect(self.guard(callback));toolbar.addWidget(button)
        self.nav=QTabWidget();layout.addWidget(self.nav,1)
        overview=QWidget();ov=QVBoxLayout(overview);self.machine=QLabel();self.machine.setWordWrap(True);ov.addWidget(self.machine)
        self.overview=QListWidget();ov.addWidget(self.overview,1);ov.addWidget(QLabel('Các thao tác auto chạy theo preset. Thiếu API/tài khoản không chặn edit media cục bộ.'))
        self.editor=Editor(self);self.downloads=DownloadsPage(self);self.subtitles=SubtitlesPage(self);self.batch=BatchPage(self);self.matrix=MatrixPage(self);self.queue=QueuePage(self);self.settings=SettingsPage(self)
        for page,label in [(overview,'Tổng quan'),(self.downloads,'Tải nội dung'),(self.subtitles,'Phụ đề'),(self.editor,'Editor / preset'),(self.batch,'Edit hàng loạt'),(self.matrix,'Ghép ma trận'),(self.queue,'Hàng đợi'),(self.settings,'Cài đặt')]:self.nav.addTab(page,label)
        self.progress=QProgressBar();self.progress.setRange(0,100);layout.addWidget(self.progress)
        self.cancel_preparation=QPushButton('Hủy tác vụ chuẩn bị / preview');self.cancel_preparation.clicked.connect(lambda:[task.cancel.set() for task in self.tasks]);layout.addWidget(self.cancel_preparation)
        layout.addWidget(self.status);self.setCentralWidget(root)
        self.editor.render_requested.connect(self.guard(self.enqueue_render))
        self.autosave_timer=QTimer(self);self.autosave_timer.setSingleShot(True);self.autosave_timer.setInterval(700);self.autosave_timer.timeout.connect(self.guard(self.autosave))
        self.editor.changed.connect(lambda:self.autosave_timer.start() if not self._restoring else None)
        self.clock=QTimer(self);self.clock.setInterval(350);self.clock.timeout.connect(self.tick);self.clock.start()
        self.actions={};self.shortcuts();self.restore();self.automation.start()
        self.tray=QSystemTrayIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_ComputerIcon),self)
        if QSystemTrayIcon.isSystemTrayAvailable():
            menu=QMenu();show=menu.addAction('Mở Fonesi Edit');show.triggered.connect(self.showNormal)
            quit_action=menu.addAction('Thoát hoàn toàn');quit_action.triggered.connect(self.exit_app);self.tray.setContextMenu(menu);self.tray.show()

    def guard(self,callback):
        def wrapped(*args):
            try:return callback(*args) if args and not isinstance(args[0],bool) else callback()
            except Exception as exc:self.message('Lỗi: '+str(exc));return None
        return wrapped

    def message(self,text):self.status.setText(str(text)[-1800:])

    def background(self,function,done):
        task=Task(function,self);self.tasks.append(task)
        task.result.connect(lambda result:self.guard(lambda:done(result))(),Qt.ConnectionType.QueuedConnection)
        task.error.connect(self.failed,Qt.ConnectionType.QueuedConnection)
        task.progress.connect(lambda p:self.progress.setValue(round(p*100)),Qt.ConnectionType.QueuedConnection)
        def finished():
            self.tasks.remove(task)
            if not self.tasks:self.progress.setRange(0,100);self.progress.setValue(100);self.progress.setFormat('Chuẩn bị hoàn tất')
            self.start_pending()
        task.finished.connect(finished)
        self.pending_tasks.append(task);self.start_pending();return task

    def start_pending(self):
        while self.pending_tasks and sum(task.isRunning() for task in self.tasks)<2:
            task=self.pending_tasks.pop(0)
            if self._shutdown:
                self.tasks.remove(task);task.deleteLater()
            else:task.start()

    def cleanup_cache(self,force=False):
        if self._cache_cleanup_busy:
            if force:self.message('Cache đang được dọn trong một tác vụ nền')
            return
        if self.editor._proxy_pending or self.editor._thumbnail_pending:
            if force:self.message('Proxy/thumbnail đang tạo; dọn cache khi việc đó hoàn tất')
            return
        maximum=int(self.store.setting('proxy_cache_limit_mb',4096))*1024**2
        if maximum<128*1024**2 or maximum>65536*1024**2:
            raise ValueError('Quota proxy cache ngoài khoảng 128–65536 MiB')
        root=self.data/'cache'/'proxies'
        current=self.editor.player.source().toLocalFile()
        self._cache_cleanup_busy=True
        def work(progress,cancel):
            try:
                return evict_proxy_cache(root,maximum,[current]),None
            except (OSError,ValueError) as exc:
                return None,str(exc)[:240]
        def done(outcome):
            self._cache_cleanup_busy=False
            result,error=outcome
            if error:self.message('Dọn cache không thành công: '+error)
            elif force or result['deleted_bytes']:
                mb=result['deleted_bytes']/1024**2
                self.message(f'Cache proxy: giải phóng {mb:.1f} MiB; vượt quota: {result["over_budget"]} (file đang phát được giữ)')
        self.background(work,done)

    def failed(self,error):self.failures.append(error);self.message('Lỗi: '+error)
    def activate_queue(self):self.nav.setCurrentWidget(self.queue)

    def tick(self):
        try:
            self.scheduler.tick();self.queue.refresh()
            self.cancel_preparation.setEnabled(bool(self.tasks))
            active=[task for task in self.tasks if task.started is not None]
            if active:
                elapsed=max(time.monotonic()-task.started for task in active);ratios=[task.ratio for task in active]
                self.progress.setRange(0,100 if any(ratios) else 0)
                self.progress.setFormat(f'Chuẩn bị: {len(active)} việc • {elapsed:.0f}s • %p%' if any(ratios) else f'Chuẩn bị: {len(active)} việc • {elapsed:.0f}s')
            else:self.progress.setRange(0,100);self.progress.setFormat('%p%')
            sample=metrics(self.data);recommended=recommended_parallel(sample,self.store.setting('resource_profile','balanced'))
            gpu='; '.join(f"{g['name']} {g['percent']:.0f}% / VRAM {g['used_mib']:.0f}/{g['total_mib']:.0f} MiB / {g['temperature']:.0f}°C" for g in sample['gpu']) if sample['gpu'] else 'GPU/VRAM: chưa đọc được'
            self.machine.setText(f"CPU {sample['cpu_percent']:.0f}% • RAM trống {sample['ram_available']/1024**3:.1f}/{sample['ram_total']/1024**3:.1f} GiB • Đĩa trống {sample['disk_free']/1024**3:.1f} GiB • Gợi ý tối đa {recommended} worker • {gpu}")
            self.overview.clear()
            for job in self.store.jobs(20):self.overview.addItem(f"{job['kind']} • {job['state']} • {job['progress']*100:.0f}% • {job['id'][:8]}")
            if self.automation.errors:self.message('Automation: '+self.automation.errors[-1])
            if time.monotonic()-self._last_cache_cleanup>=300:
                self._last_cache_cleanup=time.monotonic()
                self.cleanup_cache()
        except Exception as exc:self.message('Scheduler: '+str(exc))

    def autosave(self):
        self.project_id=self.store.save_named('projects',self.project_file.stem if self.project_file else 'Project đang làm',self.editor.composition.to_dict(),self.project_id)
        self.store.set_setting('last_project',self.project_id)
        atomic_json(self.data/'recovery.json',{'schema_version':1,'project_id':self.project_id,'composition':self.editor.composition.to_dict()})

    def restore(self):
        key=self.store.setting('last_project');project=next((p for p in self.store.list_named('projects') if p['id']==key),None)
        if project:
            self._restoring=True;self.project_id=key;self.editor.set_composition(Composition.from_dict(project['data']));self._restoring=False
            self.load_editor_frame()

    def new_project(self):
        self.autosave();self.project_id=None;self.project_file=None;self.editor.undo.clear();self.editor.set_composition(Composition());self.autosave()

    def open_project(self):
        path,_=QFileDialog.getOpenFileName(self,'Mở project',filter='Fonesi (*.fonesi *.json)')
        if not path:return
        data=json.loads(Path(path).read_text(encoding='utf-8'))
        if data.get('schema_version')!=1:raise ValueError('Project schema không hỗ trợ')
        comp=Composition.from_dict(data['composition']);self.autosave();self.project_id=data.get('project_id');self.project_file=Path(path)
        self.editor.undo.clear();self.editor.set_composition(comp);self.load_editor_frame();self.nav.setCurrentWidget(self.editor)

    def save_project(self):
        if not self.project_file:
            path,_=QFileDialog.getSaveFileName(self,'Lưu project',filter='Fonesi (*.fonesi)')
            if not path:return
            self.project_file=Path(path)
        self.autosave();atomic_json(self.project_file,{'schema_version':1,'project_id':self.project_id,'composition':self.editor.composition.to_dict()});self.message('Đã lưu project')

    def save_preset(self):
        name,ok=QInputDialog.getText(self,'Lưu preset','Tên preset')
        if ok:
            c=deepcopy(self.editor.composition);c.clips=[]
            for layer in c.layers:layer.clip_ids=[]
            self.store.save_named('presets',name,c.to_dict());self.message('Đã lưu preset không kèm tệp video nguồn')

    def load_preset(self):
        items=self.store.list_named('presets')
        if not items:raise ValueError('Chưa có preset')
        choice,ok=QInputDialog.getItem(self,'Preset','Chọn',[p['name']+' • '+p['id'][:6] for p in items],0,False)
        if ok:
            index=[p['name']+' • '+p['id'][:6] for p in items].index(choice);c=Composition.from_dict(items[index]['data']);c.clips=deepcopy(self.editor.composition.clips)
            # Locks are never overwritten silently by preset application.
            locked=[deepcopy(l) for l in self.editor.composition.layers if l.locked];ids={l.id for l in locked};c.layers=[l for l in c.layers if l.id not in ids]+locked
            self.editor.begin();self.editor.composition=c;self.editor.commit('Nạp preset')

    def export_preset(self):
        path,_=QFileDialog.getSaveFileName(self,'Xuất preset',filter='Fonesi preset (*.fonesipreset)')
        if not path:return
        comp=Composition.from_dict(self.editor.composition.to_dict());comp.clips=[]
        for layer in comp.layers:layer.clip_ids=[]
        atomic_json(Path(path),{'schema_version':1,'name':Path(path).stem,'composition':comp.to_dict()});self.message('Đã xuất preset; logo/font/audio vẫn tham chiếu đường dẫn, không sao chép tệp riêng')

    def import_preset(self):
        path,_=QFileDialog.getOpenFileName(self,'Nhập preset',filter='Fonesi preset (*.fonesipreset *.json)')
        if not path:return
        data=json.loads(Path(path).read_text(encoding='utf-8'))
        if data.get('schema_version')!=1:raise ValueError('Preset schema không hỗ trợ')
        comp=Composition.from_dict(data['composition']);comp.clips=[]
        for layer in comp.layers:layer.clip_ids=[]
        self.store.save_named('presets',str(data.get('name',Path(path).stem))[:120],comp.to_dict());self.message('Đã nhập preset; dùng Nạp preset và kiểm tra các tài nguyên đi kèm')

    def relink(self):
        root=QFileDialog.getExistingDirectory(self,'Folder media mới')
        if not root:return
        self.editor.begin();missing=[]
        for clip in self.editor.composition.clips:
            if Path(clip.path).is_file():continue
            matches=list(Path(root).rglob(Path(clip.path).name))
            if len(matches)==1:probe(matches[0]);clip.path=str(matches[0].resolve())
            else:missing.append(Path(clip.path).name)
        self.editor.commit('Liên kết lại media');self.load_editor_frame();self.message('Cần chọn lại: '+', '.join(missing) if missing else 'Đã liên kết theo tên duy nhất; kiểm tra lại preview')

    def load_editor_frame(self):
        if not self.editor.composition.clips:return
        source=Path(self.editor.composition.clips[0].path)
        if not source.exists():self.message('Media thiếu; dùng Liên kết lại media');return
        frame=Path(self.workspace.name)/(uuid4().hex+'.png')
        def work(p,c):extract_frame(source,frame,0);return frame
        def done(result):self.editor.frame=result;self.editor.refresh();self.editor.player.setSource(QUrl.fromLocalFile(str(source)))
        self.background(work,done)

    def enqueue_render(self,data):
        comp=Composition.from_dict(data)
        if not comp.clips:raise ValueError('Chưa có video')
        source=Path(comp.clips[0].path);suggestion=source.parent/(source.stem+'_edit_'+str(time.time_ns())[-8:]+'.mp4')
        path,_=QFileDialog.getSaveFileName(self,'Xuất video',str(suggestion),'MP4 (*.mp4)')
        if path:self.store.submit('render',{'composition':comp.to_dict(),'output':path});self.activate_queue()

    def reference(self,comp,second=0):
        snapshot=Composition.from_dict(comp.to_dict());folder=Path(self.workspace.name)/('ref-'+uuid4().hex)
        def done(frame):
            self.editor.canvas.rebuild(frame,reference=True);self.message('Frame từ compositor xuất. Bấm Esc hoặc sửa thuộc tính để quay lại bố cục kéo thả.')
        self.background(lambda p,c:reference_frame(snapshot,folder,second,c),done)

    def playback_preview(self,comp):
        expected=canonical(comp.to_dict())
        snapshot=Composition.from_dict(comp.to_dict());snapshot.encoder='cpu';snapshot.quality=26
        output=Path(self.workspace.name)/('playback-'+uuid4().hex+'.mp4')
        def done(result):
            if canonical(self.editor.composition.to_dict())!=expected:
                self.message('Composition đã đổi khi dựng preview; bản cũ không được phát. Hãy dựng lại.')
                return
            self.editor.player.setSource(QUrl.fromLocalFile(result['output']))
            self.editor.preview_fingerprint=expected
            self.editor.views.setCurrentIndex(1)
            if (self.editor.loop_action.isChecked()
                    and self.editor.in_point is not None and self.editor.out_point is not None):
                self.editor.player.setPosition(round(self.editor.in_point*1000))
            self.editor.player.play()
            self.message('Preview từ compositor gồm layer/âm thanh; loop In–Out chỉ chạy trên bản này. Thay đổi composition cần dựng lại.')
        self.message('Đang dựng preview có âm thanh; có thể hủy tác vụ chuẩn bị.')
        self.background(lambda progress,cancel:render_composition(snapshot,output,progress,cancel),done)

    def preview_composition(self,comp):
        self.editor.begin();self.editor.composition=comp;self.editor.commit('Preview kế hoạch');self.load_editor_frame();self.nav.setCurrentWidget(self.editor)

    def relink_renamed(self,mapping):
        comp=Composition.from_dict(self.editor.composition.to_dict())
        for clip in comp.clips:clip.path=mapping.get(clip.path,clip.path);clip.subtitles=mapping.get(clip.subtitles,clip.subtitles)
        for layer in comp.layers:layer.path=mapping.get(layer.path,layer.path)
        for track in comp.audio:track['path']=mapping.get(track['path'],track['path'])
        self.editor.undo.clear();self.editor.set_composition(comp);self.autosave();self.load_editor_frame()

    def shortcuts(self):
        menu=self.menuBar().addMenu('Thao tác');keys={'Mở project':('Ctrl+O',self.open_project),'Lưu project':('Ctrl+S',self.save_project),
            'Cài đặt':('Ctrl+,',lambda:self.nav.setCurrentWidget(self.settings)), 'Undo':('Ctrl+Z',self.editor.undo.undo),'Redo':('Ctrl+Shift+Z',self.editor.undo.redo),
            'Thêm video':('Ctrl+Shift+O',self.editor.add_video),'Nhân bản':('Ctrl+D',self.editor.duplicate),'Split':('Ctrl+B',self.editor.split),
            'Đưa vào hàng đợi':('Ctrl+Return',self.editor.request_render),'Phát/dừng':('Space',self.editor.toggle_play),'Marker':('M',self.add_marker),
            'Đặt In':('I',self.editor.mark_in),'Đặt Out':('O',self.editor.mark_out),'Nhóm layer':('Ctrl+G',self.editor.group),'Bỏ nhóm':('Ctrl+Shift+G',self.editor.ungroup),
            'Khóa layer':('Ctrl+L',self.editor.lock_selected),'Quét công cụ':('F5',lambda:self.settings.scan()),'Trợ giúp':('F1',self.help)}
        keys.update({'Nhập preset':('',self.import_preset),'Xuất preset':('',self.export_preset)})
        remap=self.store.setting('shortcuts',{})
        for name,(default,callback) in keys.items():
            action=QAction(name,self);action.setShortcut(QKeySequence(remap.get(name,default)))
            def invoke(_checked=False,callback=callback,name=name):
                policy, target = shortcut_focus_policy(QApplication.focusWidget())
                if name in _EDITOR_SHORTCUT_ACTIONS and policy != "global":
                    if policy == "text" and name == "Undo":
                        target.undo()
                    elif policy == "text" and name == "Redo":
                        target.redo()
                    return
                self.guard(callback)()
            action.triggered.connect(invoke);menu.addAction(action);self.actions[name]=action
        configure=menu.addAction('Đổi phím tắt');configure.triggered.connect(self.guard(self.edit_shortcuts))

    def edit_shortcuts(self):
        data={name:action.shortcut().toString() for name,action in self.actions.items()}
        text,ok=QInputDialog.getMultiLineText(self,'Phím tắt','JSON tên → phím (để trống để bỏ)',json.dumps(data,ensure_ascii=False,indent=2))
        if not ok:return
        try:
            normalized = parse_shortcut_remap_json(text, data)
        except ValueError as exc:
            self.message(f"Phím tắt chưa hợp lệ: {exc}")
            return
        # Persist the complete merged map before changing runtime QAction state.
        # A failed write must not leave shortcuts different from the saved settings.
        try:
            self.store.set_setting('shortcuts', normalized)
        except (OSError, RuntimeError, ValueError) as exc:
            self.message(f"Không lưu được phím tắt: {exc}")
            return
        for name, value in normalized.items():
            self.actions[name].setShortcut(QKeySequence(value))

    def add_marker(self):self.editor.timeline.markers.append(self.editor.timeline.playhead);self.editor.timeline.rebuild()
    def help(self):
        from .paths import resource_directory
        from PySide6.QtGui import QDesktopServices
        path=Path(sys.executable).parent/'USER_GUIDE.md' if getattr(sys,'frozen',False) else Path(__file__).resolve().parents[2]/'docs/USER_GUIDE.md'
        if path.is_file():QDesktopServices.openUrl(QUrl.fromLocalFile(str(path)))
        else:self.message('Hướng dẫn: github.com/danhgold7979-cyber/fonesi-edit/blob/main/docs/USER_GUIDE.md')
    def exit_app(self):self.force_close=True;self.close()
    def closeEvent(self,event):
        if not self.force_close and self.store.setting('background',False) and self.tray.isSystemTrayAvailable():self.hide();event.ignore();return
        if not self._shutdown:self.subtitles.persist();self.autosave();self.scheduler.shutdown();self.automation.stop();self._shutdown=True
        for task in self.tasks:task.cancel.set()
        for task in list(self.pending_tasks):self.pending_tasks.remove(task);self.tasks.remove(task);task.deleteLater()
        if self.tasks or self.scheduler.active:
            event.ignore();QTimer.singleShot(150,self.close);return
        self.clock.stop();self.editor.player.stop();self.editor.player.setSource(QUrl());self.tray.hide();self.workspace.cleanup();event.accept()


def main(argv=None):
    arguments=list(argv if argv is not None else sys.argv[1:])
    if arguments[:1]==['--verify']:
        from .verification import main as verify_main
        return verify_main(arguments[1:])
    if '--worker' in (argv or sys.argv[1:]):
        from .worker import main as worker_main
        args=list(argv or sys.argv[1:]);args.remove('--worker');return worker_main(args)
    parser=ArgumentParser();parser.add_argument('--data-dir',type=Path);parser.add_argument('--source',type=Path);parser.add_argument('--smoke',action='store_true');parser.add_argument('--screenshot',type=Path);parser.add_argument('--background',action='store_true')
    args=parser.parse_args(argv);app=QApplication.instance() or QApplication([]);app.setStyle('Fusion')
    app.setStyleSheet("QWidget{background:#111827;color:#e5eaf5;font-size:12px} QLabel#brand{font-size:24px;color:#b4a1ff;padding:8px} QPushButton{background:#293650;border:1px solid #465570;border-radius:5px;padding:7px} QPushButton:hover{background:#3d4e6c} QLineEdit,QSpinBox,QDoubleSpinBox,QComboBox,QPlainTextEdit{background:#1c293d;border:1px solid #40516d;padding:4px} QTabBar::tab{padding:9px 13px;background:#1d293e} QTabBar::tab:selected{background:#59458d} QHeaderView::section{background:#293650;padding:6px} QProgressBar::chunk{background:#9072df}")
    window=MainWindow(args.data_dir)
    if not args.background:window.show()
    if args.source:window.editor.open_media(args.source);window.nav.setCurrentWidget(window.editor)
    if args.smoke:
        app.setQuitOnLastWindowClosed(False)
        decoded=[0];started=time.monotonic();playing=[False]
        window.editor.video.videoSink().videoFrameChanged.connect(lambda frame:decoded.__setitem__(0,decoded[0]+1) if frame.isValid() else None)
        def finish():
            if window.tasks:QTimer.singleShot(100,finish);return
            if args.source and window.editor.composition.clips and not decoded[0] and time.monotonic()-started<12:
                if not playing[0]:window.editor.player.play();playing[0]=True
                QTimer.singleShot(100,finish);return
            failed=bool(window.failures) or bool(args.source and not window.editor.composition.clips)
            if args.source and not decoded[0]:failed=True
            if args.screenshot:
                args.screenshot.parent.mkdir(parents=True,exist_ok=True)
                if not window.grab().save(str(args.screenshot)):failed=True
            window.force_close=True;window.close();app.exit(1 if failed else 0)
        QTimer.singleShot(700,finish)
    return app.exec()


if __name__=='__main__':raise SystemExit(main())
