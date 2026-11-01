from __future__ import annotations

from dataclasses import dataclass
from typing import Callable
import cv2

from .arbiter import TrackingArbiter
from .models import Project
from .tracker import Box, CsrtTracker
from .verifier import HumanVerifier, VerificationResult
from .interpolation import center_jump, interpolate_frames, local_motion_score
from .camera import BodyAwareCameraStabilizer, CameraTarget
from .crop import CropWindow, SmoothCropper


def roundtrip_excursion_start(frames: list[FrameAnalysis], current_box: Box,
                              reference_height: float, fps: float) -> int | None:
    """Find a brief unverified A -> B -> A tracker excursion."""
    if len(frames)<3:return None
    cx=current_box[0]+current_box[2]/2; cy=current_box[1]+current_box[3]/2
    window=max(3,min(len(frames),round(fps*.9)))
    first=len(frames)-window
    for anchor_index in range(first,len(frames)-2):
        anchor=frames[anchor_index]
        ax=anchor.final_box[0]+anchor.final_box[2]/2; ay=anchor.final_box[1]+anchor.final_box[3]/2
        if ((cx-ax)**2+(cy-ay)**2)**.5/max(1.0,reference_height)>.22:continue
        middle=frames[anchor_index+1:]
        if any(item.state in {"VERIFIED","CORRECTED","MANUAL-RESET","ROUNDTRIP-RESET"} for item in middle):continue
        farthest=max((((item.final_box[0]+item.final_box[2]/2-ax)**2+
                       (item.final_box[1]+item.final_box[3]/2-ay)**2)**.5/max(1.0,reference_height)) for item in middle)
        if farthest>.65:return anchor_index
    return None


@dataclass
class FrameAnalysis:
    frame_index: int
    csrt_box: Box
    final_box: Box
    state: str
    reason: str
    verification: VerificationResult | None = None
    tracker_lost: bool = False
    camera_target: CameraTarget | None = None
    crop_window: CropWindow | None = None


@dataclass
class CorrectionEvent:
    frame_index: int
    time_seconds: float
    state: str
    reason: str


@dataclass
class InterpolationEvent:
    frame_index: int
    time_seconds: float
    inserted_frames: int
    motion_score: float
    reason: str = "检测到快速位移，内部补帧辅助跟踪"


@dataclass
class AnalysisResult:
    frames: list[FrameAnalysis]
    events: list[CorrectionEvent]
    fps: float
    source_start_frame: int
    source_total_frames: int
    lost_frames: int
    corrected_frames: int
    interpolation_events: list[InterpolationEvent] | None = None

    def __post_init__(self):
        if self.interpolation_events is None:self.interpolation_events=[]

    def at_source_frame(self, frame_index: int) -> FrameAnalysis | None:
        offset = frame_index - self.source_start_frame
        return self.frames[offset] if 0 <= offset < len(self.frames) else None


def _normalize_camera_safety(frames: list[FrameAnalysis]) -> None:
    """Camera stabilizer already applies temporal hysteresis and easing."""
    return


def rebuild_crop_windows(frames: list[FrameAnalysis], frame_width: int, frame_height: int, settings) -> None:
    """Build the single authoritative camera path used by preview and export."""
    cropper=SmoothCropper(frame_width,frame_height,settings)
    for item in frames:
        target=item.camera_target
        item.crop_window=cropper.update(target.box if target else item.final_box,
                                        target.min_view_width if target else 0.0,
                                        bool(target and settings.stabilize_camera),
                                        target.min_view_height if target else 0.0)


def replace_from_frame(original: AnalysisResult, replacement: AnalysisResult,
                       frame_index: int) -> AnalysisResult:
    """Replace only the analyzed interval, preserving approved frames on both sides."""
    prefix = [item for item in original.frames if item.frame_index < frame_index]
    replacement_end = replacement.frames[-1].frame_index if replacement.frames else frame_index - 1
    suffix = [item for item in replacement.frames if item.frame_index >= frame_index]
    tail = [item for item in original.frames if item.frame_index > replacement_end]
    frames = prefix + suffix + tail
    _normalize_camera_safety(frames)
    events = ([event for event in original.events if event.frame_index < frame_index or event.frame_index > replacement_end] +
              [event for event in replacement.events if frame_index <= event.frame_index <= replacement_end])
    interpolation_events = ([event for event in original.interpolation_events if event.frame_index < frame_index or event.frame_index > replacement_end] +
                            [event for event in replacement.interpolation_events if frame_index <= event.frame_index <= replacement_end])
    return AnalysisResult(
        frames=frames,
        events=events,
        fps=original.fps,
        source_start_frame=original.source_start_frame,
        source_total_frames=original.source_total_frames,
        lost_frames=sum(1 for item in frames if item.tracker_lost),
        corrected_frames=sum(1 for item in frames if item.state == "CORRECTED"),
        interpolation_events=sorted(interpolation_events,key=lambda event:event.frame_index),
    )


def _safe_box(box: Box, width: int, height: int) -> Box:
    x, y, w, h = box
    return max(0.0, min(x, width - w)), max(0.0, min(y, height - h)), w, h


def analyze_project(project: Project, on_progress: Callable[[int, int], None] | None = None,
                    cancelled: Callable[[], bool] | None = None,
                    end_frame: int | None = None,
                    include_unanalyzed_tail: bool = False,
                    interpolation_overrides: dict[int, int] | None = None) -> AnalysisResult:
    cap = cv2.VideoCapture(project.source)
    if not cap.isOpened():
        raise RuntimeError("无法打开视频文件。")
    fps = cap.get(cv2.CAP_PROP_FPS) or 30.0
    total = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    fw = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)); fh = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    cap.set(cv2.CAP_PROP_POS_FRAMES, project.selected_frame)
    ok, frame = cap.read()
    if not ok:
        cap.release(); raise RuntimeError("无法读取所选关键帧。")
    tracker = CsrtTracker(); tracker.initialize(frame, project.initial_box)
    arbiter = TrackingArbiter(project.initial_box); verifier = HumanVerifier()
    camera = BodyAwareCameraStabilizer(project.initial_box,project.settings.position_dead_zone,project.settings.scale_dead_zone,project.settings.arm_margin)
    last_box = project.initial_box; frames = []; events = []; interpolation_events=[]; previous_frame=None
    interpolation_overrides=interpolation_overrides or {}
    final_frame = min(total - 1, end_frame) if end_frame is not None else total - 1
    lost = corrected = 0; index = project.selected_frame; last_event_state = ""; last_interpolation_index=-9999
    try:
        while ok:
            if cancelled and cancelled(): raise InterruptedError("用户取消了分析。")
            tracked, proposal = (True, last_box) if index == project.selected_frame else tracker.update(frame)
            motion=local_motion_score(previous_frame,frame,last_box) if previous_frame is not None else 0.0
            jump=center_jump(last_box,proposal) if tracked else 99.0
            forced_count=interpolation_overrides.get(index)
            fast_motion=(not tracked or jump>0.48 or motion>0.13) and index-last_interpolation_index>3
            if previous_frame is not None and (forced_count is not None or fast_motion) and forced_count!=0:
                attempts=[forced_count] if forced_count is not None else [1,2]
                original_tracker=tracker
                for inserted in attempts:
                    rescue=CsrtTracker(); rescue.initialize(previous_frame,last_box); rescue_ok=True; rescue_box=last_box
                    for middle in interpolate_frames(previous_frame,frame,inserted):
                        rescue_ok,rescue_box=rescue.update(middle)
                        if not rescue_ok:break
                    if rescue_ok:rescue_ok,rescue_box=rescue.update(frame)
                    if rescue_ok and center_jump(last_box,rescue_box)<1.15:
                        tracker=rescue; tracked=True; proposal=rescue_box
                        interpolation_events.append(InterpolationEvent(index,index/fps,inserted,motion))
                        last_interpolation_index=index
                        break
                else: tracker=original_tracker
            if not tracked: lost += 1
            candidate = proposal if tracked else last_box
            sampled = (index - project.selected_frame) % max(1, project.settings.verification_stride) == 0
            verification = verifier.verify(frame, candidate) if sampled else None
            decision = arbiter.decide(tracked, candidate, verification)
            last_box = _safe_box(decision.box, fw, fh)
            roundtrip_start=roundtrip_excursion_start(frames,last_box,project.initial_box[3],fps)
            if roundtrip_start is not None:
                anchor=frames[roundtrip_start]; last_box=anchor.final_box
                for mistaken in frames[roundtrip_start+1:]:
                    mistaken.final_box=last_box; mistaken.state="ROUNDTRIP-RESET"
                    mistaken.reason="检测到跟踪框短暂跑走后返回，已撤销中间错误轨迹"
                    mistaken.camera_target=anchor.camera_target
                arbiter.trusted=last_box
                tracker=CsrtTracker(); tracker.initialize(frame,last_box)
            if decision.state == "CORRECTED": corrected += 1
            if decision.reinitialize:
                tracker = CsrtTracker(); tracker.initialize(frame, last_box)
            camera_verification=verification if decision.state in {"VERIFIED","CORRECTED"} else None
            camera_target=camera.update(last_box,camera_verification) if project.settings.stabilize_camera else CameraTarget(last_box)
            state="ROUNDTRIP-RESET" if roundtrip_start is not None else decision.state
            reason="检测到跟踪框短暂跑走后返回，已回退并从最后可信位置重新追踪" if roundtrip_start is not None else decision.reason
            frames.append(FrameAnalysis(index, candidate, last_box, state, reason, verification, not tracked,camera_target))
            noteworthy = state in {"CORRECTED","ROUNDTRIP-RESET"} or (state in {"POSE-REJECTED", "HOLD"} and state != last_event_state)
            if noteworthy: events.append(CorrectionEvent(index, index / fps, state, reason))
            last_event_state = state
            previous_frame=frame.copy()
            if on_progress and index % 3 == 0: on_progress(index - project.selected_frame, max(1, final_frame - project.selected_frame + 1))
            if index >= final_frame: break
            ok, frame = cap.read(); index += 1
    finally:
        cap.release(); verifier.close()
    if include_unanalyzed_tail and frames:
        # Keep the whole source on the timeline without pretending that the
        # unprocessed tail has been tracked. Manual bounded reframes can fill
        # these placeholders progressively.
        for pending_index in range(frames[-1].frame_index + 1, total):
            frames.append(FrameAnalysis(
                pending_index, last_box, last_box, "UNANALYZED",
                "尚未跟踪；请在此处使用“从当前帧重新框选”补充分析",
                camera_target=camera.update(last_box,None),
            ))
    _normalize_camera_safety(frames)
    rebuild_crop_windows(frames,fw,fh,project.settings)
    return AnalysisResult(frames, events, fps, project.selected_frame, total, lost, corrected, interpolation_events)
