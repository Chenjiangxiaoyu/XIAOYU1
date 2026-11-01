from __future__ import annotations

from dataclasses import dataclass
import os
from typing import Iterable

import cv2
import numpy as np

from .tracker import Box


POSE_EDGES = (
    (0, 2), (0, 5), (2, 7), (5, 8),
    (11, 12), (11, 13), (13, 15), (12, 14), (14, 16),
    (11, 23), (12, 24), (23, 24),
    (23, 25), (25, 27), (27, 29), (29, 31),
    (24, 26), (26, 28), (28, 30), (30, 32),
)
CORE_POINTS = (0, 2, 5, 11, 12, 23, 24, 25, 26, 27, 28)


@dataclass
class VerificationResult:
    available: bool = False
    pose_score: float = 0.0
    contour_score: float = 0.0
    body_center: tuple[float, float] | None = None
    body_box: Box | None = None
    landmarks: list[tuple[float, float, float]] | None = None
    contour: np.ndarray | None = None
    roi_origin: tuple[int, int] = (0, 0)

    @property
    def confidence(self) -> float:
        if not self.available:
            return 0.0
        return 0.55 * self.pose_score + 0.45 * self.contour_score


class HumanVerifier:
    """Independent pose + silhouette checks inside CSRT's proposed search region."""

    def __init__(self):
        os.environ.setdefault("MPLCONFIGDIR", os.path.join(os.getcwd(), ".mpl-cache"))
        import mediapipe as mp

        self.mp = mp
        self.pose = mp.solutions.pose.Pose(
            # The verification ROI moves with CSRT, so each sampled frame is
            # intentionally re-detected instead of reusing MediaPipe's ROI state.
            static_image_mode=True,
            model_complexity=1,
            smooth_landmarks=False,
            enable_segmentation=True,
            smooth_segmentation=False,
            min_detection_confidence=0.45,
            min_tracking_confidence=0.45,
        )

    @staticmethod
    def _expanded_roi(frame: np.ndarray, box: Box, pad: float = 0.28):
        fh, fw = frame.shape[:2]
        x, y, w, h = box
        px, py = w * pad, h * pad
        x1, y1 = max(0, int(x - px)), max(0, int(y - py))
        x2, y2 = min(fw, int(x + w + px)), min(fh, int(y + h + py))
        return frame[y1:y2, x1:x2], x1, y1

    def verify(self, frame: np.ndarray, candidate: Box) -> VerificationResult:
        roi, ox, oy = self._expanded_roi(frame, candidate)
        if roi.size == 0 or min(roi.shape[:2]) < 32:
            return VerificationResult()
        result = self.pose.process(cv2.cvtColor(roi, cv2.COLOR_BGR2RGB))
        if result.pose_landmarks is None:
            return VerificationResult()
        rh, rw = roi.shape[:2]
        landmarks = [(lm.x * rw + ox, lm.y * rh + oy, float(lm.visibility)) for lm in result.pose_landmarks.landmark]
        visible = [landmarks[i][2] for i in CORE_POINTS]
        pose_score = float(np.mean(visible)) if visible else 0.0

        mask = result.segmentation_mask
        contour = None
        body_box = None
        contour_score = 0.0
        mask_center = None
        if mask is not None:
            binary = (mask > 0.55).astype(np.uint8) * 255
            kernel = np.ones((3, 3), np.uint8)
            binary = cv2.morphologyEx(binary, cv2.MORPH_OPEN, kernel)
            binary = cv2.morphologyEx(binary, cv2.MORPH_CLOSE, kernel, iterations=2)
            contours, _ = cv2.findContours(binary, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            if contours:
                local = max(contours, key=cv2.contourArea)
                area = cv2.contourArea(local)
                if area > rw * rh * 0.025:
                    contour = local + np.array([[[ox, oy]]], dtype=local.dtype)
                    bx, by, bw, bh = cv2.boundingRect(contour)
                    body_box = (float(bx), float(by), float(bw), float(bh))
                    moments = cv2.moments(contour)
                    if moments["m00"]:
                        mask_center = (moments["m10"] / moments["m00"], moments["m01"] / moments["m00"])
                    fill = area / max(1.0, bw * bh)
                    contour_score = float(np.clip(fill * 1.65, 0.0, 1.0))

        def mean_point(indices: Iterable[int]):
            pts = [landmarks[i] for i in indices if landmarks[i][2] >= 0.35]
            if not pts:
                return None
            return (sum(p[0] for p in pts) / len(pts), sum(p[1] for p in pts) / len(pts))

        shoulders = mean_point((11, 12))
        hips = mean_point((23, 24))
        centers = []
        if shoulders: centers.append((shoulders, 0.42))
        if hips: centers.append((hips, 0.38))
        if mask_center: centers.append((mask_center, 0.20))
        if centers:
            total = sum(weight for _, weight in centers)
            body_center = (
                sum(point[0] * weight for point, weight in centers) / total,
                sum(point[1] * weight for point, weight in centers) / total,
            )
        else:
            body_center = mask_center
        return VerificationResult(True, pose_score, contour_score, body_center, body_box, landmarks, contour, (ox, oy))

    def close(self):
        self.pose.close()


def draw_verification(frame: np.ndarray, result: VerificationResult, csrt_box: Box, final_box: Box, state: str) -> np.ndarray:
    canvas = frame.copy()
    if result.contour is not None:
        cv2.drawContours(canvas, [result.contour], -1, (255, 255, 255), 2, cv2.LINE_AA)
    if result.landmarks:
        for a, b in POSE_EDGES:
            pa, pb = result.landmarks[a], result.landmarks[b]
            if pa[2] >= 0.35 and pb[2] >= 0.35:
                cv2.line(canvas, (int(pa[0]), int(pa[1])), (int(pb[0]), int(pb[1])), (94, 220, 151), 2, cv2.LINE_AA)
        for i in CORE_POINTS:
            x, y, vis = result.landmarks[i]
            color = (90, 225, 140) if vis >= 0.55 else (70, 190, 245)
            cv2.circle(canvas, (int(x), int(y)), 3, color, -1, cv2.LINE_AA)
    x, y, w, h = map(int, csrt_box)
    cv2.rectangle(canvas, (x, y), (x + w, y + h), (150, 150, 150), 1)
    x, y, w, h = map(int, final_box)
    cv2.rectangle(canvas, (x, y), (x + w, y + h), (126, 126, 245), 2)
    cv2.putText(canvas, f"{state}  pose:{result.pose_score:.2f} contour:{result.contour_score:.2f}", (18, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.62, (255, 255, 255), 2, cv2.LINE_AA)
    return canvas
