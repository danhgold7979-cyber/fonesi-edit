from __future__ import annotations
from dataclasses import asdict
from pathlib import Path
import copy
import json
import os
import tempfile
import time
from PIL import Image
from PySide6.QtCore import Qt,QTimer,QUrl,QSettings
from PySide6.QtGui import QAction,QKeySequence,QDesktopServices
from PySide6.QtWidgets import (QMainWindow,QWidget,QVBoxLayout,QHBoxLayout,QTabWidget,QPushButton,QLabel,QFileDialog,QMessageBox,
 QPlainTextEdit,QLineEdit,QSpinBox,QDoubleSpinBox,QComboBox,QTableWidget,QTableWidgetItem,QHeaderView,QCheckBox,QListWidget,QListWidgetItem,QInputDialog,QFormLayout)
from ..core.model import Project,Clip,Cue,CommandHistory,US,digest
from ..core.paths import user_data,atomic_write
from ..core.storage import Store,save_project,load_project
from ..core.jobs import Scheduler
from ..services.media import inspect_asset
from ..services.render import reference_frame
from ..services.subtitles import read_subtitles,write_subtitles,warnings
from ..services.downloads import identify_many,scan
from ..services.batch import scan_folders,make_batch,enqueue_batch
from ..services.matrix import scan_scenes,generate,Rules,validate_rows,export_csv,row_project,reserve
from ..services.browser import BrowserManager,PLATFORMS
from ..services.tools import scan_tools
from .editor import Editor
from .tasks import TaskRunner

DARK='''QMainWindow,QWidget{background:#101a2b;color:#dbe7f7;font-size:12px;} QTabWidget::pane{border:1px solid #2a3b54;} QTabBar::tab{padding:10px 12px;background:#17243a;} QTabBar::tab:selected{background:#164c54;color:#76f0d7;} QPushButton{background:#22354e;border:1px solid #39516e;border-radius:5px;padding:7px 10px;} QPushButton:hover{background:#2d4968;} QPushButton:disabled{color:#65758c;} QLineEdit,QPlainTextEdit,QTableWidget,QListWidget,QDoubleSpinBox,QSpinBox,QComboBox{background:#0c1524;border:1px solid #31455f;padding:4px;selection-background-color:#176f72;} QHeaderView::section{background:#1c2e45;padding:6px;border:0;} QSplitter::handle{background:#30435a;} QLabel#hero{font-size:23px;font-weight:600;color:#74e4d0;}'''


def button(text,callback,layout):
    b=QPushButton(text);b.clicked.connect(callback);layout.addWidget(b);return b


def table(headers):
    t=QTableWidget(0,len(headers));t.setHorizontalHeaderLabels(headers);t.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch);t.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows);return t


class MainWindow(QMainWindow):
    def __init__(self,data_dir=None):
        super().__init__();self.data=Path(data_dir) if data_dir else user_data();self.data.mkdir(parents=True,exist_ok=True)
        self.store=Store(self.data/'state.db');self.scheduler=Scheduler(self.store);self.browser=BrowserManager(self.data/'browser_profiles',self.store)
        self.project=Project();self.history=CommandHistory(self.project);self.project_path=None;self.generation=0;self.dirty=False;self.subtitle_updating=False
        self.runner=TaskRunner(self);self.batch_roots=[];self.batch_plan=[];self.scenes=[];self.matrix_rows=[];self.download_items=[]
        self.settings=QSettings(str(self.data/'ui.ini'),QSettings.Format.IniFormat)
        for key,value in self.store.objects('tool_override').items():os.environ['FONESI_'+key.upper()+'_PATH']=value['path']
        self.setWindowTitle('Fonesi Edit — clean rebuild · development');self.resize(1380,900);self.setStyleSheet(DARK);self.setAcceptDrops(True)
        container=QWidget();root=QVBoxLayout(container);self.setCentralWidget(container)
        top=QHBoxLayout();root.addLayout(top);hero=QLabel('FONESI  /  EDIT');hero.setObjectName('hero');top.addWidget(hero);top.addStretch()
        for label,callback in [('Mở dự án',self.open_project),('Lưu',self.save),('＋ Media',self.add_media),('Xuất → hàng đợi',self.queue_render)]:button(label,callback,top)
        self.tabs=QTabWidget();root.addWidget(self.tabs,1)
        self.build_overview();self.build_downloads();self.build_subtitles();self.editor=Editor(self.project,self.history);self.tabs.addTab(self.editor,'Editor');self.editor.changed.connect(self.mark_changed);self.editor.preview_requested.connect(self.preview)
        self.build_batch();self.build_matrix();self.build_queue();self.build_settings()
        self.statusBar().showMessage('P03–P10 đang phát triển · chỉ kiểm chứng local; xem CURRENT_STATUS.md. Không chứng nhận Windows/live nguồn.')
        self.timer=QTimer(self);self.timer.setInterval(250);self.timer.timeout.connect(self.tick);self.timer.start()
        self.autosave=QTimer(self);self.autosave.setSingleShot(True);self.autosave.setInterval(1500);self.autosave.timeout.connect(self.autosave_now)
        self.actions();self.refresh_accounts();self.scan_tools_async()
        geometry=self.settings.value('geometry')
        if geometry:self.restoreGeometry(geometry)
        if (self.data/'recovery.json').exists():self.recovery_label.setText('Có bản tự lưu phục hồi. Bấm “Mở bản phục hồi” để kiểm tra; không tự thay dự án hiện tại.')

    def page(self,title):
        widget=QWidget();layout=QVBoxLayout(widget);self.tabs.addTab(widget,title);return widget,layout
    def row(self,layout):r=QHBoxLayout();layout.addLayout(r);return r
    def notify(self,text):self.statusBar().showMessage(str(text),20000)
    def error(self,text):self.notify(text);QMessageBox.warning(self,'Cần xử lý',str(text))
    def guarded(self,fn):
        try:return fn()
        except Exception as exc:self.error(f'{type(exc).__name__}: {exc}')
    def actions(self):
        for label,key,handler in [('Mở','Ctrl+O',self.open_project),('Lưu','Ctrl+S',self.save),('Lưu thành','Ctrl+Shift+S',lambda:self.save(True)),('Thêm media','Ctrl+Shift+O',self.add_media),('Cài đặt','Ctrl+,',lambda:self.tabs.setCurrentIndex(7)),('Trợ giúp','F1',self.show_help)]:
            action=QAction(label,self);action.setShortcut(QKeySequence(key));action.triggered.connect(handler);self.addAction(action)
        # Undo/copy/delete single-key routing stays inside focused editor widgets, never global input interception.
    def build_overview(self):
        _,layout=self.page('Tổng quan');label=QLabel('Làm việc với nguồn cục bộ trước.\nGiữ nguyên video gốc · cấu hình job bất biến · chỉ thành công sau kiểm tra đầu ra.');label.setStyleSheet('font-size:20px;padding:20px');layout.addWidget(label)
        self.overview=QLabel();self.overview.setWordWrap(True);layout.addWidget(self.overview);self.recovery_label=QLabel('Chưa có bản phục hồi');layout.addWidget(self.recovery_label)
        r=self.row(layout);button('Mở bản phục hồi',lambda:self.load_path(self.data/'recovery.json'),r);button('Hướng dẫn / giới hạn',self.show_help,r)
        self.metrics=QLabel('Đang đọc tài nguyên…');layout.addWidget(self.metrics);layout.addStretch()
    def build_downloads(self):
        _,layout=self.page('Tải nội dung');self.urls=QPlainTextEdit();self.urls.setPlaceholderText('Một URL mỗi dòng. Mọi nền tảng có hồ sơ đăng nhập riêng; capability live chưa xác nhận.');self.urls.setMaximumHeight(100);layout.addWidget(self.urls)
        r=self.row(layout);self.download_root=QLineEdit(str(self.data/'downloads'));r.addWidget(self.download_root);button('Thư mục…',lambda:self.pick_directory(self.download_root),r)
        self.download_account=QComboBox();r.addWidget(self.download_account);self.download_kind=QComboBox();self.download_kind.addItems(['Video','Ảnh']);r.addWidget(self.download_kind)
        self.scan_limit=QSpinBox();self.scan_limit.setRange(1,100000);self.scan_limit.setValue(100);self.scan_limit.setPrefix('Giới hạn quét: ');r.addWidget(self.scan_limit)
        r=self.row(layout);button('Quét URL',self.scan_urls,r);button('Đưa mục chọn vào hàng đợi',self.queue_downloads,r)
        self.download_status=QLabel('Quét profile có thể chưa đầy đủ. Đăng nhập website ≠ connector dùng được phiên.');layout.addWidget(self.download_status)
        self.download_table=table(['Chọn','Platform / ID','Tiêu đề','URL']);layout.addWidget(self.download_table)
    def build_subtitles(self):
        _,layout=self.page('Phụ đề');r=self.row(layout)
        for label,callback in [('Nhập SRT/VTT/ASS',self.import_subtitles),('Xuất SRT/ASS',self.export_subtitles),('Kiểm tra thời gian',self.check_cues),('Dịch câu chưa khóa',self.translate_cues)]:button(label,callback,r)
        self.bilingual=QCheckBox('Song ngữ');r.addWidget(self.bilingual);self.bilingual.clicked.connect(lambda:self.update_project_setting('bilingual',self.bilingual.isChecked()))
        self.subtitle_table=table(['Bắt đầu (s)','Kết thúc (s)','Gốc','Bản dịch','Khóa']);self.subtitle_table.itemChanged.connect(self.cue_changed);layout.addWidget(self.subtitle_table)
        self.cue_status=QLabel('Thiếu sub mặc định vẫn edit, có cảnh báo. ASS nhập text/timing; style không hỗ trợ được báo.');layout.addWidget(self.cue_status)
    def build_batch(self):
        _,layout=self.page('Edit hàng loạt');r=self.row(layout);button('Thêm thư mục',self.add_batch_root,r);button('Bỏ mục chọn (không xóa tệp)',self.remove_batch_root,r);button('Quét + xem kế hoạch',self.plan_batch,r);button('Chạy thử mục đầu',lambda:self.queue_batch(True),r);button('Chạy mục hợp lệ',self.queue_batch,r)
        self.batch_list=QListWidget();self.batch_list.setMaximumHeight(100);layout.addWidget(self.batch_list)
        r=self.row(layout);self.batch_output=QLineEdit(str(self.data/'output'));r.addWidget(QLabel('Đầu ra'));r.addWidget(self.batch_output);button('Chọn…',lambda:self.pick_directory(self.batch_output),r)
        self.batch_table=table(['Nguồn','Trạng thái','Đích / lỗi']);layout.addWidget(self.batch_table)
        layout.addWidget(QLabel('Mỗi video một đầu ra. Dùng preset editor hiện tại, không tự lấy phụ đề của clip khác. Output/cache/symlink không được quét lại.'))
    def build_matrix(self):
        _,layout=self.page('Ghép theo cảnh');r=self.row(layout);button('Chọn thư mục C1…Cn',self.pick_scenes,r)
        self.matrix_n=QSpinBox();self.matrix_n.setRange(1,10000);self.matrix_n.setValue(5);r.addWidget(QLabel('N'));r.addWidget(self.matrix_n)
        self.matrix_w=QSpinBox();self.matrix_w.setRange(0,100);r.addWidget(QLabel('W'));r.addWidget(self.matrix_w)
        self.matrix_k=QSpinBox();self.matrix_k.setRange(0,100);r.addWidget(QLabel('K'));r.addWidget(self.matrix_k)
        self.matrix_scope=QComboBox();self.matrix_scope.addItems(['previous','window']);r.addWidget(self.matrix_scope)
        self.matrix_seed=QSpinBox();self.matrix_seed.setRange(0,2**31-1);r.addWidget(QLabel('Seed'));r.addWidget(self.matrix_seed)
        r=self.row(layout);button('Sinh ma trận',self.generate_matrix,r);button('Xuất CSV',self.save_matrix_csv,r);button('Render các hàng',self.queue_matrix,r)
        self.matrix_status=QLabel('C2 trước C10; tên logic không đổi tên tệp thật. W/K không nới ngầm; timeout khác vô nghiệm.');layout.addWidget(self.matrix_status)
        self.matrix_table=table(['Chưa chọn cảnh']);self.matrix_table.itemChanged.connect(self.matrix_edited);layout.addWidget(self.matrix_table)
    def build_queue(self):
        _,layout=self.page('Hàng đợi / Lịch sử');r=self.row(layout);self.pause=QCheckBox('Tạm dừng nhận job mới');self.pause.clicked.connect(lambda:self.set_pause());r.addWidget(self.pause)
        button('Hủy job chọn',self.cancel_job,r);button('Thử lại job lỗi',self.retry_job,r);button('Mở kết quả',self.open_result,r);button('Sao chép lỗi',self.copy_error,r)
        self.job_table=table(['ID','Loại','Trạng thái','Công đoạn','Tiến độ','Lỗi / kết quả']);self.job_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers);layout.addWidget(self.job_table);self.last_jobs=None
    def build_settings(self):
        _,layout=self.page('Cài đặt');tabs=QTabWidget();layout.addWidget(tabs)
        tools_page=QWidget();tl=QVBoxLayout(tools_page);tabs.addTab(tools_page,'Công cụ');r=self.row(tl);button('Quét / kiểm tra lại',self.scan_tools_async,r);button('Chọn đường dẫn tool',self.choose_tool_path,r)
        self.tool_table=table(['Tên','Nguồn','Đường dẫn','Phiên bản','Trạng thái / lỗi']);self.tool_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers);tl.addWidget(self.tool_table)
        tl.addWidget(QLabel('Cài/cập nhật tự động cần manifest đã xác minh theo OS/architecture. Chưa có manifest Windows được nghiệm thu cho rebuild; không chạy installer không rõ nguồn.'))
        account_page=QWidget();al=QVBoxLayout(account_page);tabs.addTab(account_page,'Chrome / tài khoản');r=self.row(al);self.platform=QComboBox();self.platform.addItems(PLATFORMS);r.addWidget(self.platform);self.profiles=QComboBox();r.addWidget(self.profiles)
        button('Tạo Chrome riêng',self.create_profile,r);button('Gán tài khoản',self.bind_account,r);button('Mở đăng nhập Chrome',self.open_chrome,r)
        self.account_table=table(['Platform','Hồ sơ','Danh tính','Website','Bridge / nguồn']);self.account_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers);al.addWidget(self.account_table)
        al.addWidget(QLabel('Mật khẩu/OTP/QR nhập trong Chrome thật. Không copy cookie DB, không tắt bảo vệ. Auth download giữ blocked đến khi có evidence handoff phù hợp.'))
        trans_page=QWidget();tf=QFormLayout(trans_page);tabs.addTab(trans_page,'Dịch');self.translation_url=QLineEdit();self.translation_url.setPlaceholderText('https://your-configured-libretranslate.example');tf.addRow('Endpoint của bạn',self.translation_url)
        self.translation_source=QLineEdit('auto');tf.addRow('Ngôn ngữ nguồn',self.translation_source);self.translation_target=QLineEdit('vi');tf.addRow('Ngôn ngữ đích',self.translation_target)
        self.translation_budget=QSpinBox();self.translation_budget.setRange(0,100000000);tf.addRow('Hạn mức ký tự',self.translation_budget)
        self.translation_consent=QCheckBox('Cho gửi nội dung sub đến provider này; đã kiểm tra chi phí/quyền dùng');tf.addRow(self.translation_consent)
        tf.addRow(QLabel('Khóa lấy từ biến môi trường FONESI_TRANSLATION_KEY, không lưu trong project/log. Glossary/context/style provider chưa hỗ trợ trong adapter này.'))
    def mark_changed(self):
        self.dirty=True
        if hasattr(self,'autosave'):self.autosave.start()
    def autosave_now(self):
        try:save_project(self.project,self.data/'recovery.json',backup=True)
        except Exception as exc:self.notify('Tự lưu lỗi: '+str(exc))
    def update_project_setting(self,key,value):self.editor.mutate('setting',lambda:self.project.settings.update({key:value}))
    def pick_directory(self,field):
        path=QFileDialog.getExistingDirectory(self,'Chọn thư mục',field.text())
        if path:field.setText(path)
    def confirm_discard(self):
        return not self.dirty or QMessageBox.question(self,'Dự án chưa lưu','Đổi dự án? Bản tự lưu vẫn được giữ.')==QMessageBox.StandardButton.Yes
    def open_project(self):
        path,_=QFileDialog.getOpenFileName(self,'Mở project','','Fonesi project (*.json)')
        if path:self.load_path(Path(path))
    def load_path(self,path):
        if not self.confirm_discard():return
        def load():
            project=load_project(path);self.runner.cancel_all();self.generation+=1;self.project.__dict__.clear();self.project.__dict__.update(project.__dict__)
            self.history.undo_items.clear();self.history.redo_items.clear();self.project_path=path;self.editor.canvas.base=None;self.editor.canvas.selection.clear();self.editor.refresh();self.refresh_cues();self.dirty=False;self.preview(0,base_only=True)
        self.guarded(load)
    def save(self,save_as=False):
        path=self.project_path
        if path is None or save_as:
            choice,_=QFileDialog.getSaveFileName(self,'Lưu project',str(self.data/'project.json'),'Fonesi project (*.json)')
            if not choice:return
            path=Path(choice)
        def write():save_project(self.project,path);self.project_path=path;self.dirty=False;self.notify('Đã lưu '+str(path))
        self.guarded(write)
    def add_media(self):
        paths,_=QFileDialog.getOpenFileNames(self,'Thêm media','','Video (*.mp4 *.mkv *.mov *.webm *.avi)')
        if paths:self.import_media(paths)
    def import_media(self,paths):
        generation=self.generation;self.notify('Đọc metadata ở tác vụ nền…')
        def work(cancel):return [inspect_asset(Path(p)) for p in paths if not cancel()]
        def done(assets):
            if generation!=self.generation:return
            def append():
                offset=self.project.duration
                for asset in assets:
                    self.project.assets.append(asset);self.project.clips.append(Clip(asset.id,0,asset.duration,offset=offset));offset+=asset.duration
            self.editor.mutate('import media',append);self.tabs.setCurrentIndex(3);self.preview(0,base_only=True)
        self.runner.submit(work,done,self.error)
    def preview(self,t=0,base_only=False):
        if not self.project.clips:return
        snapshot=Project.from_dict(self.project.to_dict());generation=self.generation
        if base_only:snapshot.layers=[];snapshot.cues=[]
        target=self.data/'cache'/('preview-'+digest({'p':snapshot.to_dict(),'time':t})+'.png');target.parent.mkdir(exist_ok=True)
        self.notify('Đang tạo frame chuẩn ngoài UI…')
        def work(cancel):
            if not target.exists():reference_frame(snapshot,t,target,cancel)
            with Image.open(target) as im:return im.copy()
        def done(image):
            if generation!=self.generation:return
            if base_only:self.editor.canvas.base=image
            else:self.editor.canvas.reference=image
            self.editor.canvas.time=t;self.editor.canvas.update();self.notify('Frame chuẩn cùng compositor/export đã sẵn sàng')
        self.runner.submit(work,done,self.error)
    def queue_render(self):
        if not self.project.clips:self.error('Thêm video trước');return
        path,_=QFileDialog.getSaveFileName(self,'Đầu ra MP4 — không ghi đè',str(self.data/'output'/'video edit.mp4'),'MP4 (*.mp4)')
        if path:self.guarded(lambda:self.enqueue_render(self.project,Path(path)))
    def enqueue_render(self,project,path,extra=None):
        snapshot={'project':project.to_dict(),'output':str(path),'tools':{k:os.environ.get('FONESI_'+k.upper()+'_PATH','') for k in ['ffmpeg','ffprobe']}}
        if extra:snapshot.update(extra)
        job=self.store.enqueue('render',snapshot);self.tabs.setCurrentIndex(6);self.notify('Đã lưu snapshot bất biến: '+job[:8]);return job
    def scan_urls(self):
        def prepare():
            sources=identify_many(self.urls.toPlainText());binding=self.download_account.currentData()
            if binding:self.browser.preflight(binding)
            self.download_items=[];self.download_table.setRowCount(0)
            def work(cancel):return [scan(s['url'],{'limit':self.scan_limit.value()},cancel) for s in sources]
            def done(results):
                for result in results:
                    self.download_status.setText('Quét: '+result['completeness']+' — '+result.get('warning',''))
                    for item in result['items']:self.download_items.append({**item,'platform':result['source']['platform']})
                self.download_table.setRowCount(len(self.download_items))
                for row,item in enumerate(self.download_items):
                    choose=QTableWidgetItem();choose.setCheckState(Qt.CheckState.Checked);self.download_table.setItem(row,0,choose)
                    for col,text in enumerate([item['platform']+' / '+item['id'],item['title'],item['url']],1):self.download_table.setItem(row,col,QTableWidgetItem(str(text)))
            self.runner.submit(work,done,self.error)
        self.guarded(prepare)
    def queue_downloads(self):
        def enqueue():
            binding=self.download_account.currentData()
            if binding:self.browser.preflight(binding)
            count=0
            for row,item in enumerate(self.download_items):
                if self.download_table.item(row,0).checkState()!=Qt.CheckState.Checked:continue
                snap={'url':item['url'],'item_id':item['id'],'source_id':item.get('source_id') or item['id'],'channel':item.get('title','Nguồn'),'output_root':self.download_root.text(),'media_kind':'image' if self.download_kind.currentIndex() else 'video','binding_id':binding}
                self.store.enqueue('download',snap,dedupe_key=digest(snap));count+=1
            self.notify(f'Đã đưa {count} mục vào hàng đợi');self.tabs.setCurrentIndex(6)
        self.guarded(enqueue)
    def import_subtitles(self):
        path,_=QFileDialog.getOpenFileName(self,'Nhập phụ đề','','Subtitles (*.srt *.vtt *.ass)')
        if not path:return
        def load():
            cues,notes=read_subtitles(Path(path));self.editor.mutate('import subtitles',lambda:setattr(self.project,'cues',cues));self.refresh_cues();self.cue_status.setText('; '.join(notes) or 'Đã nhập cue text/timing')
        self.guarded(load)
    def refresh_cues(self):
        self.subtitle_updating=True;self.subtitle_table.setRowCount(len(self.project.cues))
        for row,cue in enumerate(self.project.cues):
            for col,value in enumerate([cue.start/US,cue.end/US,cue.text,cue.translation]):self.subtitle_table.setItem(row,col,QTableWidgetItem(str(value)))
            item=QTableWidgetItem();item.setCheckState(Qt.CheckState.Checked if cue.locked else Qt.CheckState.Unchecked);self.subtitle_table.setItem(row,4,item)
        self.subtitle_updating=False
    def cue_changed(self,item):
        if self.subtitle_updating:return
        def change():
            cue=self.project.cues[item.row()];self.history.begin()
            try:
                if item.column()==0:cue.start=round(float(item.text())*US)
                elif item.column()==1:cue.end=round(float(item.text())*US)
                elif item.column()==2:cue.text=item.text();cue.locked=True
                elif item.column()==3:cue.translation=item.text();cue.locked=True
                else:cue.locked=item.checkState()==Qt.CheckState.Checked
                self.history.commit('edit cue')
            except Exception:self.history.cancel();self.refresh_cues();raise
            self.editor.refresh()
        self.guarded(change)
    def export_subtitles(self):
        path,_=QFileDialog.getSaveFileName(self,'Xuất phụ đề',str(self.data/'sub.srt'),'SRT (*.srt);;ASS (*.ass)')
        if path:self.guarded(lambda:write_subtitles(self.project.cues,Path(path),bilingual=self.bilingual.isChecked()))
    def check_cues(self):self.cue_status.setText(json.dumps(warnings(self.project.cues,self.project.duration),ensure_ascii=False) or 'Không cảnh báo')
    def translate_cues(self):
        from ..services.translation import Translator,TranslationConfig
        config=TranslationConfig(self.translation_url.text(),self.translation_source.text(),self.translation_target.text(),enabled=self.translation_consent.isChecked(),consent_remote=self.translation_consent.isChecked(),character_limit=self.translation_budget.value())
        cues=copy.deepcopy(self.project.cues);generation=self.generation
        def done(result):
            if generation!=self.generation:return
            # Preserve edits/locks made while a remote request was running.
            before={c.id:c for c in cues};translations={c.id:c.translation for c in result}
            def apply():
                for c in self.project.cues:
                    if c.id in before and not c.locked and c.text==before[c.id].text:c.translation=translations[c.id]
            self.editor.mutate('translation',apply);self.refresh_cues()
        self.runner.submit(lambda cancel:Translator(self.store,config).translate(cues),done,self.error)
    def add_batch_root(self):
        path=QFileDialog.getExistingDirectory(self,'Thư mục nguồn')
        if path and path not in self.batch_roots:self.batch_roots.append(path);item=QListWidgetItem(path);item.setCheckState(Qt.CheckState.Checked);self.batch_list.addItem(item)
    def remove_batch_root(self):
        row=self.batch_list.currentRow()
        if row>=0:self.batch_list.takeItem(row);self.batch_roots.pop(row)
    def plan_batch(self):
        roots=[Path(self.batch_list.item(i).text()) for i in range(self.batch_list.count()) if self.batch_list.item(i).checkState()==Qt.CheckState.Checked]
        template=Project.from_dict(self.project.to_dict());output=Path(self.batch_output.text());self.notify('Quét/probe ở nền…')
        def done(plans):
            self.batch_plan=plans;self.batch_table.setRowCount(len(plans))
            for r,p in enumerate(plans):
                for c,text in enumerate([p['source'],p['status'],p.get('output',p.get('error',''))]):self.batch_table.setItem(r,c,QTableWidgetItem(text))
            self.notify(f'Kế hoạch: {sum(p["status"]=="ready" for p in plans)}/{len(plans)} hợp lệ')
        self.runner.submit(lambda cancel:make_batch(scan_folders(roots,[output,self.data/'cache',self.data/'browser_profiles'],cancel),template,output,cancel=cancel),done,self.error)
    def queue_batch(self,first=False):
        plans=[p for p in self.batch_plan if p['status']=='ready'];plans=plans[:1] if first else plans
        self.guarded(lambda:enqueue_batch(self.store,plans));self.tabs.setCurrentIndex(6)
    def pick_scenes(self):
        path=QFileDialog.getExistingDirectory(self,'Thư mục cha các cảnh')
        if not path:return
        def done(scenes):self.scenes=scenes;self.matrix_status.setText(' → '.join(f'{s["label"]}: {s["name"]} ({len(s["angles"])} góc)' for s in scenes))
        self.runner.submit(lambda cancel:scan_scenes(Path(path)),done,self.error)
    def matrix_rules(self):return Rules(window=self.matrix_w.value(),different=self.matrix_k.value(),compare=self.matrix_scope.currentText(),seed=self.matrix_seed.value(),timeout=5)
    def generate_matrix(self):
        if not self.scenes:self.error('Chọn cảnh trước');return
        rules=self.matrix_rules();sizes=[len(s['angles']) for s in self.scenes];count=self.matrix_n.value()
        def done(result):self.matrix_rows=result['rows'];self.matrix_status.setText(f'{result["status"]} · {len(self.matrix_rows)}/{count} hàng · lý thuyết {result["theoretical"]} · không nới W/K');self.show_matrix()
        self.runner.submit(lambda cancel:generate(sizes,count,rules,cancel=cancel),done,self.error)
    def show_matrix(self):
        self.matrix_table.blockSignals(True);self.matrix_table.setColumnCount(len(self.scenes));self.matrix_table.setHorizontalHeaderLabels([s['label'] for s in self.scenes]);self.matrix_table.setRowCount(len(self.matrix_rows))
        for r,row in enumerate(self.matrix_rows):
            for c,value in enumerate(row):self.matrix_table.setItem(r,c,QTableWidgetItem(str(value+1)))
        self.matrix_table.blockSignals(False)
    def matrix_edited(self,item):
        def edit():
            row=copy.deepcopy(self.matrix_rows);value=int(item.text())-1
            if not 0<=value<len(self.scenes[item.column()]['angles']):raise ValueError('Góc ngoài danh sách')
            row[item.row()][item.column()]=value;bad=validate_rows(row,self.matrix_rules())
            if bad is not None:raise ValueError(f'Hàng {bad+1} vi phạm W/K/unique; thay đổi không được áp')
            self.matrix_rows=row
        self.guarded(edit);self.show_matrix()
    def save_matrix_csv(self):
        path,_=QFileDialog.getSaveFileName(self,'Xuất ma trận',str(self.data/'matrix.csv'),'CSV (*.csv)')
        if path:self.guarded(lambda:export_csv(self.scenes,self.matrix_rows,Path(path)))
    def queue_matrix(self):
        if not self.matrix_rows:return
        output=QFileDialog.getExistingDirectory(self,'Đầu ra ma trận')
        if not output:return
        template=Project.from_dict(self.project.to_dict());scenes=copy.deepcopy(self.scenes);rows=copy.deepcopy(self.matrix_rows);scope=self.project.id
        def work(cancel):return [(row_project(scenes,row,template),[s['angles'][a]['id'] for s,a in zip(scenes,row)]) for row in rows if not cancel()]
        def done(plans):
            def enqueue():
                for i,(project,combination) in enumerate(plans):
                    key=digest(combination);job=self.store.enqueue('render',{'project':project.to_dict(),'output':str(Path(output)/f'matrix_{i+1:04}.mp4'),'matrix':{'project_id':scope,'key':key}},dedupe_key=scope+':matrix:'+key)
                    reserve(self.store,scope,combination,job)
                self.tabs.setCurrentIndex(6)
            self.guarded(enqueue)
        self.runner.submit(work,done,self.error)
    def set_pause(self):self.scheduler.paused=self.pause.isChecked()
    def selected_job(self):
        row=self.job_table.currentRow();return self.job_table.item(row,0).data(Qt.ItemDataRole.UserRole) if row>=0 and self.job_table.item(row,0) else None
    def cancel_job(self):
        job=self.selected_job()
        if job:self.store.cancel(job)
    def retry_job(self):
        job=self.selected_job()
        if job:self.guarded(lambda:self.store.retry(job))
    def open_result(self):
        job=self.selected_job()
        if job:
            row=self.store.get(job);result=json.loads(row['result'] or '{}')
            if result.get('path'):QDesktopServices.openUrl(QUrl.fromLocalFile(result['path']))
    def copy_error(self):
        from PySide6.QtWidgets import QApplication
        job=self.selected_job()
        if job:QApplication.clipboard().setText(self.store.get(job).get('error') or '')
    def scan_tools_async(self):
        if not hasattr(self,'tool_table'):return
        overrides={k:v['path'] for k,v in self.store.objects('tool_override').items()}
        def done(rows):
            self.tool_table.setRowCount(len(rows))
            for r,row in enumerate(rows):
                for c,text in enumerate([row['name'],row['origin'],row['path'],row['version'],row['state']+' '+row['error']]):self.tool_table.setItem(r,c,QTableWidgetItem(str(text)))
        self.runner.submit(lambda cancel:scan_tools(overrides),done,self.error)
    def choose_tool_path(self):
        row=self.tool_table.currentRow()
        if row<0:return
        name=self.tool_table.item(row,0).text()
        if name not in {'ffmpeg','ffprobe','chrome'}:self.error('Downloader dùng module đã pin trong bản này');return
        path,_=QFileDialog.getOpenFileName(self,'Chọn '+name)
        if path:self.store.put('tool_override',name,{'path':path});os.environ['FONESI_'+name.upper()+'_PATH']=path;self.scan_tools_async()
    def refresh_accounts(self):
        profiles=self.store.objects('browser_profile');self.profiles.clear()
        for key,p in profiles.items():self.profiles.addItem(p['name'],key)
        self.download_account.clear();self.download_account.addItem('Công khai',None)
        bindings=self.store.objects('account_binding');self.account_table.setRowCount(len(bindings))
        for r,(key,b) in enumerate(bindings.items()):
            self.download_account.addItem(b['platform']+' / '+profiles[b['profile_id']]['name'],key)
            for c,text in enumerate([b['platform'],profiles[b['profile_id']]['name'],b['identity'] or 'chưa xác minh',b['web_state'],b['bridge_state']+' / '+b['source_state']]):self.account_table.setItem(r,c,QTableWidgetItem(text))
    def create_profile(self):
        name,ok=QInputDialog.getText(self,'Hồ sơ Chrome riêng','Tên hồ sơ')
        if ok and name:self.browser.create_profile(name);self.refresh_accounts()
    def bind_account(self):
        profile=self.profiles.currentData()
        if profile:self.guarded(lambda:self.browser.bind(self.platform.currentText(),profile));self.refresh_accounts()
        else:self.error('Tạo/chọn hồ sơ trước')
    def open_chrome(self):
        profile=self.profiles.currentData();chrome=os.environ.get('FONESI_CHROME_PATH','')
        if not chrome:
            rows=scan_tools();chrome=next((r['path'] for r in rows if r['name']=='chrome'),'')
        if profile:self.guarded(lambda:self.browser.open(chrome,profile,self.platform.currentText()))
        else:self.error('Tạo/chọn hồ sơ trước')
    def tick(self):
        self.scheduler.tick();rows=self.store.jobs();signature=[(r['id'],r['state'],r['progress'],r['stage'],r['error']) for r in rows]
        if signature!=self.last_jobs:
            selected=self.selected_job();self.job_table.setRowCount(len(rows))
            for i,r in enumerate(rows):
                result=json.loads(r['result'] or '{}');values=[r['id'][:8],r['kind'],r['state'],r['stage'],'—' if r['progress'] is None else f'{r["progress"]*100:.0f}%',r['error'] or result.get('path','')]
                for j,text in enumerate(values):
                    item=QTableWidgetItem(text)
                    if j==0:item.setData(Qt.ItemDataRole.UserRole,r['id'])
                    self.job_table.setItem(i,j,item)
                if r['id']==selected:self.job_table.selectRow(i)
            self.last_jobs=signature
        self.overview.setText(f'Dự án: {self.project.name}\n{len(self.project.assets)} media · {len(self.project.layers)} layer · {len(self.project.cues)} cue · {self.project.duration/US:.2f} giây\n{sum(r["state"].startswith("succeeded") for r in rows)} job đã kiểm tra thành công / {len(rows)} tổng\nTiến độ hiện tại: docs/CURRENT_STATUS.md — nhóm chưa xong không được coi hoàn tất.')
        try:
            import psutil,shutil
            mem=psutil.virtual_memory();disk=shutil.disk_usage(self.data);self.metrics.setText(f'CPU {psutil.cpu_percent():.0f}% · RAM khả dụng {mem.available/1024**3:.1f} GiB · Đĩa trống {disk.free/1024**3:.1f} GiB · GPU/VRAM: chưa đo')
        except Exception:self.metrics.setText('Metrics không đọc được — unknown')
    def show_help(self):
        QMessageBox.information(self,'Hướng dẫn bản rebuild','1. Thêm media → Editor → kéo/resize/xoay/chữ/logo/mask.\n2. Nhập sub, chỉnh cue; Frame xuất chuẩn để đối chiếu.\n3. Lưu project hoặc Xuất → Hàng đợi.\n4. Batch quét folder/dry-run; Matrix chọn C1…Cn rồi sinh W/K.\n\nCtrl+O mở · Ctrl+S lưu · Ctrl+, cài đặt · Delete canvas chỉ bỏ layer · Alt kéo bỏ snap.\n\nChưa nghiệm thu đầy đủ: Windows/GPU/Chrome handoff/live nguồn/dịch thực; nhiều tùy chọn nâng cao còn mở. Không dùng bản này như bản phát hành hoàn tất.')
    def dragEnterEvent(self,event):
        if event.mimeData().hasUrls():event.acceptProposedAction()
    def dropEvent(self,event):
        files=[]
        for url in event.mimeData().urls():
            p=Path(url.toLocalFile())
            if p.is_file():files.append(str(p))
            elif p.is_dir():self.batch_roots.append(str(p));item=QListWidgetItem(str(p));item.setCheckState(Qt.CheckState.Checked);self.batch_list.addItem(item)
        if files:self.import_media(files)
        event.acceptProposedAction()
    def closeEvent(self,event):
        self.autosave_now();self.runner.cancel_all();self.scheduler.shutdown(cancel=True);self.settings.setValue('geometry',self.saveGeometry());event.accept()
