from __future__ import annotations

from abc import ABC, abstractmethod
import numpy as np


Box = tuple[float, float, float, float]


class SubjectTracker(ABC):
    """Stable backend boundary for CSRT now and SAM 2 later."""

    @abstractmethod
    def initialize(self, frame: np.ndarray, box: Box) -> None: ...

    @abstractmethod
    def update(self, frame: np.ndarray) -> tuple[bool, Box]: ...


class CsrtTracker(SubjectTracker):
    def __init__(self):
        self._tracker = None

    @staticmethod
    def _create():
        import cv2

        if hasattr(cv2, "legacy") and hasattr(cv2.legacy, "TrackerCSRT_create"):
            return cv2.legacy.TrackerCSRT_create()
        if hasattr(cv2, "TrackerCSRT_create"):
            return cv2.TrackerCSRT_create()
        raise RuntimeError("当前 OpenCV 未包含 CSRT 跟踪器，请安装 opencv-contrib-python。")

    def initialize(self, frame: np.ndarray, box: Box) -> None:
        self._tracker = self._create()
        result = self._tracker.init(frame, tuple(map(int, box)))
        if result is False:
            raise RuntimeError("无法使用当前选框初始化跟踪器。")

    def update(self, frame: np.ndarray) -> tuple[bool, Box]:
        if self._tracker is None:
            raise RuntimeError("跟踪器尚未初始化。")
        ok, box = self._tracker.update(frame)
        return bool(ok), tuple(map(float, box))

