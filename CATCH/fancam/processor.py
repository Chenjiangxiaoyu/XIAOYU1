from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import subprocess
import tempfile
from typing import Callable
import cv2
import imageio_ffmpeg

from .analysis import AnalysisResult, analyze_project, rebuild_crop_windows
from .crop import SmoothCropper
from .models import Project, SegmentKind


@dataclass
class ProcessResult:
    output: Path
    processed_frames: int
    lost_frames: int
    corrected_frames: int = 0


def _is_skipped(project: Project, frame_index: int) -> bool:
    return any(s.kind == SegmentKind.SKIP and s.includes(frame_index) for s in project.segments)


def _is_full_frame(project: Project, frame_index: int) -> bool:
    return any(s.kind == SegmentKind.FULL_FRAME and s.includes(frame_index) for s in project.segments)


def _render_full_frame(frame, output_size: tuple[int, int]):
    """Fit the entire source image inside the output without cropping it."""
    output_w, output_h = output_size
    source_h, source_w = frame.shape[:2]
    scale = min(output_w / source_w, output_h / source_h)
    width, height = max(1, round(source_w * scale)), max(1, round(source_h * scale))
    resized = cv2.resize(frame, (width, height), interpolation=cv2.INTER_AREA if scale < 1 else cv2.INTER_CUBIC)
    canvas = frame[:1, :1].copy()
    canvas = cv2.resize(canvas, (output_w, output_h))
    canvas[:] = (18, 18, 18)
    x, y = (output_w - width) // 2, (output_h - height) // 2
    canvas[y:y + height, x:x + width] = resized
    return canvas


def _keep_ranges(project: Project, start_frame: int, end_frame: int, fps: float) -> list[tuple[float, float]]:
    cuts = sorted((max(start_frame, s.start_frame), min(end_frame, s.end_frame))
                  for s in project.segments if s.kind == SegmentKind.SKIP
                  and s.end_frame >= start_frame and s.start_frame <= end_frame)
    merged: list[list[int]] = []
    for start, end in cuts:
        if merged and start <= merged[-1][1] + 1: merged[-1][1] = max(merged[-1][1], end)
        else: merged.append([start, end])
    ranges = []; cursor = start_frame
    for start, end in merged:
        if cursor < start: ranges.append((cursor / fps, start / fps))
        cursor = end + 1
    if cursor <= end_frame: ranges.append((cursor / fps, (end_frame + 1) / fps))
    return ranges


def _mux_audio(video: Path, source: Path, output: Path, keep_ranges: list[tuple[float, float]]) -> None:
    ffmpeg = imageio_ffmpeg.get_ffmpeg_exe()
    filters = []
    for i, (start, end) in enumerate(keep_ranges):
        filters.append(f"[1:a]atrim=start={start:.6f}:end={end:.6f},asetpts=PTS-STARTPTS[a{i}]")
    labels = "".join(f"[a{i}]" for i in range(len(keep_ranges)))
    filters.append(f"{labels}concat=n={len(keep_ranges)}:v=0:a=1[aout]")
    command = [ffmpeg, "-y", "-i", str(video), "-i", str(source), "-filter_complex", ";".join(filters),
               "-map", "0:v:0", "-map", "[aout]", "-c:v", "copy", "-c:a", "aac", "-b:a", "192k",
               "-shortest", "-movflags", "+faststart", str(output)]
    done = subprocess.run(command, capture_output=True, text=True, creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
    if done.returncode != 0:
        # Some source videos have no audio stream. Preserve a usable video-only
        # export instead of failing the whole render in that case.
        fallback = [ffmpeg, "-y", "-i", str(video), "-map", "0:v:0", "-c:v", "copy", "-movflags", "+faststart", str(output)]
        fallback_done = subprocess.run(fallback, capture_output=True, text=True, creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
        if fallback_done.returncode != 0: raise RuntimeError("合并视频失败：" + fallback_done.stderr[-500:])


def process_project(project: Project, output_path: str | Path,
                    on_progress: Callable[[int, int], None] | None = None,
                    on_preview: Callable[[object], None] | None = None,
                    cancelled: Callable[[], bool] | None = None,
                    analysis: AnalysisResult | None = None) -> ProcessResult:
    analysis = analysis or analyze_project(project, on_progress, cancelled)
    source = Path(project.source); output = Path(output_path)
    cap = cv2.VideoCapture(str(source))
    if not cap.isOpened(): raise RuntimeError("无法打开视频文件。")
    fps = cap.get(cv2.CAP_PROP_FPS) or analysis.fps
    fw = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)); fh = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    cap.set(cv2.CAP_PROP_POS_FRAMES, project.selected_frame)
    cropper = SmoothCropper(fw, fh, project.settings)
    rebuild_crop_windows(analysis.frames,fw,fh,project.settings)
    processed = 0
    with tempfile.TemporaryDirectory(prefix="fancam-") as temp_dir:
        silent = Path(temp_dir) / "tracked.mp4"
        writer = cv2.VideoWriter(str(silent), cv2.VideoWriter_fourcc(*"mp4v"), fps,
                                 (project.settings.output_width, project.settings.output_height))
        if not writer.isOpened(): cap.release(); raise RuntimeError("无法创建临时视频文件。")
        try:
            for item in analysis.frames:
                if cancelled and cancelled(): raise InterruptedError("用户取消了导出。")
                ok, frame = cap.read()
                if not ok: break
                crop=item.crop_window
                if not _is_skipped(project, item.frame_index):
                    output_size = (project.settings.output_width, project.settings.output_height)
                    rendered = (_render_full_frame(frame, output_size) if _is_full_frame(project, item.frame_index)
                                else cropper.render(frame, crop, output_size))
                    writer.write(rendered); processed += 1
                    if on_preview and processed % max(1, int(fps / 3)) == 0: on_preview(rendered)
                if on_progress and processed % 3 == 0: on_progress(processed, max(1, len(analysis.frames)))
        finally:
            writer.release(); cap.release()
        if processed == 0: raise RuntimeError("所选范围没有可导出的画面。")
        output.parent.mkdir(parents=True, exist_ok=True)
        keep_ranges = _keep_ranges(project, analysis.frames[0].frame_index, analysis.frames[-1].frame_index, fps)
        _mux_audio(silent, source, output, keep_ranges)
    return ProcessResult(output, processed, analysis.lost_frames, analysis.corrected_frames)
