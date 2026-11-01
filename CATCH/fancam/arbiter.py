from __future__ import annotations

from dataclasses import dataclass
import math

from .tracker import Box
from .verifier import VerificationResult


@dataclass
class TrackingDecision:
    box: Box
    state: str
    accept_csrt: bool
    reinitialize: bool = False
    reason: str = ""


class TrackingArbiter:
    """Gives CSRT proposal rights while pose/contour checks keep veto rights."""

    def __init__(self, initial_box: Box):
        self.initial = tuple(map(float, initial_box))
        self.trusted = self.initial
        self.uncertain_frames = 0
        self.last_human_center: tuple[float, float] | None = None

    @staticmethod
    def _center(box: Box):
        x, y, w, h = box
        return x + w / 2, y + h / 2

    def _locked_box(self, center: tuple[float, float]) -> Box:
        _, _, w, h = self.initial
        return center[0] - w / 2, center[1] - h / 2, w, h

    def decide(self, csrt_ok: bool, candidate: Box, verification: VerificationResult | None) -> TrackingDecision:
        previous_center = self._center(self.trusted)
        candidate_center = self._center(candidate)
        _, _, iw, ih = self.initial
        _, _, cw, ch = candidate
        area_ratio = (cw * ch) / max(1.0, iw * ih)
        jump = math.dist(previous_center, candidate_center) / max(1.0, ih)
        size_bad = not (0.62 <= area_ratio <= 1.45)
        motion_bad = jump > 0.70

        verified = verification is not None and verification.available and verification.confidence >= 0.42 and verification.body_center is not None
        if verified:
            human_center = verification.body_center
            disagreement = math.dist(candidate_center, human_center) / max(1.0, ih)
            human_jump = (math.dist(self.last_human_center, human_center) / max(1.0, ih)) if self.last_human_center else 0.0

            # Pose is a verifier, not a free-ranging detector. A skeleton found far
            # from CSRT's local proposal is almost certainly a neighbouring dancer.
            # Comparing against both signals still permits fast real movement when
            # CSRT and the body detector move together.
            if disagreement > 0.48 or (self.last_human_center and human_jump > 0.95 and disagreement > 0.24):
                if csrt_ok and not size_bad and not motion_bad:
                    accepted = self._locked_box(candidate_center)
                    self.trusted = accepted
                    self.uncertain_frames += 1
                    return TrackingDecision(accepted, "POSE-REJECTED", True, False, "人体骨骼距当前目标过远，疑似识别到邻近人物")
                self.uncertain_frames += 1
                return TrackingDecision(self.trusted, "HOLD", False, False, "骨骼跳变且 CSRT 不可信，保持上一位置")

            self.last_human_center = human_center
            if size_bad or motion_bad or not csrt_ok:
                corrected = self._locked_box(human_center)
                self.trusted = corrected
                self.uncertain_frames = 0
                return TrackingDecision(corrected, "CORRECTED", False, True, "人体轮廓与关键点将跟踪框拉回目标")
            blended = (candidate_center[0] * 0.72 + human_center[0] * 0.28, candidate_center[1] * 0.72 + human_center[1] * 0.28)
            accepted = self._locked_box(blended)
            self.trusted = accepted
            self.uncertain_frames = 0
            return TrackingDecision(accepted, "VERIFIED", True, False, "CSRT 与人体验证一致")

        if csrt_ok and not size_bad and not motion_bad:
            accepted = self._locked_box(candidate_center)
            self.trusted = accepted
            self.uncertain_frames += 1
            return TrackingDecision(accepted, "CSRT-ONLY", True, False, "本帧采用 CSRT 跟踪结果")

        self.uncertain_frames += 1
        return TrackingDecision(self.trusted, "HOLD", False, False, "跟踪不可信，保持上一可靠位置")
