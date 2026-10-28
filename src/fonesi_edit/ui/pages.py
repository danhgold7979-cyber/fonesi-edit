"""Functional workflow pages; all expensive operations use workers or background tasks."""
from dataclasses import asdict
from copy import deepcopy
from pathlib import Path
import csv
import hashlib
import json
import math
import os
import time

from PySide6.QtCore import Qt,QAbstractTableModel,QModelIndex,QTimer
from PySide6.QtGui import QColor,QDesktopServices
from PySide6.QtWidgets import (QWidget,QVBoxLayout,QHBoxLayout,QFormLayout,QPushButton,QLabel,QLineEdit,QPlainTextEdit,
    QComboBox,QSpinBox,QDoubleSpinBox,QCheckBox,QFileDialog,QTableWidget,QTableWidgetItem,QTableView,QTreeWidget,
    QTreeWidgetItem,QHeaderView,QTabWidget,QInputDialog,QApplication,QMessageBox,QToolBar,QDialog,QDialogButtonBox)

from ..domain import Composition,Clip,Layer,canonical,atomic_json
from ..storage import TERMINAL
from ..batch import scan_folders,batch_plan,enqueue_batch
from ..matrix import scan_scenes,generate,history,combination,valid_against,matrix_rows_valid,regenerate_row,angle_usage,row_composition,enqueue_rows
from ..subtitles import Caption,read_captions,write_captions,caption_warnings
from ..downloads import platform_for,selectable_scan_url,selected_download_payloads
from ..browser import PLATFORMS,profiles,bindings,create_profile,bind,login,pairing_code
from ..native_host import register_host
from ..prototypes.tools import scan_tools,configure_tools
from ..dependencies import resolve_manifest,install,install_chrome,rollback,statuses
from ..automation import metrics,recommended_parallel,submit_once


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
        self.target_language=QComboBox();self.target_language.setEditable(True);self.target_language.addItems(['vi','en','zh','ja','ko','fr','de','es']);form.addRow('Ngôn ngữ dịch đích',self.target_language)
        self.bilingual=QCheckBox('Giữ sub gốc và bản dịch thành hai layer');form.addRow(self.bilingual)
        buttons(layout,host,[('Làm mới tài khoản',self.refresh_accounts),('Quét danh sách',lambda:self.submit('scan')),('Tải hàng loạt',lambda:self.submit('download')),('Xem kết quả quét',self.show_scan),('Đặt lịch',self.schedule)])
        selector=QHBoxLayout();layout.addLayout(selector);selector.addWidget(QLabel('Lần quét'))
        self.scans=QComboBox();selector.addWidget(self.scans,1)
        self.scans.currentIndexChanged.connect(lambda _:self.load_scan())
        buttons(layout,host,[('Chọn mục trên trang',lambda:self.check_scan_items(True)),('Bỏ chọn trang',lambda:self.check_scan_items(False)),('Trang trước',lambda:self.change_scan_page(-1)),('Trang sau',lambda:self.change_scan_page(1)),('Tải mục đã chọn',self.download_selected)])
        self.scan_page=0;self.scan_page_size=200;self.scan_selected={};self.loaded_scan_id=None
        self.scan_note=QLabel('Chưa chọn kết quả quét');self.scan_note.setWordWrap(True);layout.addWidget(self.scan_note)
        self.scan_tree=QTreeWidget();self.scan_tree.setHeaderLabels(['Nội dung / ID','Loại','Trạng thái URL'])
        self.scan_tree.itemChanged.connect(self.remember_scan_choice)
        self.scan_tree.setMinimumHeight(140);layout.addWidget(self.scan_tree,1)
        self.result=QPlainTextEdit();self.result.setReadOnly(True);self.result.setMaximumHeight(100);layout.addWidget(self.result)
        self.last_scan=None;self.refresh_accounts();self.refresh_scans()

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
            if self.auto.isChecked():
                preset=self.host.editor.composition.to_dict()
                if self.bilingual.isChecked():preset['adjustments']['bilingual_subtitles']=True
                p['workflow']={'preset':preset,'translate':self.translate.isChecked(),'language':self.target_language.currentText(),'translation':self.host.store.setting('translation',{})}
            yield p

    def submit(self,kind):
        payloads=list(self.payloads())
        for payload in payloads:
            key=self.host.store.submit(kind,payload)
            if kind=='scan':self.last_scan=key
        if kind=='scan':self.refresh_scans(preferred=self.last_scan)
        self.host.message(f'Đã thêm {len(payloads)} tác vụ {kind}');self.host.activate_queue()

    def refresh_scans(self,preferred=None):
        selected=preferred or self.scans.currentData() or self.last_scan
        self.scans.blockSignals(True);self.scans.clear()
        for job in self.host.store.jobs(limit=2000):
            if job['kind']!='scan':continue
            # Do not expose a potentially signed source URL in the scan chooser.
            self.scans.addItem(f"{job['state']} • {job['id'][:8]}",job['id'])
        index=self.scans.findData(selected)
        if index>=0:self.scans.setCurrentIndex(index)
        self.scans.blockSignals(False)

    def show_scan(self):
        self.refresh_scans()
        self.load_scan()

    def load_scan(self):
        self.scan_tree.blockSignals(True)
        self.scan_tree.clear()
        job_id=self.scans.currentData()
        if job_id != self.loaded_scan_id:
            self.loaded_scan_id=job_id;self.scan_page=0
        if not job_id:
            self.scan_note.setText('Chưa có kết quả quét')
            self.result.clear();self.scan_tree.blockSignals(False)
            return
        job=self.host.store.job(job_id)
        if job['state']!='succeeded':
            self.scan_note.setText(f"Quét {job['state']}; chưa có danh sách xác nhận.")
            self.result.setPlainText('Lỗi: '+str(job['error'] or 'Chưa có kết quả'))
            self.scan_tree.blockSignals(False)
            return
        data=job['result'] or {}
        items=data.get('items') or []
        complete=data.get('complete')
        completeness='đã xác nhận đủ' if complete is True else 'quét một phần' if complete is False else 'chưa rõ đã quét hết'
        last_page=max(0,(len(items)-1)//self.scan_page_size)
        self.scan_page=max(0,min(self.scan_page,last_page))
        start=self.scan_page*self.scan_page_size;end=min(len(items),start+self.scan_page_size)
        chosen=self.scan_selected.setdefault(job_id,set())
        self.scan_note.setText(f"{data.get('platform','Nguồn')} • {len(items)} mục • {completeness} • trang {self.scan_page+1}/{last_page+1} • đã chọn {len(chosen)}. Chỉ chọn mục được tải.")
        self.result.setPlainText('Lựa chọn được giữ khi chuyển trang; tài khoản và thư mục lấy từ snapshot quét, không tự quét lại nguồn.')
        parent=QTreeWidgetItem([f"Job {job_id[:8]} • {start+1 if items else 0}–{end}",'Nguồn',completeness])
        self.scan_tree.addTopLevelItem(parent)
        first_by_url={}
        for index,item in enumerate(items):
            if not isinstance(item,dict):continue
            safe=selectable_scan_url(item.get('url'))
            if safe and safe not in first_by_url:
                first_by_url[safe]=index
        for index in range(start,end):
            item=items[index]
            if not isinstance(item,dict):continue
            safe=selectable_scan_url(item.get('url'))
            duplicate=bool(safe) and first_by_url.get(safe)!=index
            selectable=bool(safe) and item.get('selectable') is not False and not duplicate
            label=str(item.get('title') or item.get('id') or 'Mục không tên')[:160]
            state='Có thể tải' if selectable else ('URL trùng trong lần quét' if duplicate else str(item.get('reason') or 'Thiếu URL tải lại an toàn'))
            child=QTreeWidgetItem([label,str(item.get('kind','video')),state])
            child.setData(0,Qt.ItemDataRole.UserRole,index)
            if selectable:
                child.setFlags(child.flags()|Qt.ItemFlag.ItemIsUserCheckable)
                child.setCheckState(0,Qt.CheckState.Checked if index in chosen else Qt.CheckState.Unchecked)
            else:
                child.setFlags(child.flags() & ~(Qt.ItemFlag.ItemIsEnabled | Qt.ItemFlag.ItemIsUserCheckable))
            parent.addChild(child)
        parent.setExpanded(True)
        self.scan_tree.blockSignals(False)

    def remember_scan_choice(self,item,column):
        index=item.data(0,Qt.ItemDataRole.UserRole)
        job_id=self.scans.currentData()
        if type(index) is not int or not job_id:return
        chosen=self.scan_selected.setdefault(job_id,set())
        if item.checkState(0)==Qt.CheckState.Checked:chosen.add(index)
        else:chosen.discard(index)
        job=self.host.store.job(job_id)
        data=job.get('result') or {}
        count=len(data.get('items') or [])
        total=max(1,(count-1)//self.scan_page_size+1)
        completeness='quét một phần' if data.get('complete') is False else 'chưa rõ đã quét hết' if data.get('complete') is None else 'đã xác nhận đủ'
        self.scan_note.setText(f"{data.get('platform','Nguồn')} • {count} mục • {completeness} • trang {self.scan_page+1}/{total} • đã chọn {len(chosen)}")

    def change_scan_page(self,delta):
        job_id=self.scans.currentData()
        if not job_id:return
        job=self.host.store.job(job_id)
        items=(job.get('result') or {}).get('items') or []
        maximum=max(0,(len(items)-1)//self.scan_page_size)
        target=max(0,min(maximum,self.scan_page+delta))
        if target!=self.scan_page:
            self.scan_page=target
            self.load_scan()

    def check_scan_items(self,checked):
        root=self.scan_tree.topLevelItem(0)
        if root is None:return
        for index in range(root.childCount()):
            item=root.child(index)
            if item.flags() & Qt.ItemFlag.ItemIsUserCheckable:
                item.setCheckState(0,Qt.CheckState.Checked if checked else Qt.CheckState.Unchecked)

    def download_selected(self):
        job_id=self.scans.currentData()
        if not job_id:raise ValueError('Chưa chọn một lần quét')
        job=self.host.store.job(job_id)
        if self.scan_tree.topLevelItem(0) is None:
            raise ValueError('Hãy xem kết quả quét trước khi chọn')
        indexes=sorted(self.scan_selected.get(job_id,set()))
        requests=selected_download_payloads(job,indexes)
        account=job['payload'].get('account_ref')
        if account:
            binding=next((item for item in bindings(self.host.store)
                          if item['id']==account),None)
            if not binding or binding['platform']!=platform_for(job['payload']['url']):
                raise PermissionError('Tài khoản quét không tồn tại hoặc khác nền tảng; không chuyển sang công khai')
        for payload in requests:
            # Stable per-scan identity means pressing Download twice does not
            # enqueue the same selected source twice; use Queue/Retry instead.
            submit_once(self.host.store,'download',payload,
                        'scan-item:'+job_id+':'+payload['url'])
        self.host.message(f"Đã xếp {len(requests)} mục từ scan {job_id[:8]}; mục đã xếp trước không tạo trùng (dùng Retry nếu cần)")
        self.host.activate_queue()

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
        buttons(layout,host,[('Mở SRT/VTT/ASS',self.open),('Lưu sub',self.save),('Thêm câu',self.add),('Tách câu',self.split),('Gộp câu chọn',self.merge),('Tìm/thay',self.find_replace),('Dịch thời gian',self.shift),('Gắn vào clip',self.attach)])
        row=QHBoxLayout();layout.addLayout(row);self.source=QComboBox();self.source.setEditable(True);self.source.addItems(['auto','zh','en','vi','ja','ko']);row.addWidget(self.source)
        self.target=QComboBox();self.target.setEditable(True);self.target.addItems(['vi','en','zh','ja','ko','fr','de','es']);row.addWidget(self.target)
        self.bilingual=QCheckBox('Song ngữ gốc + dịch');row.addWidget(self.bilingual)
        b=QPushButton('Dịch qua hàng đợi');b.clicked.connect(host.guard(self.translate));row.addWidget(b)
        b=QPushButton('Chỉ dịch câu chọn');b.clicked.connect(host.guard(lambda:self.translate(True)));row.addWidget(b)
        b=QPushButton('Nạp kết quả dịch');b.clicked.connect(host.guard(self.load_translation));row.addWidget(b)
        self.table=QTableWidget(0,5);self.table.setHorizontalHeaderLabels(['Bắt đầu s','Kết thúc s','Bản gốc','Bản dịch / nội dung','Khóa'])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch);self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows);layout.addWidget(self.table,1)
        self.warning=QLabel();self.warning.setWordWrap(True);layout.addWidget(self.warning)
        self.draft=QTimer(self);self.draft.setSingleShot(True);self.draft.setInterval(500);self.draft.timeout.connect(host.guard(self.persist))
        self.table.itemChanged.connect(lambda item:self.draft.start())
        draft=host.store.setting('subtitle_draft')
        if draft:
            self.table.blockSignals(True);self.captions=[];self.table.setRowCount(len(draft['rows']))
            for row,values in enumerate(draft['rows']):
                self.captions.append(Caption(0,1,values[3],values[2],values[4],values[5]))
                for col in range(4):self.table.setItem(row,col,QTableWidgetItem(values[col]))
                check=QTableWidgetItem();check.setCheckState(Qt.CheckState.Checked if values[4] else Qt.CheckState.Unchecked);self.table.setItem(row,4,check)
            self.table.blockSignals(False);self.source.setCurrentText(draft['source']);self.target.setCurrentText(draft['target']);self.bilingual.setChecked(draft.get('bilingual',False))

    def refresh(self):
        self.table.blockSignals(True);self.table.setUpdatesEnabled(False)
        self.table.setRowCount(len(self.captions))
        for row,c in enumerate(self.captions):
            for col,value in enumerate((f'{c.start_ms/1000:.3f}',f'{c.end_ms/1000:.3f}',c.source_text or c.text,c.text)):
                self.table.setItem(row,col,QTableWidgetItem(value))
            check=QTableWidgetItem();check.setCheckState(Qt.CheckState.Checked if c.locked else Qt.CheckState.Unchecked);self.table.setItem(row,4,check)
        self.warning.setText('\n'.join(caption_warnings(self.captions)[:10]))
        self.table.setUpdatesEnabled(True);self.table.blockSignals(False);self.draft.start()

    def persist(self):
        rows=[]
        for row,cue in enumerate(self.captions):rows.append([*[self.table.item(row,col).text() if self.table.item(row,col) else '' for col in range(4)],self.table.item(row,4).checkState()==Qt.CheckState.Checked,cue.id])
        self.host.store.set_setting('subtitle_draft',{'rows':rows,'source':self.source.currentText(),'target':self.target.currentText(),'bilingual':self.bilingual.isChecked()})

    def collect(self):
        result=[]
        for row,old in enumerate(self.captions):
            result.append(Caption(round(float(self.table.item(row,0).text())*1000),round(float(self.table.item(row,1).text())*1000),self.table.item(row,3).text(),self.table.item(row,2).text(),self.table.item(row,4).checkState()==Qt.CheckState.Checked,old.id))
        return result

    def open(self):
        path,_=QFileDialog.getOpenFileName(self,'Mở phụ đề',filter='Sub (*.srt *.vtt *.ass)')
        if path:self.host.background(lambda p,c:read_captions(Path(path)),self.loaded)
    def loaded(self,captions):self.captions=captions;self.refresh()

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
        if not captions:raise ValueError('Chưa có câu phụ đề')
        bilingual=self.bilingual.isChecked()
        if bilingual and not any(c.source_text and c.source_text!=c.text for c in captions):raise ValueError('Chưa có bản gốc khác bản dịch; dịch/nhập bản gốc trước khi bật song ngữ')
        key=hashlib.sha256(canonical([asdict(c) for c in captions]).encode()).hexdigest()[:20];path=self.host.data/'subtitles'/(key+'.srt')
        if not path.exists():write_captions(path,captions)
        original_path=path.with_name(key+'.source.srt')
        if bilingual and not original_path.exists():write_captions(original_path,[Caption(c.start_ms,c.end_ms,c.source_text or c.text) for c in captions])
        index=max(0,editor.clips.currentRow());clip=editor.composition.clips[index];editor.begin();clip.subtitles=None
        for role,sub_path,language in [('target',path,self.target.currentText()),*([('source',original_path,self.source.currentText())] if bilingual else [])]:
            existing=next((layer for layer in editor.composition.layers if layer.kind=='subtitle' and clip.id in layer.clip_ids and layer.style.get('subtitle_role','target')==role),None)
            if existing:existing.path=str(sub_path);existing.text=(captions[0].source_text if role=='source' else captions[0].text) if captions else ''
            else:
                existing=Layer(kind='subtitle',name='Sub gốc' if role=='source' else 'Sub dịch',path=str(sub_path),text=(captions[0].source_text if role=='source' else captions[0].text) if captions else '',x=.1,y=.66 if role=='source' else .82,width=.8,height=.14,style={**deepcopy(editor.composition.subtitle_style),'subtitle_role':role,'font_size':24 if role=='source' else 32},clip_ids=[clip.id]);editor.composition.layers.append(existing)
            if language!='auto':existing.style['subtitle_languages']=[language]
            if role=='target':selected=existing.id
        if not bilingual:editor.composition.layers=[layer for layer in editor.composition.layers if not (layer.kind=='subtitle' and clip.id in layer.clip_ids and layer.style.get('subtitle_role')=='source')]
        editor.composition.adjustments['bilingual_subtitles']=bilingual;editor.selected_id=selected;editor.selected_ids={selected};editor.commit('Gắn sub');self.host.nav.setCurrentWidget(editor)
        self.host.message('Đã gắn sub; video nguồn giữ nguyên')

    def translate(self,selected_only=False):
        captions=self.collect()
        if not captions:raise ValueError('Chưa có cue')
        self.translation_snapshot={c.id:asdict(c) for c in captions}
        if selected_only:
            selected={i.row() for i in self.table.selectedIndexes()}
            if not selected:raise ValueError('Chọn câu cần dịch')
            captions=[c for i,c in enumerate(captions) if i in selected]
        output=self.host.data/'subtitles'/('translation-'+str(time.time_ns())+'.srt')
        self.last_job=self.host.store.submit('translate',{'captions':[asdict(c) for c in captions],'source_language':self.source.currentText(),'target_language':self.target.currentText(),'config':self.host.store.setting('translation',{}),'output':str(output)})
        self.host.message('Đã đưa bản chụp sub vào hàng đợi; không tự ghi đè các sửa tay tiếp theo')

    def load_translation(self):
        if not self.last_job:return
        job=self.host.store.job(self.last_job)
        if job['state']!='succeeded':raise ValueError(job['error'] or 'Tác vụ chưa hoàn thành')
        current=self.collect();results={c['id']:Caption(**c) for c in job['result']['captions']};changed=0
        for i,cue in enumerate(current):
            if cue.id in results and not cue.locked and asdict(cue)==getattr(self,'translation_snapshot',{}).get(cue.id):current[i]=results[cue.id];changed+=1
        self.captions=current;self.refresh();self.host.message(f'Đã nạp {changed} câu; giữ các câu đã sửa/khóa sau khi gửi dịch')

    def shift(self):
        cues=self.collect();value,ok=QInputDialog.getDouble(self,'Dịch thời gian','Số giây (+ trễ, − sớm)',0,-100000,100000,3)
        if ok:
            delta=round(value*1000)
            if any(c.start_ms+delta<0 for c in cues):raise ValueError('Offset làm cue bắt đầu trước 0')
            for cue in cues:cue.start_ms+=delta;cue.end_ms+=delta
            self.captions=cues;self.refresh()
    def find_replace(self):
        cues=self.collect();find,ok=QInputDialog.getText(self,'Tìm/thay','Nội dung cần tìm')
        if not ok or not find:return
        replacement,ok=QInputDialog.getText(self,'Tìm/thay','Thay bằng')
        if not ok:return
        for cue in cues:
            if not cue.locked:cue.text=cue.text.replace(find,replacement)
        self.captions=cues;self.refresh()


class BatchPage(QWidget):
    def __init__(self,host):
        super().__init__();self.host=host;self.groups={};self.plans=[];layout=QVBoxLayout(self);form=QFormLayout();layout.addLayout(form)
        self.folder=file_row(form,'Thư mục cha',host,True);self.audio=file_row(form,'Âm thanh chính chung (tùy chọn)',host)
        self.audio_folder=file_row(form,'Thư mục nhiều audio (khi ghép riêng)',host,True)
        self.audio_mode=QComboBox()
        for label,mode in [('Một audio cho cả lô','shared'),('Trùng tên video/audio','by_name'),('Theo thứ tự danh sách','ordered'),('Ngẫu nhiên với seed cố định','random')]:
            self.audio_mode.addItem(label,mode)
        form.addRow('Ghép âm thanh chính',self.audio_mode)
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
        audio_mode=self.audio_mode.currentData() or 'shared';audio_folder=self.audio_folder.text() or None
        self.host.background(lambda p,c:batch_plan(groups,preset,audio,policy,minimum,maximum,
                            audio_mode=audio_mode,audio_folder=audio_folder),self.planned)
    def planned(self,plans):
        self.plans=plans
        preview='\n'.join(p['output']+(' • audio: '+Path(p['audio_source']).name if p.get('audio_source') else ' • audio: preset/gốc') for p in plans[:4])
        self.summary.setText(f'{len(plans)} đầu ra. '+preview)
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
        if (role!=Qt.ItemDataRole.EditRole or not index.isValid()
                or not (0<=index.row()<len(self.rows))
                or not (1<=index.column()<=len(self.scenes))
                or (index.row(),index.column()) in self.locked):
            return False
        try:
            number=int(str(value).upper().removeprefix('G'))
            angle=next(a for a in self.scenes[index.column()-1] if a.index==number)
            old=self.rows[index.row()][index.column()-1]
            self.rows[index.row()][index.column()-1]=angle
            if not self.page.valid_rows():
                self.rows[index.row()][index.column()-1]=old
                raise ValueError('Thay góc vi phạm unique/W/K/history')
            # Formula column depends on every scene cell: refresh together.
            self.dataChanged.emit(index,self.index(index.row(),len(self.scenes)+1))
            return True
        except (ValueError,StopIteration) as exc:
            self.page.host.message(str(exc))
            return False
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
        self.allocation=QComboBox();self.allocation.addItems(['proportional','equal','weights','manual']);form.addRow('Chia thời lượng',self.allocation)
        self.scene_weights=QLineEdit();self.scene_weights.setPlaceholderText('Trọng số từng cảnh, ví dụ: 1,2,1');form.addRow('Trọng số cảnh (nếu chọn weights)',self.scene_weights)
        self.scene_durations=QLineEdit();self.scene_durations.setPlaceholderText('Thời lượng mỗi cảnh (s), ví dụ: 2.5,4,3');form.addRow('Giây/cảnh (nếu chọn manual)',self.scene_durations)
        buttons(layout,host,[('Quét / sinh ma trận',self.generate),('Khóa / mở ô',self.lock),('Tạo lại hàng chọn',self.regenerate),('Preview hàng',self.preview),('Thống kê góc',self.statistics),('Xuất CSV',self.csv),('Render ma trận',self.enqueue),('Preview đổi tên C/G',self.rename_preview),('Hoàn tác / phục hồi đổi tên',self.undo_rename)])
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
        return matrix_rows_valid(self.model.rows,self.old_history,
            self.window.value(),self.different.value(),self.compare.isChecked())

    def regenerate(self):
        selected=self.table.currentIndex()
        row=selected.row() if selected.isValid() else -1
        if row<0 or row>=len(self.model.rows):
            raise ValueError('Chọn một hàng của ma trận để tạo lại')
        if not self.valid_rows():
            raise ValueError('Ma trận hiện tại vi phạm history/W/K; sinh lại trước')
        scenes=[list(scene) for scene in self.model.scenes]
        current=[list(item) for item in self.model.rows]
        baseline=[combination(item) for item in current]
        previous=[list(entry) for entry in self.old_history]
        scope=self.scope()
        w,k,compare=self.window.value(),self.different.value(),self.compare.isChecked()
        seed=self.seed.value()
        locked={column-1:current[row][column-1].hash
                for r,column in self.model.locked
                if r==row and 1<=column<=len(scenes)}
        def work(progress,cancel):
            latest=history(self.host.store,scope)
            if latest!=previous:
                raise ValueError('Lịch sử đặt chỗ đã thay đổi; hãy sinh lại ma trận')
            return regenerate_row(scenes,current,row,seed,w,k,compare,
                                  latest,locked,seconds=5,cancel=cancel)
        def done(result):
            # Async worker must never overwrite edits, locks or constraints
            # the user changed while regeneration was running.
            if ([combination(item) for item in self.model.rows]!=baseline
                    or [[angle.hash for angle in scene] for scene in self.model.scenes]
                       !=[[angle.hash for angle in scene] for scene in scenes]
                    or self.scope()!=scope
                    or self.old_history!=previous
                    or history(self.host.store,scope)!=previous
                    or (self.window.value(),self.different.value(),
                        self.compare.isChecked(),self.seed.value())!=(w,k,compare,seed)
                    or {column-1:self.model.rows[row][column-1].hash
                        for r,column in self.model.locked
                        if r==row and 1<=column<=len(scenes)}!=locked):
                self.host.message('Ma trận/khóa đã đổi khi đang tạo lại; kết quả cũ bị bỏ')
                return
            self.model.rows[row]=result['row']
            self.model.dataChanged.emit(self.model.index(row,0),
                self.model.index(row,len(scenes)+1))
            self.table.selectRow(row)
            self.summary.setText(f"Đã tạo lại hàng V{row+1:04}; thử {result['attempts']} tổ hợp. Các hàng khác và ô khóa giữ nguyên; W/K đã kiểm tra toàn ma trận.")
        self.host.background(work,done)

    def lock(self):
        for index in self.table.selectedIndexes():
            if not index.isValid() or not (1<=index.column()<=len(self.model.scenes)):
                continue
            key=index.row(),index.column()
            if key in self.model.locked:self.model.locked.remove(key)
            else:self.model.locked.add(key)
        self.table.viewport().update()
    def statistics(self):
        if not self.model.rows:raise ValueError('Chưa có ma trận để thống kê')
        groups=angle_usage(self.model.scenes,self.model.rows)
        lines=['Thống kê góc trong ma trận đã lập (không phải số video đã render thành công):']
        for group in groups:
            lines.append(f"C{group[0]['scene']}: "+
                '  '.join(f"G{item['angle']}={item['uses']}" for item in group))
        self.summary.setText('\n'.join(lines))
        return groups

    def duration_weights(self):
        if self.allocation.currentText()!='weights':
            return None
        values=[part.strip() for part in self.scene_weights.text().split(',')]
        if not values or any(not part for part in values):
            raise ValueError('Nhập trọng số cho từng cảnh, phân cách bằng dấu phẩy')
        try:
            weights=[float(part) for part in values]
        except ValueError:
            raise ValueError('Trọng số cảnh phải là số dương, dùng dấu chấm thập phân') from None
        if len(weights)!=len(self.model.scenes):
            raise ValueError('Số trọng số phải bằng số cảnh trong ma trận')
        if any(not math.isfinite(value) or value<=0 for value in weights):
            raise ValueError('Mọi trọng số cảnh phải dương và hữu hạn')
        return weights

    def duration_scene_lengths(self):
        if self.allocation.currentText()!='manual':
            return None
        values=[part.strip() for part in self.scene_durations.text().split(',')]
        if not values or any(not part for part in values):
            raise ValueError('Nhập thời lượng giây cho mỗi cảnh, phân cách bằng dấu phẩy')
        try:
            lengths=[float(part) for part in values]
        except ValueError:
            raise ValueError('Thời lượng cảnh phải là số, dùng dấu chấm thập phân') from None
        if len(lengths)!=len(self.model.scenes):
            raise ValueError('Số thời lượng phải bằng số cảnh trong ma trận')
        if any(not math.isfinite(value) or value<=0 for value in lengths):
            raise ValueError('Mỗi thời lượng cảnh phải dương và hữu hạn')
        return lengths

    def preview(self):
        row=self.table.currentIndex().row()
        if row<0:raise ValueError('Chọn một hàng')
        preset=deepcopy(self.host.editor.composition);angles=self.model.rows[row];audio=self.audio.text() or None;allocation=self.allocation.currentText()
        weights=self.duration_weights();durations=self.duration_scene_lengths()
        self.host.background(lambda p,c:row_composition(angles,preset,audio,allocation,weights=weights,manual_durations=durations),self.host.preview_composition)
    def enqueue(self):
        if not self.model.rows or not self.valid_rows():raise ValueError('Ma trận chưa hợp lệ')
        if not self.output.text():raise ValueError('Chọn thư mục xuất')
        rows=deepcopy(self.model.rows);preset=deepcopy(self.host.editor.composition);scope=self.scope();root=Path(self.output.text());audio=self.audio.text() or None;allocation=self.allocation.currentText()
        weights=self.duration_weights();durations=self.duration_scene_lengths()
        w,k,compare=self.window.value(),self.different.value(),self.compare.isChecked()
        self.host.background(lambda p,c:enqueue_rows(self.host.store,scope,rows,preset,root,audio,allocation,window=w,different=k,compare_window=compare,weights=weights,manual_durations=durations),lambda ids:(self.host.message(f'Đã enqueue {len(ids)} hàng'),self.host.activate_queue()))
    def csv(self):
        path,_=QFileDialog.getSaveFileName(self,'Xuất ma trận',filter='CSV (*.csv)')
        if path:
            with Path(path).open('w',encoding='utf-8-sig',newline='') as stream:
                writer=csv.writer(stream);writer.writerow(['Video',*[f'C{i+1}' for i in range(len(self.scenes))],'Formula'])
                for i,row in enumerate(self.model.rows):writer.writerow([i+1,*[f'G{a.index}' for a in row],'+'.join(f'C{a.scene}G{a.index}' for a in row)])

    def rename_preview(self):
        if not self.scenes:raise ValueError('Quét cảnh trước')
        from ..renaming import scene_rename_plan,apply_rename
        operations=scene_rename_plan(self.scenes)
        if not operations:raise ValueError('Tên C/G đã đúng')
        dialog=QDialog(self);dialog.setWindowTitle('Đổi tên thật • video và sub đi kèm');dialog.resize(1000,500);layout=QVBoxLayout(dialog)
        note=QLabel('Kiểm tra ánh xạ trước khi đổi tên. Giữ nguyên nội dung; lưu journal để hoàn tác. Không đổi tên khi queue đang dùng nguồn.');note.setWordWrap(True);layout.addWidget(note)
        table=QTableWidget(len(operations),2);table.setHorizontalHeaderLabels(['Tên hiện tại','Tên mới']);table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers);table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        for row,op in enumerate(operations):table.setItem(row,0,QTableWidgetItem(op['source']));table.setItem(row,1,QTableWidgetItem(op['target']))
        layout.addWidget(table);controls=QDialogButtonBox(QDialogButtonBox.StandardButton.Apply|QDialogButtonBox.StandardButton.Cancel);controls.button(QDialogButtonBox.StandardButton.Apply).setText('Đổi tên theo bảng');controls.button(QDialogButtonBox.StandardButton.Apply).clicked.connect(dialog.accept);controls.rejected.connect(dialog.reject);layout.addWidget(controls)
        if dialog.exec()==QDialog.DialogCode.Accepted:
            root=Path(self.folder.text()).resolve();self.rename_run(lambda cancel:apply_rename(root,operations,cancel),operations)

    def rename_run(self,function,operations):
        paths={p for op in operations for p in (op['source'],op['target'])}
        for job in self.host.store.jobs(100000):
            if job['state'] in {'pending','running','blocked'} and any(clip.get('path') in paths for clip in job['payload'].get('composition',{}).get('clips',[])):raise ValueError('Nguồn còn được queue dùng; hủy/hoàn tất các job đó trước khi đổi tên')
        paused=self.host.scheduler.paused;self.host.scheduler.paused=True
        def done(result):
            self.host.relink_renamed(result['mapping']);self.scenes=[];self.model.replace([],[]);self.host.message(f"Đã đổi {result['count']} tệp. Journal: {result['journal']}")
        task=self.host.background(lambda progress,cancel:function(cancel),done)
        task.finished.connect(lambda:setattr(self.host.scheduler,'paused',paused))

    def undo_rename(self):
        from ..renaming import undo_rename,recover_rename
        path,_=QFileDialog.getOpenFileName(self,'Chọn journal trong .fonesi-renames',str(Path(self.folder.text())/'.fonesi-renames'),'JSON (*.json)')
        if not path:return
        data=json.loads(Path(path).read_text(encoding='utf-8'));function=undo_rename if data.get('state')=='completed' else recover_rename
        self.rename_run(lambda cancel:function(Path(path),cancel),data['operations'])


class QueuePage(QWidget):
    def __init__(self,host):
        super().__init__();self.host=host;layout=QVBoxLayout(self)
        buttons(layout,host,[('Tạm dừng / tiếp tục hàng đợi',self.pause),('Hủy việc chọn',self.cancel),('Thử lại việc chọn',self.retry),('Ưu tiên lên',lambda:self.priority(10)),('Ưu tiên xuống',lambda:self.priority(-10)),('Mở kết quả',self.open_result),('Chi tiết',self.detail)])
        self.table=QTableWidget(0,7);self.table.setHorizontalHeaderLabels(['Job','Loại','Trạng thái','Tiến độ','Đã chạy','ETA ước tính','Lỗi / kết quả'])
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers);self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents);self.table.horizontalHeader().setStretchLastSection(True);layout.addWidget(self.table,1)
        self.details=QPlainTextEdit();self.details.setReadOnly(True);self.details.setMaximumHeight(130);layout.addWidget(self.details)
    def selected(self):return [self.table.item(row,0).data(Qt.ItemDataRole.UserRole) for row in sorted({i.row() for i in self.table.selectedIndexes()})]
    def refresh(self):
        selected=set(self.selected());jobs=self.host.store.jobs();self.table.setRowCount(len(jobs))
        for row,job in enumerate(jobs):
            elapsed=max(0,(time.time() if job['state']=='running' else job['updated'])-(job['started'] or job['updated']));p=job['progress'];eta=f'{elapsed*(1-p)/p:.0f}s' if .05<p<1 and job['state']=='running' else '—'
            status=job['state']+(' • cảnh báo' if (job['result'] or {}).get('warnings') else '')
            progress='Đang chạy / chưa biết tổng' if job['state']=='running' and p==0 else f'{p*100:.1f}%'
            values=[job['id'][:10],job['kind'],status,progress,f'{elapsed:.0f}s',eta,job['error'] or ((job['result'] or {}).get('output',''))]
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
    def priority(self,delta):
        with self.host.store.connect() as c:
            for key in self.selected():c.execute("UPDATE jobs SET priority=priority+? WHERE id=? AND state='pending'",(delta,key))
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
        buttons(box,host,[('Tạo hồ sơ',self.create_profile),('Đổi tên hồ sơ',self.rename_profile),('Mở đăng nhập thật',self.login),('Tạo / copy mã ghép',self.pair),('Thu hồi ghép extension',self.revoke_pairing),('Làm mới trạng thái',self.refresh_profiles),('Đăng ký native host',self.register),('Mở thư mục extension',self.extension),('Tài khoản mặc định',self.default),('Quên phiên trong app',self.forget_session)])
        self.accounts=QTableWidget(0,4);self.accounts.setHorizontalHeaderLabels(['Nền tảng','Hồ sơ','Danh tính xác định được','Phiên / bridge']);box.addWidget(self.accounts,1)
        label=QLabel('Một hồ sơ dùng nhiều nền tảng; nick thứ hai cùng nền tảng dùng hồ sơ khác. Website login, snapshot phiên và khả năng connector dùng phiên là các bước riêng.');label.setWordWrap(True);box.addWidget(label);tabs.addTab(chrome,'Chrome / tài khoản')
        provider=QWidget();form=QFormLayout(provider);self.provider=QComboBox();self.provider.addItems(['google','libre']);form.addRow('Bộ dịch',self.provider)
        self.endpoint=QLineEdit();form.addRow('LibreTranslate HTTPS endpoint',self.endpoint);self.key=QLineEdit();self.key.setEchoMode(QLineEdit.EchoMode.Password);form.addRow('API key (không đưa vào project)',self.key)
        self.budget=QSpinBox();self.budget.setRange(1,100000000);self.budget.setValue(100000);form.addRow('Hạn mức ký tự / ngày',self.budget)
        self.glossary=QPlainTextEdit('{}');form.addRow('Thuật ngữ JSON',self.glossary)
        save=QPushButton('Lưu cấu hình dịch');save.clicked.connect(host.guard(self.save_provider));form.addRow(save);tabs.addTab(provider,'Dịch / chi phí')
        resources=QWidget();form=QFormLayout(resources);self.resource_profile=QComboBox();self.resource_profile.addItems(['quiet','balanced','max']);self.resource_profile.setCurrentText(host.store.setting('resource_profile','balanced'));form.addRow('Profile tài nguyên',self.resource_profile)
        self.parallel=QSpinBox();self.parallel.setRange(1,16);self.parallel.setValue(host.store.setting('parallel',2));form.addRow('Tối đa worker',self.parallel)
        self.job_limits={};limits=host.store.setting('job_limits',{'scan':2,'download':2,'render':1,'translate':1})
        for key,label in [('scan','Quét song song'),('download','Tải song song'),('render','Edit/render song song'),('translate','Dịch song song')]:
            field=QSpinBox();field.setRange(1,16);field.setValue(limits.get(key,1));self.job_limits[key]=field;form.addRow(label,field)
        suggestion=QPushButton('Điền gợi ý theo máy hiện tại');suggestion.clicked.connect(host.guard(self.suggest_resources));form.addRow(suggestion)
        hint=QLabel('Số từng loại còn chịu giới hạn tổng. CPU quá cao, RAM/đĩa quá thấp sẽ ngừng nhận thêm việc; việc đang chạy được giữ.');hint.setWordWrap(True);form.addRow(hint)
        self.background=QCheckBox('Đóng cửa sổ thì tiếp tục chạy nền (nếu có system tray)');self.background.setChecked(host.store.setting('background',False));form.addRow(self.background)
        save=QPushButton('Lưu tài nguyên');save.clicked.connect(host.guard(self.save_resources));form.addRow(save)
        disable=QPushButton('Tắt tất cả watcher/lịch');disable.clicked.connect(host.guard(self.clear_auto));form.addRow(disable);tabs.addTab(resources,'Tự động / máy')
        self.refresh_profiles();self.scan();config=host.store.setting('translation',{});self.provider.setCurrentText(config.get('provider','google'));self.endpoint.setText(config.get('endpoint',''));self.budget.setValue(config.get('daily_limit',100000));self.glossary.setPlainText(json.dumps(config.get('glossary',{}),ensure_ascii=False,indent=2))

    def scan(self):self.host.background(lambda p,c:statuses(self.host.store),self.scanned)
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
        if name not in {'ffmpeg','ffprobe','Google Chrome','node'}:raise ValueError('Bộ tải dùng module gói kèm. Binary ngoài được chẩn đoán riêng; không tự đổi backend chưa kiểm chứng.')
        path,_=QFileDialog.getOpenFileName(self.host,'Chọn executable')
        if path:
            overrides=self.host.store.setting('tool_paths',{});overrides[name]=path;self.host.store.set_setting('tool_paths',overrides);configure_tools(overrides);self.scan()
    def install(self):self.install_name(self.selected_tool())
    def install_name(self,name):
        if name=='Google Chrome':self.host.background(lambda p,c:install_chrome(self.host.store,p,c),lambda _:self.scan())
        elif name=='ffprobe':self.install_name('ffmpeg')
        elif name in {'gallery-dl','yt-dlp'}:raise ValueError('Bộ tải được gói cùng ứng dụng; cập nhật qua bản app có dependency đã khóa. Không cài binary rồi báo đang dùng khi backend vẫn là module.')
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
        selected=self.profile.currentData()
        self.profile.clear()
        for item in profiles(self.host.store):self.profile.addItem(item['label'],item['id'])
        index=self.profile.findData(selected)
        if index>=0:self.profile.setCurrentIndex(index)
        accounts=bindings(self.host.store);self.accounts.setRowCount(len(accounts))
        for row,item in enumerate(accounts):
            for col,value in enumerate((item['platform'],item['label'],item['identity'] or 'chưa xác minh',item['status'])):self.accounts.setItem(row,col,QTableWidgetItem(value))
            self.accounts.item(row,0).setData(Qt.ItemDataRole.UserRole,item['id'])
    def create_profile(self):
        name,ok=QInputDialog.getText(self,'Hồ sơ Chrome','Tên')
        if ok:
            key=create_profile(self.host.store,name);self.refresh_profiles();self.profile.setCurrentIndex(self.profile.findData(key))
    def rename_profile(self):
        from ..browser import rename_profile
        key=self.current_profile();name,ok=QInputDialog.getText(self,'Đổi tên hồ sơ','Tên',text=self.profile.currentText())
        if ok:rename_profile(self.host.store,key,name);self.refresh_profiles();self.host.downloads.refresh_accounts()
    def forget_session(self):
        from ..browser import forget_session
        row=self.accounts.currentRow()
        if row<0:raise ValueError('Chọn một liên kết tài khoản trong bảng')
        forget_session(self.host.store,self.accounts.item(row,0).data(Qt.ItemDataRole.UserRole));self.refresh_profiles();self.host.downloads.refresh_accounts();self.host.message('Đã quên bản phiên trong app. Hồ sơ và đăng nhập trong Chrome được giữ.')
    def revoke_pairing(self):
        from ..browser import revoke_pairing
        revoke_pairing(self.host.store,self.current_profile());self.host.message('Đã thu hồi quyền gửi phiên của extension trong hồ sơ này; ghép lại bằng mã mới khi cần. Không xóa hồ sơ Chrome.')
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
        if path:register_host(Path(path),self.host.data);self.host.message('Đã đăng ký native host cho người dùng hiện tại')
    def extension(self):
        from ..paths import resource_directory
        from PySide6.QtCore import QUrl
        QDesktopServices.openUrl(QUrl.fromLocalFile(str(resource_directory('extension'))))
    def default(self):
        key=bind(self.host.store,self.current_profile(),self.platform.currentText());self.host.store.set_setting('default_binding:'+self.platform.currentText(),key);self.refresh_profiles();self.host.downloads.refresh_accounts()
    def save_provider(self):
        glossary=json.loads(self.glossary.toPlainText())
        if not isinstance(glossary,dict) or any(not isinstance(k,str) or not isinstance(v,str) for k,v in glossary.items()):raise ValueError('Thuật ngữ phải là object string → string')
        endpoint=self.endpoint.text()
        if self.provider.currentText()=='libre':
            from ..subtitles import translation_endpoint
            endpoint=translation_endpoint(endpoint)
        config={'provider':self.provider.currentText(),'endpoint':endpoint,'daily_limit':self.budget.value(),'glossary':glossary};self.host.store.set_setting('translation',config)
        if self.key.text():
            variable='FONESI_GOOGLE_TRANSLATE_API_KEY' if self.provider.currentText()=='google' else 'FONESI_LIBRETRANSLATE_API_KEY'
            os.environ[variable]=self.key.text();self.key.clear()
            if os.name=='nt':
                from ..browser import protect
                with self.host.store.connect() as c:c.execute('INSERT OR REPLACE INTO secrets VALUES(?,?)',('api:'+variable,protect(os.environ[variable].encode())))
        self.host.message('Đã lưu cấu hình; API key chỉ ở bộ nhớ phiên này trên Linux, dùng DPAPI khi lưu trên Windows')
    def save_resources(self):
        self.host.store.set_setting('resource_profile',self.resource_profile.currentText());self.host.store.set_setting('parallel',self.parallel.value());self.host.store.set_setting('background',self.background.isChecked());self.host.store.set_setting('job_limits',{key:field.value() for key,field in self.job_limits.items()});self.host.scheduler.parallel=self.parallel.value();self.host.message('Đã lưu giới hạn tài nguyên')
    def suggest_resources(self):
        data=metrics(self.host.data);recommended=recommended_parallel(data,self.resource_profile.currentText());self.parallel.setValue(max(1,recommended))
        for key,field in self.job_limits.items():field.setValue(1 if key in {'render','translate'} else max(1,min(3,recommended)))
        self.host.message(f'Gợi ý hiện tại: tổng {recommended} worker. Kiểm tra rồi bấm Lưu tài nguyên; đây là admission tức thời, chưa phải benchmark máy dài hạn.')
    def clear_auto(self):
        self.host.store.set_setting('watches',[])
        with self.host.store.connect() as c:c.execute('DELETE FROM schedules')
        self.host.message('Đã tắt watcher/lịch, giữ nguyên dữ liệu')
