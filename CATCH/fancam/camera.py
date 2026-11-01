from __future__ import annotations

from dataclasses import dataclass
import math

from .tracker import Box
from .verifier import VerificationResult


@dataclass
class CameraTarget:
    box: Box
    min_view_width: float = 0.0
    min_view_height: float = 0.0
    center_locked: bool = False
    scale_locked: bool = False


class BodyAwareCameraStabilizer:
    """Converts noisy tracking boxes into a restrained virtual camera path."""

    def __init__(self, initial_box: Box, position_dead_zone: float = .06,
                 scale_dead_zone: float = .12, arm_margin: float = 1.25):
        x,y,w,h=map(float,initial_box); self.initial_w=w; self.initial_h=h; self.center=[x+w/2,y+h*.46]; self.center_initialized=False
        self.position_dead_zone=position_dead_zone; self.scale_dead_zone=scale_dead_zone; self.arm_margin=arm_margin
        self.filtered_arm_span=0.0; self.shrink_confirmations=0
        self.filtered_body_height=0.0; self.filtered_vertical_offset=0.0

    @staticmethod
    def _midpoint(landmarks, first, second):
        a,b=landmarks[first],landmarks[second]
        if a[2]<.35 or b[2]<.35:return None
        return ((a[0]+b[0])/2,(a[1]+b[1])/2)

    def _anatomy(self, verification: VerificationResult | None):
        if not verification or not verification.available or not verification.landmarks:return None,None,None,None,None
        points=verification.landmarks; shoulders=self._midpoint(points,11,12); hips=self._midpoint(points,23,24)
        center=verification.body_center; torso=None
        if shoulders and hips:
            center=(shoulders[0]*.48+hips[0]*.52,shoulders[1]*.48+hips[1]*.52)
            torso=math.dist(shoulders,hips)
        spans=[]
        for left,right,multiplier in ((15,16,1.0),(13,14,1.35),(11,12,2.35)):
            if points[left][2]>=.35 and points[right][2]>=.35:spans.append(math.dist(points[left][:2],points[right][:2])*multiplier)
        # Use actual head and foot landmarks as a hard framing constraint.  The
        # extra bottom margin protects toes during jumps and extended poses.
        head=[points[i][1] for i in (0,2,5,7,8) if points[i][2]>=.35]
        feet=[points[i][1] for i in (27,28,29,30,31,32) if points[i][2]>=.35]
        body_top=min(head) if head else (verification.body_box[1] if verification.body_box else None)
        body_bottom=max(feet) if feet else (verification.body_box[1]+verification.body_box[3] if verification.body_box else None)
        return center,torso,max(spans) if spans else None,body_top,body_bottom

    def update(self, tracking_box: Box, verification: VerificationResult | None) -> CameraTarget:
        x,y,w,h=tracking_box; fallback=(x+w/2,y+h*.46); anatomy_center,torso,arm_span,body_top,body_bottom=self._anatomy(verification)
        if anatomy_center and not self.center_initialized:
            self.center=[anatomy_center[0],anatomy_center[1]]; self.center_initialized=True
        # Once anatomy has established the real body center, never let raw CSRT
        # motion steer the camera between verification frames. CSRT may react to
        # a leading hand or background texture before the torso actually moves.
        desired=anatomy_center or (self.center if self.center_initialized else fallback)
        dx,dy=desired[0]-self.center[0],desired[1]-self.center[1]
        dead_x=self.initial_h*self.position_dead_zone; dead_y=self.initial_h*self.position_dead_zone*.72
        locked=abs(dx)<=dead_x and abs(dy)<=dead_y
        if not locked:
            move_x=dx-math.copysign(dead_x,dx) if abs(dx)>dead_x else 0.0; move_y=dy-math.copysign(dead_y,dy) if abs(dy)>dead_y else 0.0
            distance=math.hypot(dx,dy)/max(1.0,self.initial_h); alpha=.42 if distance>.45 else .20
            self.center[0]+=move_x*alpha; self.center[1]+=move_y*alpha

        if arm_span:
            if self.filtered_arm_span<=0:
                self.filtered_arm_span=arm_span
            elif arm_span>self.filtered_arm_span*1.03:
                self.filtered_arm_span=self.filtered_arm_span*.75+arm_span*.25; self.shrink_confirmations=0
            elif arm_span<self.filtered_arm_span*.90:
                self.shrink_confirmations+=1
                if self.shrink_confirmations>=4:
                    self.filtered_arm_span=self.filtered_arm_span*.92+arm_span*.08
            else:
                self.shrink_confirmations=0
        if anatomy_center and body_top is not None and body_bottom is not None and body_bottom>body_top:
            body_height=body_bottom-body_top
            # 5% above the head and 12% below the lowest visible foot.
            padded_top=body_top-body_height*.05; padded_bottom=body_bottom+body_height*.12
            required_height=padded_bottom-padded_top
            desired_offset=(padded_top+padded_bottom)/2-anatomy_center[1]
            if self.filtered_body_height<=0:
                self.filtered_body_height=required_height; self.filtered_vertical_offset=desired_offset
            else:
                # Expand/recenter promptly to protect feet; relax slowly so a
                # single uncertain landmark cannot create pumping or bobbing.
                height_alpha=.28 if required_height>self.filtered_body_height else .06
                offset_alpha=.20 if desired_offset>self.filtered_vertical_offset else .08
                self.filtered_body_height=(1-height_alpha)*self.filtered_body_height+height_alpha*required_height
                self.filtered_vertical_offset=(1-offset_alpha)*self.filtered_vertical_offset+offset_alpha*desired_offset
        framing_y=self.center[1]+self.filtered_vertical_offset
        stable_box=(self.center[0]-self.initial_w/2,framing_y-self.initial_h*.46,self.initial_w,self.initial_h)
        # The manual ROI contributes identity and the fallback center only. Once
        # pose is trusted, framing width comes exclusively from measured anatomy.
        view_width=self.filtered_arm_span*self.arm_margin if self.filtered_arm_span else 0.0
        return CameraTarget(stable_box,min_view_width=view_width,min_view_height=self.filtered_body_height,
                            center_locked=locked,scale_locked=True)
