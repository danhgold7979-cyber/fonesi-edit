"""Functional workflow pages; all expensive operations use workers or background tasks."""
from dataclasses import asdict
from copy import deepcopy
from pathlib import Path
import csv
import hashlib
import json
import os
import time

from PySide6.QtCore import Qt,QAbstractTableModel,QModelIndex
from PySide6.QtGui import QColor,QDesktopServices
from PySide6.QtWidgets import (QWidget,QVBoxLayout,QHBoxLayout,QFormLayout,QPushButton,QLabel,QLineEdit,QPlainTextEdit,
    QComboBox,QSpinBox,QDoubleSpinBox,QCheckBox,QFileDialog,QTableWidget,QTableWidgetItem,QTableView,QTreeWidget,
    QTreeWidgetItem,QHeaderView,QTabWidget,QInputDialog,QApplication,QMessageBox,QToolBar)

from ..domain import Composition,Clip,canonical,atomic_json
from ..storage import TERMINAL
from ..batch import scan_folders,batch_plan,enqueue_batch
from ..matrix import scan_scenes,generate,history,combination,valid_against,row_composition,enqueue_rows
from ..subtitles import Caption,read_captions,write_captions,caption_warnings
from ..downloads import platform_for
from ..browser import PLATFORMS,profiles,bindings,create_profile,bind,login,pairing_code
from ..native_host import register_host
from ..prototypes.tools import scan_tools,configure_tools
from ..dependencies import resolve_manifest,install,install_chrome,rollback
from ..automation import metrics,recommended_parallel


def buttons(layout,host,items):
    row=QToolBar();layout.addWidget(row)
    for label,callback in items:
        action=row.addAction(label);action.triggered.connect(host.guard(callback))
    return row


def file_row(form,label,host,directory=False,save=False):
    box=QWidget();row=QHBoxLayout(box);row.setContentsMargins(0,0,0,0);field=QLineEdit();row.addWidget(field)
    button=QPushButton('Chọn…');row.addWidget(button)
    def choose():
        path=QFileDialog.getExistingDirectory(host,label) if directory else (QFileDialog.getSaveFileName(host,label)[0] if save else QFileDialog.getOpenFileName(host,label)[0])
        if path:field.setText(path)
    button.clicked.connect(host.guard(choose));form.addRow(label,box);return field


class DownloadsPage(QWidget):
    def __init__(self,host):
        super().__init__();self.host=host;layout=QVBoxLayout(self)
        layout.addWidget(QLabel('Quét và tải qua yt-dlp/gallery-dl. Mức hỗ trợ live và phiên đăng nhập được kiểm tra riêng theo nguồn.'))
        self.urls=QPlainTextEdit();self.urls.setPlaceholderText('Một URL kênh/bài/playlist mỗi dòng');self.urls.setMaximumHeight(110);layout.addWidget(self.urls)
        form=QFormLayout();layout.addLayout(form)
        self.folder=file_row(form,'Thư mục tải',host,True);self.folder.setText(str(host.data/'downloads'))
        self.engine=QComboBox();self.engine.addItems(['auto','video','gallery']);form.addRow('Bộ tải',self.engine)
        self.media=QComboBox();self.media.addItems(['both','videos','images']);form.addRow('Loại nội dung',self.media)
        self.account=QComboBox();form.addRow('Tài khoản',self.account)
        self.limit=QSpinBox();self.limit.setRange(0,1000000);self.limit.setValue(0);form.addRow('Số lượng (0 = không giới hạn)',self.limit)
        self.height=QSpinBox();self.height.setRange(144,4320);self.height.setValue(1080);form.addRow('Chất lượng tối đa',self.height)
        self.lang=QLineEdit('vi,zh.*,en');form.addRow('Ngôn ngữ sub ưu tiên',self.lang)
        self.after=QLineEdit();self.before=QLineEdit();form.addRow('Từ ngày YYYYMMDD',self.after);form.addRow('Đến ngày YYYYMMDD',self.before)
        self.sub=QCheckBox('Tải phụ đề nếu có');self.sub.setChecked(True);form.addRow(self.sub)
        self.auto=QCheckBox('Sau tải: edit theo preset editor hiện tại');form.addRow(self.auto)
        self.translate=QCheckBox('Tự dịch sub trước edit (cần provider được cấu hình)');form.addRow(self.translate)
        buttons(layout,host,[('Làm mới tài khoản',self.refresh_accounts),('Quét danh sách',lambda:self.submit('scan')),('Tải hàng loạt',lambda:self.submit('download')),('Xem kết quả quét',self.show_scan),('Đặt lịch',self.schedule)])
        self.result=QPlainTextEdit();self.result.setReadOnly(True);layout.addWidget(self.result,1);self.last_scan=None;self.refresh_accounts()

    def refresh_accounts(self):
        selected=self.account.currentData();self.account.clear();self.account.addItem('Công khai / mặc định từng nền tảng',None)
        for item in bindings(self.host.store):self.account.addItem(f'{item["platform"]} • {item["label"]} • {item["status"]}',item['id'])
        index=self.account.findData(selected)
        if index>=0:self.account.setCurrentIndex(index)

    def payloads(self):
        if not self.folder.text():raise ValueError('Chọn thư mục tải')
        urls=list(dict.fromkeys(line.strip() for line in self.urls.toPlainText().splitlines() if line.strip()))
        if not urls:raise ValueError('Chưa có URL')
        accounts={item['id']:item for item in bindings(self.host.store)}
        for url in urls:
            platform=platform_for(url);account=self.account.currentData() or self.host.store.setting('default_binding:'+platform)
            if account and (account not in accounts or accounts[account]['platform']!=platform):raise ValueError('Tài khoản được chọn không thuộc nền tảng '+platform)
            p={'url':url,'folder':self.folder.text(),'engine':self.engine.currentText(),'media':self.media.currentText(),
                'limit':self.limit.value(),'height':self.height.value(),'subtitles':self.sub.isChecked(),'languages':[x.strip() for x in self.lang.text().split(',') if x.strip()],
                'account_ref':account,'expected_identity':accounts[account]['identity'] if account else None}
            for key,field in [('date_after',self.after),('date_before',self.before)]:
                if field.text():
                    import datetime;datetime.datetime.strptime(field.text(),'%Y%m%d');p[key]=field.text()
            if self.auto.isChecked():p['workflow']={'preset':self.host.editor.composition.to_dict(),'translate':self.translate.isChecked(),'language':'vi','translation':self.host.store.setting('translation',{})}
            yield p

    def submit(self,kind):
        payloads=list(self.payloads())
        for payload in payloads:
            key=self.host.store.submit(kind,payload)
            if kind=='scan':self.last_scan=key
        self.host.message(f'Đã thêm {len(payloads)} tác vụ {kind}');self.host.activate_queue()

    def show_scan(self):
        if not self.last_scan:return
        job=self.host.store.job(self.last_scan)
        self.result.setPlainText(json.dumps(job['result'] or {'state':job['state'],'error':job['error']},ensure_ascii=False,indent=2))

    def schedule(self):
        payloads=list(self.payloads());minutes,ok=QInputDialog.getInt(self,'Lịch tải','Mỗi bao nhiêu phút?',60,1,100000)
        if not ok:return
        with self.host.store.connect() as conn:
            for p in payloads:
                key=hashlib.sha256(canonical(p).encode()).hexdigest()[:32]
                conn.execute('INSERT OR REPLACE INTO schedules(id,data,next_run) VALUES(?,?,?)',(key,canonical({'payload':p,'interval':minutes*60}),time.time()))
        self.host.message('Đã đặt lịch. App cần đang chạy hoặc được bật chế độ nền.')


class SubtitlesPage(QWidget):
    def __init__(self,host):
        super().__init__();self.host=host;self.captions=[];self.last_job=None;layout=QVBoxLayout(self)
        buttons(layout,host,[('Mở SRT/VTT/ASS',self.open),('Lưu sub',self.save),('Thêm câu',self.add),('Tách câu',self.split),('Gộp câu chọn',self.merge),('Gắn vào clip',self.attach)])
        row=QHBoxLayout();layout.addLayout(row);self.source=QComboBox();self.source.setEditable(True);self.source.addItems(['auto','zh','en','vi','ja','ko']);row.addWidget(self.source)
        self.target=QComboBox();self.target.setEditable(True);self.target.addItems(['vi','en','zh','ja','ko','fr','de','es']);row.addWidget(self.target)
        b=QPushButton('Dịch qua hàng đợi');b.clicked.connect(host.guard(self.translate));row.addWidget(b)
        b=QPushButton('Nạp kết quả dịch');b.clicked.connect(host.guard(self.load_translation));row.addWidget(b)
        self.table=QTableWidget(0,5);self.table.setHorizontalHeaderLabels(['Bắt đầu s','Kết thúc s','Bản gốc','Bản dịch / nội dung','Khóa'])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch);self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows);layout.addWidget(self.table,1)
        self.warning=QLabel();self.warning.setWordWrap(True);layout.addWidget(self.warning)

    def refresh(self):
        self.table.setRowCount(len(self.captions))
        for row,c in enumerate(self.captions):
            for col,value in enumerate((f'{c.start_ms/1000:.3f}',f'{c.end_ms/1000:.3f}',c.source_text or c.text,c.text)):
                self.table.setItem(row,col,QTableWidgetItem(value))
            check=QTableWidgetItem();check.setCheckState(Qt.CheckState.Checked if c.locked else Qt.CheckState.Unchecked);self.table.setItem(row,4,check)
        self.warning.setText('\n'.join(caption_warnings(self.captions)[:10]))

    def collect(self):
        result=[]
        for row,old in enumerate(self.captions):
            result.append(Caption(round(float(self.table.item(row,0).text())*1000),round(float(self.table.item(row,1).text())*1000),self.table.item(row,3).text(),self.table.item(row,2).text(),self.table.item(row,4).checkState()==Qt.CheckState.Checked,old.id))
        return result

    def open(self):
        path,_=QFileDialog.getOpenFileName(self,'Mở phụ đề',filter='Sub (*.srt *.vtt *.ass)')
        if path:self.captions=read_captions(Path(path));self.refresh()

    def save(self):
        self.captions=self.collect();path,_=QFileDialog.getSaveFileName(self,'Xuất sub',filter='SRT (*.srt);;ASS (*.ass);;VTT (*.vtt)')
        if path:write_captions(Path(path),self.captions,overwrite=True);self.host.message('Đã lưu sub')

    def add(self):
        self.captions=self.collect();start=self.captions[-1].end_ms if self.captions else 0
        self.captions.append(Caption(start,start+2000,'Câu mới'));self.refresh()

    def split(self):
        self.captions=self.collect();index=self.table.currentRow()
        if index<0:return
        cue=self.captions[index];half=(cue.start_ms+cue.end_ms)//2;words=cue.text.split();cut=max(1,len(words)//2)
        self.captions[index:index+1]=[Caption(cue.start_ms,half,' '.join(words[:cut]),locked=cue.locked),Caption(half,cue.end_ms,' '.join(words[cut:]) or '…',locked=cue.locked)];self.refresh()

    def merge(self):
        self.captions=self.collect();rows=sorted({i.row() for i in self.table.selectedIndexes()})
        if len(rows)<2:return
        if rows!=list(range(rows[0],rows[-1]+1)):raise ValueError('Chọn các cue liền nhau')
        cues=self.captions[rows[0]:rows[-1]+1]
        self.captions[rows[0]:rows[-1]+1]=[Caption(cues[0].start_ms,cues[-1].end_ms,'\n'.join(c.text for c in cues),locked=any(c.locked for c in cues))];self.refresh()

    def attach(self):
        captions=self.collect();editor=self.host.editor
        if not editor.composition.clips:raise ValueError('Chọn video trong editor trước')
        key=hashlib.sha256(canonical([asdict(c) for c in captions]).encode()).hexdigest()[:20];path=self.host.data/'subtitles'/(key+'.srt')
        if not path.exists():write_captions(path,captions)
        index=max(0,editor.clips.currentRow());editor.begin();editor.composition.clips[index].subtitles=str(path);editor.commit('Gắn sub')
        self.host.message('Đã gắn sub; video nguồn giữ nguyên')

    def translate(self):
        captions=self.collect()
        if not captions:raise ValueError('Chưa có cue')
        output=self.host.data/'subtitles'/('translation-'+str(time.time_ns())+'.srt')
        self.last_job=self.host.store.submit('translate',{'captions':[asdict(c) for c in captions],'source_language':self.source.currentText(),'target_language':self.target.currentText(),'config':self.host.store.setting('translation',{}),'output':str(output)})
        self.host.message('Đã đưa bản chụp sub vào hàng đợi; không tự ghi đè các sửa tay tiếp theo')

    def load_translation(self):
        if not self.last_job:return
        job=self.host.store.job(self.last_job)
        if job['state']!='succeeded':raise ValueError(job['error'] or 'Tác vụ chưa hoàn thành')
        self.captions=[Caption(**c) for c in job['result']['captions']];self.refresh()


class BatchPage(QWidget):
    def __init__(self,host):
        super().__init__();self.host=host;self.groups={};self.plans=[];layout=QVBoxLayout(self);form=QFormLayout();layout.addLayout(form)
        self.folder=file_row(form,'Thư mục cha',host,True);self.audio=file_row(form,'Âm thanh chính (tùy chọn)',host)
        self.policy=QComboBox();self.policy.addItems(['speed','trim','loop','freeze']);form.addRow('Cách khớp thời lượng',self.policy)
        self.minimum=QDoubleSpinBox();self.minimum.setRange(.1,10);self.minimum.setValue(.5);form.addRow('Speed min',self.minimum)
        self.maximum=QDoubleSpinBox();self.maximum.setRange(.1,10);self.maximum.setValue(2);form.addRow('Speed max',self.maximum)
        self.mute=QCheckBox('Tắt tiếng gốc');form.addRow(self.mute)
        buttons(layout,host,[('Quét folder',self.scan),('Lập kế hoạch / dry-run',self.plan),('Preview đầu ra đầu tiên',self.preview),('Chạy toàn bộ',self.enqueue),('Theo dõi folder tự động',self.watch)])
        self.tree=QTreeWidget();self.tree.setHeaderLabels(['Kênh / video','Số tệp']);layout.addWidget(self.tree,1)
        self.summary=QLabel('Preset lấy từ editor hiện tại; loại folder khỏi danh sách không xóa dữ liệu.');self.summary.setWordWrap(True);layout.addWidget(self.summary)

    def scan(self):
        self.host.background(lambda p,c:scan_folders(Path(self.folder.text())),self.scanned)
    def scanned(self,groups):
        self.groups=groups;self.tree.clear()
        for channel,files in groups.items():
            parent=QTreeWidgetItem([channel,str(len(files))]);parent.setFlags(parent.flags()|Qt.ItemFlag.ItemIsUserCheckable|Qt.ItemFlag.ItemIsAutoTristate);parent.setCheckState(0,Qt.CheckState.Checked);self.tree.addTopLevelItem(parent)
            for file in files:
                child=QTreeWidgetItem([file,'']);child.setFlags(child.flags()|Qt.ItemFlag.ItemIsUserCheckable);child.setCheckState(0,Qt.CheckState.Checked);parent.addChild(child)
    def selected(self):
        result={}
        for index in range(self.tree.topLevelItemCount()):
            parent=self.tree.topLevelItem(index);files=[parent.child(i).text(0) for i in range(parent.childCount()) if parent.child(i).checkState(0)==Qt.CheckState.Checked]
            if files:result[parent.text(0)]=files
        return result
    def plan(self):
        groups=self.selected()
        if not groups:raise ValueError('Quét/chọn folder trước')
        preset=deepcopy(self.host.editor.composition);preset.mute_original=self.mute.isChecked()
        audio=self.audio.text() or None;policy=self.policy.currentText();minimum=self.minimum.value();maximum=self.maximum.value()
        self.host.background(lambda p,c:batch_plan(groups,preset,audio,policy,minimum,maximum),self.planned)
    def planned(self,plans):self.plans=plans;self.summary.setText(f'{len(plans)} đầu ra. '+ '\n'.join(p['output'] for p in plans[:4]))
    def preview(self):
        if not self.plans:raise ValueError('Lập kế hoạch trước')
        self.host.preview_composition(Composition.from_dict(self.plans[0]['composition']))
    def enqueue(self):
        if not self.plans:raise ValueError('Lập kế hoạch trước')
        enqueue_batch(self.host.store,self.plans);self.host.activate_queue()
    def watch(self):
        if not self.folder.text():raise ValueError('Chọn folder')
        watches=self.host.store.setting('watches',[]);watches.append({'folder':self.folder.text(),'preset':self.host.editor.composition.to_dict()});self.host.store.set_setting('watches',watches);self.host.message('Đã bật watcher khi app đang chạy; quản lý trong Cài đặt')


class MatrixModel(QAbstractTableModel):
    def __init__(self,page):super().__init__();self.page=page;self.rows=[];self.scenes=[];self.locked=set()
    def rowCount(self,parent=QModelIndex()):return len(self.rows)
    def columnCount(self,parent=QModelIndex()):return len(self.scenes)+2
    def headerData(self,section,orientation,role=Qt.ItemDataRole.DisplayRole):
        if role==Qt.ItemDataRole.DisplayRole:return ('Đầu ra' if section==0 else 'Công thức' if section==len(self.scenes)+1 else f'C{section}') if orientation==Qt.Orientation.Horizontal else str(section+1)
    def data(self,index,role=Qt.ItemDataRole.DisplayRole):
        if not index.isValid():return None
        row,col=index.row(),index.column()
        if role==Qt.ItemDataRole.BackgroundRole and (row,col) in self.locked:return QColor('#554336')
        if role==Qt.ItemDataRole.ToolTipRole and 0<col<=len(self.scenes):return self.rows[row][col-1].path
        if role in {Qt.ItemDataRole.DisplayRole,Qt.ItemDataRole.EditRole}:
            if col==0:return f'V{row+1:04}'
            if col==len(self.scenes)+1:return '+'.join(f'C{a.scene}G{a.index}' for a in self.rows[row])
            return 'G'+str(self.rows[row][col-1].index)
    def flags(self,index):
        flags=super().flags(index)
        if 0<index.column()<=len(self.scenes) and (index.row(),index.column()) not in self.locked:flags|=Qt.ItemFlag.ItemIsEditable
        return flags
    def setData(self,index,value,role=Qt.ItemDataRole.EditRole):
        if role!=Qt.ItemDataRole.EditRole:return False
        try:
            number=int(str(value).upper().removeprefix('G'));angle=next(a for a in self.scenes[index.column()-1] if a.index==number)
            old=self.rows[index.row()][index.column()-1];self.rows[index.row()][index.column()-1]=angle
            if not self.page.valid_rows():self.rows[index.row()][index.column()-1]=old;raise ValueError('Thay góc vi phạm unique/W/K/history')
            self.dataChanged.emit(index,index);return True
        except (ValueError,StopIteration) as exc:self.page.host.message(str(exc));return False
    def replace(self,scenes,rows):
        self.beginResetModel();self.scenes=scenes;self.rows=rows;self.locked=set();self.endResetModel()


class MatrixPage(QWidget):
    def __init__(self,host):
        super().__init__();self.host=host;self.scenes=[];self.old_history=[];layout=QVBoxLayout(self);form=QFormLayout();layout.addLayout(form)
        self.folder=file_row(form,'Folder chứa C1…Cn',host,True);self.audio=file_row(form,'Âm thanh chính',host);self.output=file_row(form,'Thư mục xuất',host,True)
        self.count=QSpinBox();self.count.setRange(1,100000);self.count.setValue(10);form.addRow('Số đầu ra',self.count)
        self.window=QSpinBox();self.window.setRange(0,10000);form.addRow('W — không lặp góc trong số video trước',self.window)
        self.different=QSpinBox();self.different.setRange(0,1000);form.addRow('K — số cảnh khác tối thiểu',self.different)
        self.compare=QCheckBox('K so với mọi hàng trong W (mặc định: hàng trước)');form.addRow(self.compare)
        self.seed=QSpinBox();self.seed.setRange(0,2147483647);form.addRow('Seed',self.seed)
        self.allocation=QComboBox();self.allocation.addItems(['proportional','equal']);form.addRow('Chia thời lượng',self.allocation)
        buttons(layout,host,[('Quét / sinh ma trận',self.generate),('Khóa / mở ô',self.lock),('Preview hàng',self.preview),('Xuất CSV',self.csv),('Render ma trận',self.enqueue)])
        self.table=QTableView();self.model=MatrixModel(self);self.table.setModel(self.model);self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents);layout.addWidget(self.table,1)
        self.summary=QLabel('Tên C/G là tên logic, giữ nguyên tệp nguồn. Double-click ô góc để sửa G1/G2…');self.summary.setWordWrap(True);layout.addWidget(self.summary)
    def scope(self):return self.host.project_id or hashlib.sha256(str(Path(self.folder.text()).resolve()).encode()).hexdigest()
    def generate(self):
        folder=Path(self.folder.text());n=self.count.value();seed=self.seed.value();w=self.window.value();k=self.different.value();compare=self.compare.isChecked()
        self.old_history=history(self.host.store,self.scope())
        locks={}
        for row,col in self.model.locked:
            if col>0 and col<=len(self.model.scenes):locks.setdefault(row,{})[col-1]=self.model.rows[row][col-1].hash
        old=self.old_history
        def work(progress,cancel):
            scenes=scan_scenes(folder);result=generate(scenes,n,seed,w,k,compare,old,seconds=10,locks=locks,cancel=cancel);return scenes,result
        def done(data):
            self.scenes,result=data;self.model.replace(self.scenes,result['rows']);self.summary.setText(f"{len(result['rows'])}/{result['requested']} hàng; tối đa lý thuyết {result['capacity']}. "+(result['reason'] or 'Đã tìm đủ theo ràng buộc.'))
            if not self.output.text():self.output.setText(str(folder.parent/(folder.name+' edit')))
        self.host.background(work,done)
    def valid_rows(self):
        previous=list(self.old_history);used={canonical(row) for row in previous}
        for row in self.model.rows:
            key=combination(row)
            if key in used or not valid_against(row,previous,self.window.value(),self.different.value(),self.compare.isChecked()):return False
            previous.append([a.hash for a in row]);used.add(key)
        return True
    def lock(self):
        for index in self.table.selectedIndexes():
            key=index.row(),index.column()
            if key in self.model.locked:self.model.locked.remove(key)
            else:self.model.locked.add(key)
        self.table.viewport().update()
    def preview(self):
        row=self.table.currentIndex().row()
        if row<0:raise ValueError('Chọn một hàng')
        preset=deepcopy(self.host.editor.composition);angles=self.model.rows[row];audio=self.audio.text() or None;allocation=self.allocation.currentText()
        self.host.background(lambda p,c:row_composition(angles,preset,audio,allocation),self.host.preview_composition)
    def enqueue(self):
        if not self.model.rows or not self.valid_rows():raise ValueError('Ma trận chưa hợp lệ')
        if not self.output.text():raise ValueError('Chọn thư mục xuất')
        rows=deepcopy(self.model.rows);preset=deepcopy(self.host.editor.composition);scope=self.scope();root=Path(self.output.text());audio=self.audio.text() or None;allocation=self.allocation.currentText()
        self.host.background(lambda p,c:enqueue_rows(self.host.store,scope,rows,preset,root,audio,allocation),lambda ids:(self.host.message(f'Đã enqueue {len(ids)} hàng'),self.host.activate_queue()))
    def csv(self):
        path,_=QFileDialog.getSaveFileName(self,'Xuất ma trận',filter='CSV (*.csv)')
        if path:
            with Path(path).open('w',encoding='utf-8-sig',newline='') as stream:
                writer=csv.writer(stream);writer.writerow(['Video',*[f'C{i+1}' for i in range(len(self.scenes))],'Formula'])
                for i,row in enumerate(self.model.rows):writer.writerow([i+1,*[f'G{a.index}' for a in row],'+'.join(f'C{a.scene}G{a.index}' for a in row)])


class QueuePage(QWidget):
    def __init__(self,host):
        super().__init__();self.host=host;layout=QVBoxLayout(self)
        buttons(layout,host,[('Tạm dừng / tiếp tục hàng đợi',self.pause),('Hủy việc chọn',self.cancel),('Thử lại việc chọn',self.retry),('Mở kết quả',self.open_result),('Chi tiết',self.detail)])
        self.table=QTableWidget(0,7);self.table.setHorizontalHeaderLabels(['Job','Loại','Trạng thái','Tiến độ','Đã tạo','ETA ước tính','Lỗi / kết quả'])
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers);self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents);self.table.horizontalHeader().setStretchLastSection(True);layout.addWidget(self.table,1)
        self.details=QPlainTextEdit();self.details.setReadOnly(True);self.details.setMaximumHeight(130);layout.addWidget(self.details)
    def selected(self):return [self.table.item(row,0).data(Qt.ItemDataRole.UserRole) for row in sorted({i.row() for i in self.table.selectedIndexes()})]
    def refresh(self):
        selected=set(self.selected());jobs=self.host.store.jobs();self.table.setRowCount(len(jobs))
        for row,job in enumerate(jobs):
            elapsed=max(0,time.time()-job['created']);p=job['progress'];eta=f'{elapsed*(1-p)/p:.0f}s' if .05<p<1 and job['state']=='running' else '—'
            values=[job['id'][:10],job['kind'],job['state'],f'{p*100:.1f}%',f'{elapsed:.0f}s',eta,job['error'] or ((job['result'] or {}).get('output',''))]
            for col,value in enumerate(values):
                item=QTableWidgetItem(str(value))
                if col==0:item.setData(Qt.ItemDataRole.UserRole,job['id'])
                self.table.setItem(row,col,item)
            if job['id'] in selected:self.table.selectRow(row)
    def pause(self):self.host.scheduler.paused=not self.host.scheduler.paused;self.host.message('Hàng đợi đã tạm dừng' if self.host.scheduler.paused else 'Hàng đợi đang chạy')
    def cancel(self):
        for key in self.selected():self.host.store.cancel(key)
    def retry(self):
        for key in self.selected():self.host.store.retry(key)
    def open_result(self):
        from PySide6.QtCore import QUrl
        for key in self.selected():
            result=self.host.store.job(key)['result'] or {};path=result.get('output')
            if path:QDesktopServices.openUrl(QUrl.fromLocalFile(str(Path(path).resolve())))
    def detail(self):
        if self.selected():self.details.setPlainText(json.dumps(self.host.store.job(self.selected()[0]),ensure_ascii=False,indent=2))


class SettingsPage(QWidget):
    def __init__(self,host):
        super().__init__();self.host=host;layout=QVBoxLayout(self);tabs=QTabWidget();layout.addWidget(tabs)
        tools=QWidget();box=QVBoxLayout(tools);buttons(box,host,[('Quét lại',self.scan),('Chọn đường dẫn',self.path),('Tải / cài công cụ chọn',self.install),('Cài phần bắt buộc thiếu',self.install_missing),('Rollback',self.rollback)])
        self.tools=QTableWidget(0,4);self.tools.setHorizontalHeaderLabels(['Công cụ','Trạng thái','Phiên bản','Đường dẫn / lý do']);self.tools.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents);self.tools.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers);box.addWidget(self.tools,1)
        note=QLabel('Bộ tải mặc định chạy module gói cùng app. Binary downloader ngoài được quét để chẩn đoán; chọn override thực thi hiện áp dụng FFmpeg/ffprobe/Chrome.');note.setWordWrap(True);box.addWidget(note);tabs.addTab(tools,'Công cụ')
        chrome=QWidget();box=QVBoxLayout(chrome);form=QFormLayout();box.addLayout(form)
        self.profile=QComboBox();form.addRow('Hồ sơ Chrome',self.profile);self.platform=QComboBox();self.platform.addItems(PLATFORMS);form.addRow('Nền tảng',self.platform)
        buttons(box,host,[('Tạo hồ sơ',self.create_profile),('Mở đăng nhập thật',self.login),('Tạo / copy mã ghép',self.pair),('Làm mới trạng thái',self.refresh_profiles),('Đăng ký native host',self.register),('Mở thư mục extension',self.extension),('Tài khoản mặc định',self.default)])
        self.accounts=QTableWidget(0,4);self.accounts.setHorizontalHeaderLabels(['Nền tảng','Hồ sơ','Danh tính xác định được','Phiên / bridge']);box.addWidget(self.accounts,1)
        label=QLabel('Một hồ sơ dùng nhiều nền tảng; nick thứ hai cùng nền tảng dùng hồ sơ khác. Website login, snapshot phiên và khả năng connector dùng phiên là các bước riêng.');label.setWordWrap(True);box.addWidget(label);tabs.addTab(chrome,'Chrome / tài khoản')
        provider=QWidget();form=QFormLayout(provider);self.provider=QComboBox();self.provider.addItems(['google','libre']);form.addRow('Bộ dịch',self.provider)
        self.endpoint=QLineEdit();form.addRow('LibreTranslate HTTPS endpoint',self.endpoint);self.key=QLineEdit();self.key.setEchoMode(QLineEdit.EchoMode.Password);form.addRow('API key (không đưa vào project)',self.key)
        self.budget=QSpinBox();self.budget.setRange(1,100000000);self.budget.setValue(100000);form.addRow('Hạn mức ký tự / ngày',self.budget)
        self.glossary=QPlainTextEdit('{}');form.addRow('Thuật ngữ JSON',self.glossary)
        save=QPushButton('Lưu cấu hình dịch');save.clicked.connect(host.guard(self.save_provider));form.addRow(save);tabs.addTab(provider,'Dịch / chi phí')
        resources=QWidget();form=QFormLayout(resources);self.resource_profile=QComboBox();self.resource_profile.addItems(['quiet','balanced','max']);self.resource_profile.setCurrentText(host.store.setting('resource_profile','balanced'));form.addRow('Profile tài nguyên',self.resource_profile)
        self.parallel=QSpinBox();self.parallel.setRange(1,16);self.parallel.setValue(host.store.setting('parallel',2));form.addRow('Tối đa worker',self.parallel)
        self.background=QCheckBox('Đóng cửa sổ thì tiếp tục chạy nền (nếu có system tray)');self.background.setChecked(host.store.setting('background',False));form.addRow(self.background)
        save=QPushButton('Lưu tài nguyên');save.clicked.connect(host.guard(self.save_resources));form.addRow(save)
        disable=QPushButton('Tắt tất cả watcher/lịch');disable.clicked.connect(host.guard(self.clear_auto));form.addRow(disable);tabs.addTab(resources,'Tự động / máy')
        self.refresh_profiles();self.scan();config=host.store.setting('translation',{});self.provider.setCurrentText(config.get('provider','google'));self.endpoint.setText(config.get('endpoint',''));self.budget.setValue(config.get('daily_limit',100000));self.glossary.setPlainText(json.dumps(config.get('glossary',{}),ensure_ascii=False,indent=2))

    def scan(self):self.host.background(lambda p,c:scan_tools(self.host.store.setting('tool_paths',{})),self.scanned)
    def scanned(self,tools):
        self.statuses=tools;self.tools.setRowCount(len(tools))
        for row,item in enumerate(tools):
            for col,text in enumerate((item.name,item.status,item.version,item.path or item.detail)):self.tools.setItem(row,col,QTableWidgetItem(text))
    def selected_tool(self):
        row=self.tools.currentRow()
        if row<0:raise ValueError('Chọn một công cụ')
        return self.tools.item(row,0).text()
    def path(self):
        name=self.selected_tool()
        if name not in {'ffmpeg','ffprobe','Google Chrome','node'}:raise ValueError('Bộ tải dùng module gói kèm; không tự thay engine bằng binary ngoài chưa kiểm chứng')
        path,_=QFileDialog.getOpenFileName(self.host,'Chọn executable')
        if path:
            overrides=self.host.store.setting('tool_paths',{});overrides[name]=path;self.host.store.set_setting('tool_paths',overrides);configure_tools(overrides);self.scan()
    def install(self):self.install_name(self.selected_tool())
    def install_name(self,name):
        if name=='Google Chrome':self.host.background(lambda p,c:install_chrome(self.host.store,p,c),lambda _:self.scan())
        elif name=='ffprobe':self.install_name('ffmpeg')
        elif name in {'gallery-dl'}:raise ValueError('gallery-dl được gói cùng ứng dụng; cập nhật qua bản app đã khóa dependency')
        else:self.host.background(lambda p,c:install(self.host.store,resolve_manifest(name),p,c),lambda _:self.scan())
    def install_missing(self):
        names={item.name for item in getattr(self,'statuses',[]) if item.status!='ready'}
        if {'ffmpeg','ffprobe'}&names:self.install_name('ffmpeg')
        if 'Google Chrome' in names:self.install_name('Google Chrome')
        if 'node' in names:self.install_name('node')
    def rollback(self):
        name=self.selected_tool()
        with self.host.store.connect() as c:versions=[r[0] for r in c.execute('SELECT version FROM tool_versions WHERE name=?',(name,))]
        if not versions:raise ValueError('Chưa có bản do app quản lý')
        version,ok=QInputDialog.getItem(self,'Rollback','Phiên bản',versions,0,False)
        if ok:rollback(self.host.store,name,version);self.scan()
    def refresh_profiles(self):
        self.profile.clear()
        for item in profiles(self.host.store):self.profile.addItem(item['label'],item['id'])
        accounts=bindings(self.host.store);self.accounts.setRowCount(len(accounts))
        for row,item in enumerate(accounts):
            for col,value in enumerate((item['platform'],item['label'],item['identity'] or 'chưa xác minh',item['status'])):self.accounts.setItem(row,col,QTableWidgetItem(value))
    def create_profile(self):
        name,ok=QInputDialog.getText(self,'Hồ sơ Chrome','Tên')
        if ok:create_profile(self.host.store,name);self.refresh_profiles()
    def current_profile(self):
        key=self.profile.currentData()
        if not key:raise ValueError('Tạo/chọn hồ sơ trước')
        return key
    def login(self):
        key=self.current_profile();platform=self.platform.currentText();chrome=self.host.store.setting('tool_paths',{}).get('Google Chrome')
        self.host.background(lambda p,c:login(self.host.store,key,platform,chrome),lambda _:(self.refresh_profiles(),self.host.downloads.refresh_accounts(),self.host.message('Chrome đã mở; đăng nhập trực tiếp rồi gửi phiên bằng bridge')))
    def pair(self):
        code=pairing_code(self.host.store,self.current_profile());QApplication.clipboard().setText(code);self.host.message('Mã ghép đã copy, hết hạn sau 5 phút. Dán trong extension của đúng hồ sơ này.')
    def register(self):
        path,_=QFileDialog.getOpenFileName(self,'Chọn fonesi-native-host.exe',filter='EXE (*.exe)')
        if path:register_host(Path(path));self.host.message('Đã đăng ký native host cho người dùng hiện tại')
    def extension(self):
        from ..paths import resource_directory
        from PySide6.QtCore import QUrl
        QDesktopServices.openUrl(QUrl.fromLocalFile(str(resource_directory('extension'))))
    def default(self):
        key=bind(self.host.store,self.current_profile(),self.platform.currentText());self.host.store.set_setting('default_binding:'+self.platform.currentText(),key);self.refresh_profiles();self.host.downloads.refresh_accounts()
    def save_provider(self):
        glossary=json.loads(self.glossary.toPlainText())
        if not isinstance(glossary,dict) or any(not isinstance(k,str) or not isinstance(v,str) for k,v in glossary.items()):raise ValueError('Thuật ngữ phải là object string → string')
        config={'provider':self.provider.currentText(),'endpoint':self.endpoint.text(),'daily_limit':self.budget.value(),'glossary':glossary};self.host.store.set_setting('translation',config)
        if self.key.text():
            variable='FONESI_GOOGLE_TRANSLATE_API_KEY' if self.provider.currentText()=='google' else 'FONESI_LIBRETRANSLATE_API_KEY'
            os.environ[variable]=self.key.text();self.key.clear()
            if os.name=='nt':
                from ..browser import protect
                with self.host.store.connect() as c:c.execute('INSERT OR REPLACE INTO secrets VALUES(?,?)',('api:'+variable,protect(os.environ[variable].encode())))
        self.host.message('Đã lưu cấu hình; API key chỉ ở bộ nhớ phiên này trên Linux, dùng DPAPI khi lưu trên Windows')
    def save_resources(self):
        self.host.store.set_setting('resource_profile',self.resource_profile.currentText());self.host.store.set_setting('parallel',self.parallel.value());self.host.store.set_setting('background',self.background.isChecked());self.host.scheduler.parallel=self.parallel.value();self.host.message('Đã lưu giới hạn tài nguyên')
    def clear_auto(self):
        self.host.store.set_setting('watches',[])
        with self.host.store.connect() as c:c.execute('DELETE FROM schedules')
        self.host.message('Đã tắt watcher/lịch, giữ nguyên dữ liệu')
