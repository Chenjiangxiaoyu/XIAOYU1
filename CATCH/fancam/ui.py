from __future__ import annotations

from pathlib import Path
import sys
import cv2
import numpy as np
from PySide6.QtCore import QPoint, QRect, Qt, QThread, QUrl, Signal
from PySide6.QtGui import QColor, QImage, QPainter, QPen, QPixmap
from PySide6.QtMultimedia import QAudioOutput, QMediaPlayer
from PySide6.QtWidgets import (QApplication, QCheckBox, QComboBox, QFileDialog, QFrame, QHBoxLayout,
    QLabel, QListWidget, QListWidgetItem, QMainWindow, QMessageBox, QProgressBar, QPushButton,
    QSlider, QSpinBox, QStackedWidget, QVBoxLayout, QWidget)

from .analysis import AnalysisResult, CorrectionEvent, analyze_project, rebuild_crop_windows, replace_from_frame
from .models import CropSettings, Project, Segment, SegmentKind
from .processor import _render_full_frame, process_project
from .crop import SmoothCropper
from .verifier import VerificationResult, draw_verification
from .video import VideoReader

STYLE = """
QWidget { background:#F8F6F2; color:#3F4541; font-family:'Microsoft YaHei'; font-size:13px; }
#sidebar { background:#ECE7E1; border-radius:20px; } #brand { font-size:22px; font-weight:700; }
#muted { color:#8B918D; } #panel { background:#FFFDFC; border:1px solid #E9E5DF; border-radius:20px; }
QPushButton { background:#FFFDFC; border:1px solid #DED9D2; border-radius:11px; padding:10px 15px; }
QPushButton:hover { border-color:#C98E8C; } QPushButton#primary { background:#CB8D8B; color:white; border:0; font-weight:700; }
QPushButton:disabled { background:#DDD8D2; color:#999; } QComboBox,QSpinBox,QListWidget { background:white; border:1px solid #DED9D2; border-radius:9px; padding:7px; }
QSlider::groove:horizontal { height:6px; border-radius:3px; background:#E5E1DB; } QSlider::handle:horizontal { width:16px; margin:-5px 0; border-radius:8px; background:#CB8D8B; }
QProgressBar { border:0; background:#EAE5DF; border-radius:6px; height:12px; text-align:center; } QProgressBar::chunk { background:#98B7A8; border-radius:6px; }
"""


def to_pixmap(frame) -> QPixmap:
    rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB); h, w, ch = rgb.shape
    return QPixmap.fromImage(QImage(rgb.data, w, h, ch*w, QImage.Format.Format_RGB888).copy())


class RoiView(QLabel):
    roi_changed = Signal(tuple)
    def __init__(self):
        super().__init__("导入视频后，在画面中拖动框选目标人物")
        self.setAlignment(Qt.AlignmentFlag.AlignCenter); self.setMinimumSize(640,360)
        self.setStyleSheet("background:#242725;color:#AAA;border-radius:16px;")
        self._source=None; self._frame_size=(0,0); self._draw_rect=QRect(); self._start=QPoint(); self._dragging=False; self.roi=None
    def set_frame(self, frame): self._source=to_pixmap(frame); self._frame_size=(frame.shape[1],frame.shape[0]); self._draw_rect=QRect(); self.roi=None; self.update()
    def _image_rect(self):
        if not self._source: return self.rect()
        size=self._source.size(); size.scale(self.size(),Qt.AspectRatioMode.KeepAspectRatio)
        return QRect((self.width()-size.width())//2,(self.height()-size.height())//2,size.width(),size.height())
    def paintEvent(self,event):
        super().paintEvent(event)
        if not self._source:return
        p=QPainter(self); r=self._image_rect(); p.drawPixmap(r,self._source)
        if not self._draw_rect.isNull(): p.setPen(QPen(QColor("#FF918C"),3)); p.setBrush(QColor(255,145,140,30)); p.drawRoundedRect(self._draw_rect.normalized(),8,8)
    def mousePressEvent(self,event):
        if self._source and event.button()==Qt.MouseButton.LeftButton and self._image_rect().contains(event.position().toPoint()): self._start=event.position().toPoint(); self._dragging=True; self._draw_rect=QRect(self._start,self._start); self.update()
    def mouseMoveEvent(self,event):
        if self._dragging:
            p=event.position().toPoint(); r=self._image_rect(); p.setX(max(r.left(),min(p.x(),r.right()))); p.setY(max(r.top(),min(p.y(),r.bottom()))); self._draw_rect=QRect(self._start,p).normalized(); self.update()
    def mouseReleaseEvent(self,event):
        if not self._dragging:return
        self._dragging=False; rect=self._draw_rect.normalized(); image=self._image_rect()
        if rect.width()<15 or rect.height()<15: self._draw_rect=QRect(); self.roi=None; self.update(); return
        sx,sy=self._frame_size[0]/image.width(),self._frame_size[1]/image.height()
        self.roi=((rect.left()-image.left())*sx,(rect.top()-image.top())*sy,rect.width()*sx,rect.height()*sy); self.roi_changed.emit(self.roi)


class InterpolationMarkerBar(QWidget):
    markerClicked=Signal(int)
    def __init__(self): super().__init__(); self.setFixedHeight(30); self.first=0; self.last=1; self.markers=[]
    def set_markers(self,first,last,events): self.first=first; self.last=max(first+1,last); self.markers=list(events); self.update()
    def paintEvent(self,event):
        painter=QPainter(self); painter.setRenderHint(QPainter.RenderHint.Antialiasing); painter.setPen(QColor("#D68A48")); painter.drawLine(4,24,self.width()-4,24)
        for marker in self.markers:
            x=4+round((marker.frame_index-self.first)/(self.last-self.first)*max(1,self.width()-8)); label=f"补{marker.inserted_frames}"
            painter.setBrush(QColor("#F2B879")); painter.setPen(Qt.PenStyle.NoPen); painter.drawRoundedRect(QRect(max(0,x-15),2,30,18),6,6); painter.setPen(QColor("#66452D")); painter.drawText(QRect(max(0,x-15),2,30,18),Qt.AlignmentFlag.AlignCenter,label); painter.setPen(QColor("#D68A48")); painter.drawLine(x,20,x,27)
    def mousePressEvent(self,event):
        if not self.markers:return
        frame=self.first+(event.position().x()-4)/max(1,self.width()-8)*(self.last-self.first); nearest=min(self.markers,key=lambda item:abs(item.frame_index-frame))
        if abs(nearest.frame_index-frame)<=max(2,(self.last-self.first)*18/max(1,self.width())): self.markerClicked.emit(nearest.frame_index)


class AnalysisThread(QThread):
    progress=Signal(int); completed=Signal(object); failed=Signal(str)
    def __init__(self,project,end_frame=None,include_unanalyzed_tail=False,interpolation_overrides=None): super().__init__(); self.project=project; self.end_frame=end_frame; self.include_unanalyzed_tail=include_unanalyzed_tail; self.interpolation_overrides=interpolation_overrides; self.cancelled=False
    def run(self):
        try: self.completed.emit(analyze_project(self.project,lambda n,t:self.progress.emit(int(n*100/max(1,t))),lambda:self.cancelled,self.end_frame,self.include_unanalyzed_tail,self.interpolation_overrides))
        except Exception as exc: self.failed.emit(str(exc))


class ExportThread(QThread):
    progress=Signal(int); completed=Signal(str,int,int); failed=Signal(str)
    def __init__(self,project,analysis,output): super().__init__(); self.project=project; self.analysis=analysis; self.output=output; self.cancelled=False
    def run(self):
        try:
            r=process_project(self.project,self.output,lambda n,t:self.progress.emit(int(n*100/max(1,t))),cancelled=lambda:self.cancelled,analysis=self.analysis)
            self.completed.emit(str(r.output),r.lost_frames,r.corrected_frames)
        except Exception as exc:self.failed.emit(str(exc))


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__(); self.setWindowTitle("Fancam Maker · 舞台直拍生成器"); self.resize(1320,840)
        self.reader=None; self.path=""; self.frame_index=0; self.roi=None; self.project=None; self.analysis=None; self.worker=None
        self.manual_mode=False; self.reanalysis_start=None; self.reanalysis_reason=""; self.selected_interpolation_frame=None
        self.cut_start=None; self.full_start=None; self._media_updating=False
        self.audio_output=QAudioOutput(self); self.audio_output.setVolume(.8)
        self.media_player=QMediaPlayer(self); self.media_player.setAudioOutput(self.audio_output)
        self.media_player.positionChanged.connect(self._media_position_changed)
        self.media_player.playbackStateChanged.connect(self._media_state_changed)
        self._build()
    def _panel(self):
        p=QFrame(); p.setObjectName("panel"); b=QVBoxLayout(p); b.setContentsMargins(24,22,24,22); b.setSpacing(13); return p,b
    def _build(self):
        root=QWidget(); self.setCentralWidget(root); layout=QHBoxLayout(root); layout.setContentsMargins(18,18,18,18); layout.setSpacing(18)
        side=QFrame(); side.setObjectName("sidebar"); side.setFixedWidth(220); sb=QVBoxLayout(side); sb.setContentsMargins(20,24,20,20)
        brand=QLabel("◉ Fancam Maker"); brand.setObjectName("brand"); sb.addWidget(brand); sb.addWidget(QLabel("把舞台全景变成专属直拍")); sb.addSpacing(24)
        self.pages=QStackedWidget()
        for i,text in enumerate(["1  导入与框选","2  跟踪与构图","3  分析预览"]):
            btn=QPushButton(text); btn.clicked.connect(lambda _,x=i:self.pages.setCurrentIndex(x)); sb.addWidget(btn)
        sb.addStretch(); sb.addWidget(QLabel("本地处理 · 不上传视频")); layout.addWidget(side); layout.addWidget(self.pages,1)
        self.pages.addWidget(self._select_page()); self.pages.addWidget(self._settings_page()); self.pages.addWidget(self._preview_page())
    def _select_page(self):
        page=QWidget(); out=QVBoxLayout(page); title=QLabel("导入视频，框选你想跟随的人"); title.setObjectName("brand"); out.addWidget(title); out.addWidget(QLabel("选择人物清晰、无遮挡的一帧。建议用较窄的框覆盖头部和躯干，不必把四肢与周围空白全部框入。"))
        panel,box=self._panel(); out.addWidget(panel,1); self.roi_view=RoiView(); self.roi_view.roi_changed.connect(self._roi_ready); box.addWidget(self.roi_view,1)
        row=QHBoxLayout(); self.open_btn=QPushButton("导入视频"); self.open_btn.clicked.connect(self.open_video); row.addWidget(self.open_btn); self.time_label=QLabel("00:00 / 00:00"); row.addWidget(self.time_label)
        self.slider=QSlider(Qt.Orientation.Horizontal); self.slider.setEnabled(False); self.slider.valueChanged.connect(self.seek); row.addWidget(self.slider,1); self.next_btn=QPushButton("确认人物，下一步 →"); self.next_btn.setObjectName("primary"); self.next_btn.setEnabled(False); self.next_btn.clicked.connect(lambda:self.pages.setCurrentIndex(1)); row.addWidget(self.next_btn); box.addLayout(row); return page
    def _settings_page(self):
        page=QWidget(); out=QVBoxLayout(page); title=QLabel("设置直拍画面"); title.setObjectName("brand"); out.addWidget(title); panel,box=self._panel(); out.addWidget(panel)
        for label,items,attr in [("输出比例",["9:16 竖屏","3:4 竖屏","1:1 方形","16:9 横屏"],"ratio"),("跟随平滑",["标准","柔和","紧跟"],"smooth"),("人体验证频率",["每 5 帧（推荐）","每 3 帧（更稳）","每 8 帧（更快）"],"verify_stride")]:
            row=QHBoxLayout(); row.addWidget(QLabel(label)); w=QComboBox(); w.addItems(items); setattr(self,attr,w); row.addWidget(w); row.addStretch(); box.addLayout(row)
        first_row=QHBoxLayout(); first_row.addWidget(QLabel("首次跟踪时长")); self.initial_duration=QComboBox(); self.initial_duration.addItems(["3 秒","5 秒","10 秒（推荐）","30 秒","1 分钟","全部视频"]); self.initial_duration.setCurrentIndex(2); first_row.addWidget(self.initial_duration); first_row.addWidget(QLabel("可先分析短片段测试效果")); first_row.addStretch(); box.addLayout(first_row)
        row=QHBoxLayout(); row.addWidget(QLabel("人物留白")); self.scale=QSpinBox(); self.scale.setRange(150,350); self.scale.setValue(215); self.scale.setSuffix(" %"); row.addWidget(self.scale); row.addStretch(); box.addLayout(row)
        self.lock_zoom=QCheckBox("锁定景别，禁止跟踪框膨胀造成镜头拉远"); self.lock_zoom.setChecked(True); box.addWidget(self.lock_zoom)
        self.camera_stabilizer=QCheckBox("启用人体中心线稳定：小动作锁定镜头，真实走位柔和跟随，并预留125%臂展"); self.camera_stabilizer.setChecked(True); box.addWidget(self.camera_stabilizer)
        self.debug_overlay=QCheckBox("预览验证帧中的白色轮廓、绿色骨骼和跟踪框"); self.debug_overlay.setChecked(True); box.addWidget(self.debug_overlay)
        info=QLabel("可在“原视频全景（编辑）”和“导出成片”之间随时切换；两种视角共用同一时间轴、声音和最终裁切轨迹，切换不会重新分析。\n全景编辑视角会显示验证标记和最终导出范围；导出成片视角只显示与 MP4 一致的干净构图。")
        info.setStyleSheet("background:#EDF3EF;padding:16px;border-radius:12px;color:#62766B;"); box.addWidget(info); out.addStretch()
        row=QHBoxLayout(); back=QPushButton("← 返回框选"); back.clicked.connect(lambda:self.pages.setCurrentIndex(0)); row.addWidget(back); row.addStretch(); go=QPushButton("生成完整分析预览 →"); go.setObjectName("primary"); go.clicked.connect(self.start_analysis); row.addWidget(go); out.addLayout(row); return page
    def _preview_page(self):
        page=QWidget(); out=QVBoxLayout(page); title=QLabel("分析预览 · 确认后再导出"); title.setObjectName("brand"); out.addWidget(title)
        panel,box=self._panel(); out.addWidget(panel,1); body=QHBoxLayout(); self.preview=RoiView(); self.preview.setText("请先生成分析预览"); self.preview.setMinimumSize(650,430); self.preview.roi_changed.connect(self._manual_roi_ready); body.addWidget(self.preview,3)
        right=QVBoxLayout(); right.addWidget(QLabel("纠正与异常时间点（点击即可跳转）")); self.events=QListWidget(); self.events.itemClicked.connect(self._jump_event); right.addWidget(self.events,1); right.addWidget(QLabel("已删除片段")); self.cuts=QListWidget(); self.cuts.itemClicked.connect(self._jump_cut); right.addWidget(self.cuts,1); self.remove_cut_btn=QPushButton("撤销选中的删除片段"); self.remove_cut_btn.clicked.connect(self._remove_cut); right.addWidget(self.remove_cut_btn); right.addWidget(QLabel("全景画面片段")); self.full_segments=QListWidget(); self.full_segments.itemClicked.connect(self._jump_full_segment); right.addWidget(self.full_segments,1); self.remove_full_btn=QPushButton("撤销选中的全景片段"); self.remove_full_btn.clicked.connect(self._remove_full_segment); right.addWidget(self.remove_full_btn); body.addLayout(right,1); box.addLayout(body,1)
        playrow=QHBoxLayout(); self.play_btn=QPushButton("▶ 播放"); self.play_btn.clicked.connect(self._toggle_play); self.play_btn.setEnabled(False); playrow.addWidget(self.play_btn); self.reframe_btn=QPushButton("从当前帧重新框选"); self.reframe_btn.clicked.connect(self._begin_manual_reframe); self.reframe_btn.setEnabled(False); playrow.addWidget(self.reframe_btn); playrow.addWidget(QLabel("重算范围")); self.reframe_range=QComboBox(); self.reframe_range.addItems(["3 秒","5 秒（推荐）","10 秒","全部后续"]); self.reframe_range.setCurrentIndex(1); playrow.addWidget(self.reframe_range); self.cut_in_btn=QPushButton("设为删除起点"); self.cut_in_btn.clicked.connect(self._mark_cut_start); self.cut_in_btn.setEnabled(False); playrow.addWidget(self.cut_in_btn); self.cut_out_btn=QPushButton("删除到当前帧"); self.cut_out_btn.clicked.connect(self._mark_cut_end); self.cut_out_btn.setEnabled(False); playrow.addWidget(self.cut_out_btn); self.preview_time=QLabel("00:00"); playrow.addWidget(self.preview_time); box.addLayout(playrow)
        editrow=QHBoxLayout(); editrow.addWidget(QLabel("预览视角")); self.preview_mode=QComboBox(); self.preview_mode.addItems(["原视频全景（编辑）","导出成片"]); self.preview_mode.currentIndexChanged.connect(lambda:self._show_analysis_frame(self.preview_slider.value())); editrow.addWidget(self.preview_mode); self.full_in_btn=QPushButton("设为全景起点"); self.full_in_btn.clicked.connect(self._mark_full_start); self.full_in_btn.setEnabled(False); editrow.addWidget(self.full_in_btn); self.full_out_btn=QPushButton("全景到当前帧"); self.full_out_btn.clicked.connect(self._mark_full_end); self.full_out_btn.setEnabled(False); editrow.addWidget(self.full_out_btn); editrow.addStretch(); editrow.addWidget(QLabel("音量")); self.volume_slider=QSlider(Qt.Orientation.Horizontal); self.volume_slider.setRange(0,100); self.volume_slider.setValue(80); self.volume_slider.setFixedWidth(130); self.volume_slider.valueChanged.connect(lambda value:self.audio_output.setVolume(value/100)); editrow.addWidget(self.volume_slider); box.addLayout(editrow)
        self.interpolation_markers=InterpolationMarkerBar(); self.interpolation_markers.markerClicked.connect(self._select_interpolation); box.addWidget(self.interpolation_markers)
        timeline=QHBoxLayout(); timeline.addWidget(QLabel("时间轴")); self.preview_slider=QSlider(Qt.Orientation.Horizontal); self.preview_slider.valueChanged.connect(self._show_analysis_frame); self.preview_slider.setEnabled(False); timeline.addWidget(self.preview_slider,1); box.addLayout(timeline)
        interpolation_row=QHBoxLayout(); self.interpolation_selected=QLabel("未选择内部补帧标签"); interpolation_row.addWidget(self.interpolation_selected); interpolation_row.addWidget(QLabel("补帧数量")); self.interpolation_count=QComboBox(); self.interpolation_count.addItems(["1 帧","2 帧","3 帧","4 帧"]); interpolation_row.addWidget(self.interpolation_count); self.manual_interpolation_btn=QPushButton("当前帧手动补帧"); self.manual_interpolation_btn.clicked.connect(self._manual_interpolation); interpolation_row.addWidget(self.manual_interpolation_btn); self.regenerate_interpolation_btn=QPushButton("按此数量局部重算"); self.regenerate_interpolation_btn.clicked.connect(self._regenerate_interpolation); interpolation_row.addWidget(self.regenerate_interpolation_btn); self.delete_interpolation_btn=QPushButton("删除此次补帧"); self.delete_interpolation_btn.clicked.connect(self._delete_interpolation); interpolation_row.addWidget(self.delete_interpolation_btn); interpolation_row.addStretch(); box.addLayout(interpolation_row)
        self.progress=QProgressBar(); box.addWidget(self.progress); self.status=QLabel("分析完成前不能导出。完成后请拖动时间轴检查结果。"); box.addWidget(self.status)
        row=QHBoxLayout(); back=QPushButton("← 调整设置"); back.clicked.connect(lambda:self.pages.setCurrentIndex(1)); row.addWidget(back); row.addStretch(); self.export_btn=QPushButton("确认轨迹并导出 MP4"); self.export_btn.setObjectName("primary"); self.export_btn.setEnabled(False); self.export_btn.clicked.connect(self.start_export); row.addWidget(self.export_btn); box.addLayout(row); return page
    def open_video(self):
        path,_=QFileDialog.getOpenFileName(self,"选择舞台视频","","视频文件 (*.mp4 *.mov *.mkv *.avi)")
        if not path:return
        try:
            if self.reader:self.reader.close()
            self.media_player.stop(); self.media_player.setSource(QUrl.fromLocalFile(path))
            self.reader=VideoReader(path); self.path=path; self.frame_index=0; self.analysis=None; self.slider.setRange(0,max(0,self.reader.info.frames-1)); self.slider.setValue(0); self.slider.setEnabled(True); self._show_frame(0); self._update_time()
        except Exception as exc: QMessageBox.critical(self,"无法导入",str(exc))
    def seek(self,value): self.frame_index=value; self._show_frame(value); self._update_time(); self.next_btn.setEnabled(False); self.analysis=None
    def _show_frame(self,index):
        if self.reader:self.roi_view.set_frame(self.reader.frame(index))
    def _update_time(self):
        if self.reader:
            cur=self.frame_index/self.reader.info.fps; total=self.reader.info.duration; self.time_label.setText(f"{int(cur//60):02d}:{int(cur%60):02d} / {int(total//60):02d}:{int(total%60):02d}")
    def _roi_ready(self,roi): self.roi=roi; self.next_btn.setEnabled(True); self.analysis=None
    def _settings(self):
        ratios=[(9,16,1080,1920),(3,4,1080,1440),(1,1,1080,1080),(16,9,1920,1080)]; rw,rh,ow,oh=ratios[self.ratio.currentIndex()]
        settings=CropSettings(rw,rh,ow,oh,self.scale.value()/100,[.91,.95,.82][self.smooth.currentIndex()],0.0,self.lock_zoom.isChecked(),[5,3,8][self.verify_stride.currentIndex()],self.debug_overlay.isChecked())
        settings.stabilize_camera=self.camera_stabilizer.isChecked(); return settings
    def start_analysis(self):
        if not self.path or not self.roi: QMessageBox.warning(self,"尚未框选","请先导入视频并框选人物。"); return
        seconds=[3,5,10,30,60,None][self.initial_duration.currentIndex()]
        analysis_end=None if seconds is None else min(self.reader.info.frames-1,self.frame_index+round(seconds*self.reader.info.fps)-1)
        self.media_player.pause(); self.project=Project(self.path,self.frame_index,self.roi,self._settings(),[Segment(self.frame_index,self.reader.info.frames-1)]); self.analysis=None; self.reanalysis_start=None; self.reanalysis_reason=""; self.selected_interpolation_frame=None; self.cut_start=None; self.full_start=None; self.events.clear(); self.cuts.clear(); self.full_segments.clear(); self.interpolation_selected.setText("未选择内部补帧标签"); self.pages.setCurrentIndex(2); self.export_btn.setEnabled(False); self.reframe_btn.setEnabled(False); self.cut_in_btn.setEnabled(False); self.cut_out_btn.setEnabled(False); self.full_in_btn.setEnabled(False); self.full_out_btn.setEnabled(False); self.progress.setValue(0)
        scope="全部视频" if seconds is None else f"{seconds} 秒"
        self.status.setText(f"正在分析首次跟踪范围：{scope}。短范围适合先测试框选和跟踪效果……")
        self.worker=AnalysisThread(self.project,analysis_end,True); self.worker.progress.connect(self.progress.setValue); self.worker.completed.connect(self._analysis_done); self.worker.failed.connect(self._failed); self.worker.start()
    def _analysis_done(self,result:AnalysisResult):
        jump_to = result.source_start_frame
        if self.reanalysis_start is not None and self.analysis is not None:
            jump_to = self.reanalysis_start
            self.analysis = replace_from_frame(self.analysis, result, self.reanalysis_start)
            rebuild_crop_windows(self.analysis.frames,self.reader.info.width,self.reader.info.height,self.project.settings)
            if self.reanalysis_reason=="manual": self.analysis.events.append(CorrectionEvent(jump_to, jump_to / self.analysis.fps, "MANUAL-RESET", "用户从此帧重新框选并重算所选时间范围"))
            self.analysis.events.sort(key=lambda event: event.frame_index)
            action="内部补帧设置已更新" if self.reanalysis_reason=="interpolation" else "已重新跟踪所选范围"
            self.status.setText(f"{action}，范围外轨迹保持不变。")
            self.reanalysis_start = None
            self.reanalysis_reason = ""
        else:
            self.analysis=result
        result=self.analysis; self.progress.setValue(100); end=result.source_start_frame+len(result.frames)-1; self.preview_slider.setRange(result.source_start_frame,end); self.preview_slider.setValue(jump_to); self.preview_slider.setEnabled(True); self.play_btn.setEnabled(True); self.reframe_btn.setEnabled(True); self.cut_in_btn.setEnabled(True); self.cut_out_btn.setEnabled(True); self.full_in_btn.setEnabled(True); self.full_out_btn.setEnabled(True); self.export_btn.setEnabled(True)
        self._refresh_events()
        self._refresh_interpolation_markers()
        if jump_to == result.source_start_frame:
            pending=sum(1 for frame in result.frames if frame.state=="UNANALYZED")
            pending_text=f"；后面还有 {pending} 帧尚未跟踪，可逐段重新框选" if pending else ""
            self.status.setText(f"分析完成：主动纠正 {result.corrected_frames} 次，异常/纠正事件 {len(result.events)} 个{pending_text}。")
        self._show_analysis_frame(jump_to)
    def _refresh_events(self):
        self.events.clear(); result=self.analysis
        labels={"CORRECTED":"自动纠正","POSE-REJECTED":"拒绝骨骼跳变","HOLD":"保持上一位置","MANUAL-RESET":"手动重新框选"}
        for e in result.events:
            m=int(e.time_seconds//60); s=e.time_seconds%60; item=QListWidgetItem(f"{m:02d}:{s:05.2f}  {labels.get(e.state,e.state)}\n{e.reason}"); item.setData(Qt.ItemDataRole.UserRole,e.frame_index); self.events.addItem(item)
    def _refresh_interpolation_markers(self):
        first=self.analysis.source_start_frame; last=first+len(self.analysis.frames)-1; self.interpolation_markers.set_markers(first,last,self.analysis.interpolation_events)
    def _select_interpolation(self,frame_index):
        event=next((item for item in self.analysis.interpolation_events if item.frame_index==frame_index),None)
        if not event:return
        self.selected_interpolation_frame=frame_index; self.interpolation_count.setCurrentIndex(max(0,min(3,event.inserted_frames-1))); self.interpolation_selected.setText(f"已选 {event.time_seconds:.2f} 秒 · 内部补 {event.inserted_frames} 帧"); self._jump_to_frame(frame_index)
    def _regenerate_interpolation(self):
        if self.selected_interpolation_frame is None: QMessageBox.information(self,"尚未选择","请先点击时间轴上橙色的“补帧”标签。"); return
        self._reanalyze_interpolation(self.selected_interpolation_frame,self.interpolation_count.currentIndex()+1)
    def _manual_interpolation(self):
        if not self.analysis:return
        frame=self.preview_slider.value(); self.selected_interpolation_frame=frame
        self.interpolation_selected.setText(f"手动选择 {frame/self.analysis.fps:.2f} 秒 · 将重算附近两秒")
        self._reanalyze_interpolation(frame,self.interpolation_count.currentIndex()+1)
    def _delete_interpolation(self):
        if self.selected_interpolation_frame is None: QMessageBox.information(self,"尚未选择","请先点击时间轴上橙色的“补帧”标签。"); return
        self._reanalyze_interpolation(self.selected_interpolation_frame,0)
    def _reanalyze_interpolation(self,event_frame,count):
        self.media_player.pause(); radius=max(1,round(self.analysis.fps)); start=max(self.analysis.source_start_frame,event_frame-radius); seed=self.analysis.at_source_frame(start)
        if seed is None:return
        end=min(self.reader.info.frames-1,event_frame+radius); partial=Project(self.path,start,seed.final_box,self.project.settings,[Segment(start,end)])
        self.reanalysis_start=start; self.reanalysis_reason="interpolation"; self.export_btn.setEnabled(False); self.preview_slider.setEnabled(False); self.progress.setValue(0)
        action="删除补帧并重算" if count==0 else f"改为内部补 {count} 帧并重算"
        self.status.setText(f"正在从 {event_frame/self.analysis.fps:.2f} 秒附近{action}……")
        self.worker=AnalysisThread(partial,end,False,{event_frame:count}); self.worker.progress.connect(self.progress.setValue); self.worker.completed.connect(self._analysis_done); self.worker.failed.connect(self._failed); self.worker.start()
    def _show_analysis_frame(self,source_index):
        if not self.analysis or not self.reader:return
        item=self.analysis.at_source_frame(source_index)
        if not item:return
        frame=self.reader.frame(source_index); verification=item.verification or VerificationResult()
        skipped=any(segment.kind==SegmentKind.SKIP and segment.includes(source_index) for segment in self.project.segments)
        full_frame=any(segment.kind==SegmentKind.FULL_FRAME and segment.includes(source_index) for segment in self.project.segments)
        interpolation=next((event for event in self.analysis.interpolation_events if event.frame_index==source_index),None)
        export_preview=self.preview_mode.currentIndex()==1
        if export_preview:
            output_size=(self.project.settings.output_width,self.project.settings.output_height)
            if skipped:
                shown=np.full((output_size[1],output_size[0],3),24,dtype=np.uint8); cv2.putText(shown,"DELETED SEGMENT",(40,80),cv2.FONT_HERSHEY_SIMPLEX,1.0,(100,100,240),2,cv2.LINE_AA)
            else:
                shown=_render_full_frame(frame,output_size) if full_frame else SmoothCropper.render(frame,item.crop_window,output_size)
        else:
            shown=draw_verification(frame,verification,item.csrt_box,item.final_box,item.state) if self.project.settings.show_debug_overlay else frame.copy()
            crop=item.crop_window
            if crop:
                cv2.rectangle(shown,(crop.x,crop.y),(crop.x+crop.width,crop.y+crop.height),(235,205,95),2,cv2.LINE_AA); cv2.putText(shown,"EXPORT VIEW",(max(8,crop.x+6),max(24,crop.y+24)),cv2.FONT_HERSHEY_SIMPLEX,.58,(235,205,95),2,cv2.LINE_AA)
            if skipped: cv2.putText(shown,"DELETED SEGMENT",(18,62),cv2.FONT_HERSHEY_SIMPLEX,.72,(80,80,255),2,cv2.LINE_AA)
            elif full_frame: cv2.putText(shown,"FULL FRAME OUTPUT",(18,62),cv2.FONT_HERSHEY_SIMPLEX,.72,(120,220,255),2,cv2.LINE_AA)
            if interpolation: cv2.putText(shown,f"INTERNAL +{interpolation.inserted_frames} FRAMES",(18,92),cv2.FONT_HERSHEY_SIMPLEX,.66,(90,185,245),2,cv2.LINE_AA)
        if not self._media_updating: self.media_player.setPosition(round(source_index/self.analysis.fps*1000))
        self.preview.set_frame(shown); sec=source_index/self.analysis.fps; mode="导出成片" if export_preview else "原视频全景"; suffix=" · 将删除" if skipped else (" · 全景输出" if full_frame else ""); self.preview_time.setText(f"{int(sec//60):02d}:{sec%60:05.2f} · {mode} · {item.state}{suffix}")
    def _jump_to_frame(self,frame): self.preview_slider.setValue(frame)
    def _jump_event(self,item): self._jump_to_frame(item.data(Qt.ItemDataRole.UserRole))
    def _jump_cut(self,item): self._jump_to_frame(item.data(Qt.ItemDataRole.UserRole))
    def _toggle_play(self):
        if self.media_player.playbackState()==QMediaPlayer.PlaybackState.PlayingState: self.media_player.pause()
        else: self.media_player.setPosition(round(self.preview_slider.value()/self.analysis.fps*1000)); self.media_player.play()
    def _media_state_changed(self,state): self.play_btn.setText("Ⅱ 暂停" if state==QMediaPlayer.PlaybackState.PlayingState else "▶ 播放")
    def _media_position_changed(self,milliseconds):
        if not self.analysis:return
        frame=round(milliseconds*self.analysis.fps/1000); end=self.analysis.source_start_frame+len(self.analysis.frames)-1
        if frame>end: self.media_player.pause(); return
        if frame<self.analysis.source_start_frame:return
        self._media_updating=True; self.preview_slider.setValue(frame); self._media_updating=False
    def _mark_cut_start(self):
        if not self.analysis:return
        self.media_player.pause(); self.cut_start=self.preview_slider.value(); self.status.setText("删除起点已标记。请移动到人物重新回到画面前的最后一帧，再点击“删除到当前帧”。")
    def _mark_cut_end(self):
        if self.cut_start is None: QMessageBox.information(self,"尚未设置起点","请先移动到人物出画的位置并点击“设为删除起点”。"); return
        end=self.preview_slider.value(); start=self.cut_start
        if end<start: start,end=end,start
        self.project.segments.append(Segment(start,end,SegmentKind.SKIP,"人物出画")); self.cut_start=None; self._normalize_cuts(); self._refresh_cuts(); self._show_analysis_frame(self.preview_slider.value()); self.status.setText("片段已标记为删除。导出时视频和对应音频都会跳过这一区间。")
    def _normalize_cuts(self):
        keeps=[s for s in self.project.segments if s.kind!=SegmentKind.SKIP]; cuts=sorted((s for s in self.project.segments if s.kind==SegmentKind.SKIP),key=lambda s:s.start_frame); merged=[]
        for cut in cuts:
            if merged and cut.start_frame<=merged[-1].end_frame+1: merged[-1].end_frame=max(merged[-1].end_frame,cut.end_frame)
            else: merged.append(Segment(cut.start_frame,cut.end_frame,SegmentKind.SKIP,cut.label))
        self.project.segments=keeps+merged
    def _refresh_cuts(self):
        self.cuts.clear()
        for segment in self.project.segments:
            if segment.kind!=SegmentKind.SKIP:continue
            a=segment.start_frame/self.analysis.fps; b=segment.end_frame/self.analysis.fps; item=QListWidgetItem(f"{int(a//60):02d}:{a%60:05.2f} — {int(b//60):02d}:{b%60:05.2f}"); item.setData(Qt.ItemDataRole.UserRole,segment.start_frame); item.setData(Qt.ItemDataRole.UserRole+1,(segment.start_frame,segment.end_frame)); self.cuts.addItem(item)
    def _remove_cut(self):
        item=self.cuts.currentItem()
        if not item:return
        target=item.data(Qt.ItemDataRole.UserRole+1); self.project.segments=[s for s in self.project.segments if not (s.kind==SegmentKind.SKIP and (s.start_frame,s.end_frame)==tuple(target))]; self._refresh_cuts(); self._show_analysis_frame(self.preview_slider.value()); self.status.setText("已撤销该删除片段。")
    def _mark_full_start(self):
        if not self.analysis:return
        self.media_player.pause(); self.full_start=self.preview_slider.value(); self.status.setText("全景起点已标记。请移动到准备恢复人物直拍的位置，再点击“全景到当前帧”。")
    def _mark_full_end(self):
        if self.full_start is None: QMessageBox.information(self,"尚未设置起点","请先移动到需要恢复原始完整画面的位置并点击“设为全景起点”。"); return
        end=self.preview_slider.value(); start=self.full_start
        if end<start:start,end=end,start
        self.project.segments.append(Segment(start,end,SegmentKind.FULL_FRAME,"原始全景")); self.full_start=None; self._normalize_full_segments(); self._refresh_full_segments(); self._show_analysis_frame(self.preview_slider.value()); self.status.setText("该片段将输出原视频完整画面并保留声音。人物回来后，可从回场帧重新框选。")
    def _normalize_full_segments(self):
        others=[s for s in self.project.segments if s.kind!=SegmentKind.FULL_FRAME]; segments=sorted((s for s in self.project.segments if s.kind==SegmentKind.FULL_FRAME),key=lambda s:s.start_frame); merged=[]
        for segment in segments:
            if merged and segment.start_frame<=merged[-1].end_frame+1: merged[-1].end_frame=max(merged[-1].end_frame,segment.end_frame)
            else: merged.append(Segment(segment.start_frame,segment.end_frame,SegmentKind.FULL_FRAME,segment.label))
        self.project.segments=others+merged
    def _refresh_full_segments(self):
        self.full_segments.clear()
        for segment in self.project.segments:
            if segment.kind!=SegmentKind.FULL_FRAME:continue
            a=segment.start_frame/self.analysis.fps; b=segment.end_frame/self.analysis.fps; item=QListWidgetItem(f"{int(a//60):02d}:{a%60:05.2f} — {int(b//60):02d}:{b%60:05.2f}"); item.setData(Qt.ItemDataRole.UserRole,segment.start_frame); item.setData(Qt.ItemDataRole.UserRole+1,(segment.start_frame,segment.end_frame)); self.full_segments.addItem(item)
    def _jump_full_segment(self,item): self._jump_to_frame(item.data(Qt.ItemDataRole.UserRole))
    def _remove_full_segment(self):
        item=self.full_segments.currentItem()
        if not item:return
        target=item.data(Qt.ItemDataRole.UserRole+1); self.project.segments=[s for s in self.project.segments if not (s.kind==SegmentKind.FULL_FRAME and (s.start_frame,s.end_frame)==tuple(target))]; self._refresh_full_segments(); self._show_analysis_frame(self.preview_slider.value()); self.status.setText("已撤销该全景片段。")
    def _begin_manual_reframe(self):
        if not self.analysis:return
        self.media_player.pause(); self.manual_mode=True
        self.status.setText(f"已暂停。请在当前画面拖出较窄目标框；松开后将按“{self.reframe_range.currentText()}”重新分析。")
    def _manual_roi_ready(self,roi):
        if not self.manual_mode or not self.analysis:return
        self.manual_mode=False; start=self.preview_slider.value(); self.reanalysis_start=start; self.reanalysis_reason="manual"
        item=self.analysis.at_source_frame(start); ox,oy,ow,oh=roi; output_w=self.project.settings.output_width; output_h=self.project.settings.output_height
        full_frame=any(segment.kind==SegmentKind.FULL_FRAME and segment.includes(start) for segment in self.project.segments)
        if self.preview_mode.currentIndex()==0:
            source_roi=roi
        elif full_frame:
            scale=min(output_w/self.reader.info.width,output_h/self.reader.info.height); pad_x=(output_w-self.reader.info.width*scale)/2; pad_y=(output_h-self.reader.info.height*scale)/2
            source_roi=((ox-pad_x)/scale,(oy-pad_y)/scale,ow/scale,oh/scale)
        else:
            crop=item.crop_window; source_roi=(crop.x+ox*crop.width/output_w,crop.y+oy*crop.height/output_h,ow*crop.width/output_w,oh*crop.height/output_h)
        sx,sy,sw,sh=source_roi; sx=max(0,min(sx,self.reader.info.width-1)); sy=max(0,min(sy,self.reader.info.height-1)); sw=max(4,min(sw,self.reader.info.width-sx)); sh=max(4,min(sh,self.reader.info.height-sy)); source_roi=(sx,sy,sw,sh)
        partial=Project(self.path,start,source_roi,self.project.settings,[Segment(start,self.reader.info.frames-1)])
        seconds=[3,5,10,None][self.reframe_range.currentIndex()]
        end_frame=None if seconds is None else min(self.reader.info.frames-1,start+round(seconds*self.reader.info.fps)-1)
        self.export_btn.setEnabled(False); self.reframe_btn.setEnabled(False); self.cut_in_btn.setEnabled(False); self.cut_out_btn.setEnabled(False); self.full_in_btn.setEnabled(False); self.full_out_btn.setEnabled(False); self.preview_slider.setEnabled(False); self.play_btn.setEnabled(False); self.progress.setValue(0)
        scope="全部后续" if end_frame is None else f"约 {seconds} 秒（到第 {end_frame} 帧）"
        self.status.setText(f"正在从第 {start} 帧按新框重新分析 {scope}，范围外的旧轨迹保持不变……")
        self.worker=AnalysisThread(partial,end_frame); self.worker.progress.connect(self.progress.setValue); self.worker.completed.connect(self._analysis_done); self.worker.failed.connect(self._failed); self.worker.start()
    def start_export(self):
        if not self.analysis:return
        self.media_player.pause()
        default=str(Path(self.path).with_name(Path(self.path).stem+"_fancam.mp4")); output,_=QFileDialog.getSaveFileName(self,"导出直拍",default,"MP4 视频 (*.mp4)")
        if not output:return
        self.project.save(Path(output).with_suffix(".fancam.json")); self.export_btn.setEnabled(False); self.status.setText("正在使用已确认的轨迹编码 MP4，不会重新分析……")
        self.worker=ExportThread(self.project,self.analysis,output); self.worker.progress.connect(self.progress.setValue); self.worker.completed.connect(self._done); self.worker.failed.connect(self._failed); self.worker.start()
    def _done(self,path,lost,corrected): self.export_btn.setEnabled(True); self.progress.setValue(100); self.status.setText(f"导出完成：{path}"); QMessageBox.information(self,"导出完成",f"视频已生成。分析阶段主动纠正 {corrected} 次。")
    def _failed(self,message):
        self.reanalysis_start=None; self.manual_mode=False; ready=bool(self.analysis); self.export_btn.setEnabled(ready); self.reframe_btn.setEnabled(ready); self.cut_in_btn.setEnabled(ready); self.cut_out_btn.setEnabled(ready); self.full_in_btn.setEnabled(ready); self.full_out_btn.setEnabled(ready); self.preview_slider.setEnabled(ready); self.play_btn.setEnabled(ready); self.status.setText(message); QMessageBox.critical(self,"处理未完成",message)
    def closeEvent(self,event):
        self.media_player.stop()
        if self.worker and self.worker.isRunning(): self.worker.cancelled=True; self.worker.wait(3000)
        if self.reader:self.reader.close()
        super().closeEvent(event)


def run():
    app=QApplication(sys.argv); app.setStyleSheet(STYLE); window=MainWindow(); window.show(); sys.exit(app.exec())
