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
    QProgressBar,QFileDialog,QInputDialog,QListWidget,QLineEdit,QPlainTextEdit,QTextEdit,QSystemTrayIcon,QMenu,QStyle)

from .domain import Composition,atomic_json
from .paths import data_directory
from .storage import Store
from .jobs import Scheduler
from .automation import Automation,metrics,recommended_parallel
from .prototypes.tools import configure_tools
from .prototypes.media import extract_frame,probe
from .render import reference_frame
from .ui.tasks import Task
from .ui.editor import Editor
from .ui.pages import DownloadsPage,SubtitlesPage,BatchPage,MatrixPage,QueuePage,SettingsPage


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
        self.progress=QProgressBar();self.progress.setRange(0,100);layout.addWidget(self.progress);layout.addWidget(self.status);self.setCentralWidget(root)
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
            self.start_pending()
        task.finished.connect(finished)
        self.pending_tasks.append(task);self.start_pending();return task

    def start_pending(self):
        while self.pending_tasks and sum(task.isRunning() for task in self.tasks)<2:
            task=self.pending_tasks.pop(0)
            if self._shutdown:
                self.tasks.remove(task);task.deleteLater()
            else:task.start()

    def failed(self,error):self.failures.append(error);self.message('Lỗi: '+error)
    def activate_queue(self):self.nav.setCurrentWidget(self.queue)

    def tick(self):
        try:
            self.scheduler.tick();self.queue.refresh()
            sample=metrics(self.data);recommended=recommended_parallel(sample,self.store.setting('resource_profile','balanced'))
            gpu='; '.join(f"{g['name']} {g['percent']:.0f}% / VRAM {g['used_mib']:.0f}/{g['total_mib']:.0f} MiB / {g['temperature']:.0f}°C" for g in sample['gpu']) if sample['gpu'] else 'GPU/VRAM: chưa đọc được'
            self.machine.setText(f"CPU {sample['cpu_percent']:.0f}% • RAM trống {sample['ram_available']/1024**3:.1f}/{sample['ram_total']/1024**3:.1f} GiB • Đĩa trống {sample['disk_free']/1024**3:.1f} GiB • Gợi ý tối đa {recommended} worker • {gpu}")
            self.overview.clear()
            for job in self.store.jobs(20):self.overview.addItem(f"{job['kind']} • {job['state']} • {job['progress']*100:.0f}% • {job['id'][:8]}")
            if self.automation.errors:self.message('Automation: '+self.automation.errors[-1])
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

    def preview_composition(self,comp):
        self.editor.begin();self.editor.composition=comp;self.editor.commit('Preview kế hoạch');self.load_editor_frame();self.nav.setCurrentWidget(self.editor)

    def shortcuts(self):
        menu=self.menuBar().addMenu('Thao tác');keys={'Mở project':('Ctrl+O',self.open_project),'Lưu project':('Ctrl+S',self.save_project),
            'Cài đặt':('Ctrl+,',lambda:self.nav.setCurrentWidget(self.settings)), 'Undo':('Ctrl+Z',self.editor.undo.undo),'Redo':('Ctrl+Shift+Z',self.editor.undo.redo),
            'Thêm video':('Ctrl+Shift+O',self.editor.add_video),'Nhân bản':('Ctrl+D',self.editor.duplicate),'Split':('Ctrl+B',self.editor.split),
            'Đưa vào hàng đợi':('Ctrl+Return',self.editor.request_render),'Phát/dừng':('Space',self.editor.toggle_play),'Marker':('M',self.add_marker)}
        remap=self.store.setting('shortcuts',{})
        for name,(default,callback) in keys.items():
            action=QAction(name,self);action.setShortcut(QKeySequence(remap.get(name,default)))
            def invoke(_checked=False,callback=callback):
                if isinstance(QApplication.focusWidget(),(QLineEdit,QPlainTextEdit,QTextEdit)) and callback not in {self.save_project,self.open_project}:return
                self.guard(callback)()
            action.triggered.connect(invoke);menu.addAction(action);self.actions[name]=action
        configure=menu.addAction('Đổi phím tắt');configure.triggered.connect(self.guard(self.edit_shortcuts))

    def edit_shortcuts(self):
        data={name:action.shortcut().toString() for name,action in self.actions.items()}
        text,ok=QInputDialog.getMultiLineText(self,'Phím tắt','JSON tên → phím (để trống để bỏ)',json.dumps(data,ensure_ascii=False,indent=2))
        if not ok:return
        changed=json.loads(text)
        if not isinstance(changed,dict) or set(changed)-set(data):raise ValueError('Tên thao tác không hợp lệ')
        normalized=[QKeySequence(value).toString() for value in changed.values() if value]
        if len(set(normalized))!=len(normalized):raise ValueError('Phím tắt trùng nhau')
        for name,value in changed.items():self.actions[name].setShortcut(QKeySequence(value))
        self.store.set_setting('shortcuts',changed)

    def add_marker(self):self.editor.timeline.markers.append(self.editor.timeline.playhead);self.editor.timeline.rebuild()
    def exit_app(self):self.force_close=True;self.close()
    def closeEvent(self,event):
        if not self.force_close and self.store.setting('background',False) and self.tray.isSystemTrayAvailable():self.hide();event.ignore();return
        if not self._shutdown:self.autosave();self.scheduler.shutdown();self.automation.stop();self._shutdown=True
        for task in self.tasks:task.cancel.set()
        for task in list(self.pending_tasks):self.pending_tasks.remove(task);self.tasks.remove(task);task.deleteLater()
        if self.tasks or self.scheduler.active:
            event.ignore();QTimer.singleShot(150,self.close);return
        self.clock.stop();self.editor.player.stop();self.editor.player.setSource(QUrl());self.tray.hide();self.workspace.cleanup();event.accept()


def main(argv=None):
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
        def finish():
            if window.tasks:QTimer.singleShot(100,finish);return
            failed=bool(window.failures) or bool(args.source and not window.editor.composition.clips)
            if args.screenshot:
                args.screenshot.parent.mkdir(parents=True,exist_ok=True)
                if not window.grab().save(str(args.screenshot)):failed=True
            window.force_close=True;window.close();app.exit(1 if failed else 0)
        QTimer.singleShot(700,finish)
    return app.exec()


if __name__=='__main__':raise SystemExit(main())
