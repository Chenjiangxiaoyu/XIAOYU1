from __future__ import annotations

from dataclasses import dataclass
import numpy as np

from .models import CropSettings


@dataclass
class CropWindow:
    x: int
    y: int
    width: int
    height: int


class SmoothCropper:
    """Turns noisy subject boxes into a steady, fixed-aspect virtual camera."""

    def __init__(self, frame_width: int, frame_height: int, settings: CropSettings):
        self.fw = frame_width
        self.fh = frame_height
        self.s = settings
        self._state: np.ndarray | None = None
        self._base_subject_height: float | None = None

    def _target(self, box: tuple[float, float, float, float], min_view_width: float = 0.0,
                stabilized: bool = False, min_view_height: float = 0.0) -> np.ndarray:
        x, y, w, h = box
        if self._base_subject_height is None:
            self._base_subject_height = h
        ratio = self.s.ratio_width / self.s.ratio_height
        if stabilized and (min_view_width>0 or min_view_height>0):
            # Width must contain the arm-span margin, while height must contain
            # the complete detected body plus head/foot safety margins.
            target_w=max(min_view_width,min_view_height*ratio)
            target_h=target_w/ratio
        else:
            subject_h = self._base_subject_height if self.s.lock_zoom else h
            target_h = min(self.fh, max(subject_h * self.s.subject_scale, self.fh * 0.25))
            target_w = target_h * ratio
        if target_w > self.fw:
            target_w = self.fw
            target_h = target_w / ratio
        cx = x + w * (0.5 if stabilized else 0.5 + self.s.look_ahead)
        cy = y + h * 0.46
        return np.array([cx, cy, target_w, target_h], dtype=np.float64)

    def update(self, box: tuple[float, float, float, float], min_view_width: float = 0.0,
               stabilized: bool = False, min_view_height: float = 0.0) -> CropWindow:
        target = self._target(box, min_view_width, stabilized, min_view_height)
        if self._state is None:
            self._state = target
        else:
            a = float(np.clip(self.s.smoothing, 0.0, 0.98))
            distance = np.linalg.norm(target[:2] - self._state[:2])
            threshold = max(self._state[2], self._state[3]) * 0.025
            if distance < threshold:
                target[:2] = self._state[:2]
            self._state = a * self._state + (1.0 - a) * target
        cx, cy, width, height = self._state
        width, height = int(round(width)), int(round(height))
        x = int(round(cx - width / 2))
        y = int(round(cy - height / 2))
        if width <= self.fw: x = max(0, min(x, self.fw - width))
        if height <= self.fh: y = max(0, min(y, self.fh - height))
        return CropWindow(x, y, width, height)

    @staticmethod
    def render(frame: np.ndarray, crop: CropWindow, output_size: tuple[int, int]) -> np.ndarray:
        import cv2

        output_w,output_h=output_size; sx=output_w/max(1,crop.width); sy=output_h/max(1,crop.height)
        matrix=np.array([[sx,0,-crop.x*sx],[0,sy,-crop.y*sy]],dtype=np.float32)
        return cv2.warpAffine(frame,matrix,(output_w,output_h),flags=cv2.INTER_LANCZOS4,borderMode=cv2.BORDER_CONSTANT,borderValue=(18,18,18))
