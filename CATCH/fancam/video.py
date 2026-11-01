from __future__ import annotations

from dataclasses import dataclass
import cv2
import numpy as np


@dataclass
class VideoInfo:
    width: int
    height: int
    fps: float
    frames: int

    @property
    def duration(self) -> float:
        return self.frames / self.fps if self.fps else 0.0


class VideoReader:
    def __init__(self, path: str):
        self.path = path
        self.cap = cv2.VideoCapture(path)
        if not self.cap.isOpened():
            raise RuntimeError("无法打开视频。")
        self.info = VideoInfo(
            int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH)),
            int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT)),
            self.cap.get(cv2.CAP_PROP_FPS) or 30.0,
            int(self.cap.get(cv2.CAP_PROP_FRAME_COUNT)),
        )
        self._next_index = 0

    def frame(self, index: int) -> np.ndarray:
        index = max(0, min(index, self.info.frames - 1))
        if index != self._next_index:
            self.cap.set(cv2.CAP_PROP_POS_FRAMES, index)
        ok, frame = self.cap.read()
        if not ok:
            raise RuntimeError("无法读取当前帧。")
        self._next_index = index + 1
        return frame

    def close(self) -> None:
        self.cap.release()
