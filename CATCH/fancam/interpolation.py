from __future__ import annotations

import math
import cv2
import numpy as np

from .tracker import Box


def center_jump(first: Box, second: Box) -> float:
    ax, ay, aw, ah = first; bx, by, bw, bh = second
    return math.dist((ax + aw / 2, ay + ah / 2), (bx + bw / 2, by + bh / 2)) / max(1.0, ah)


def local_motion_score(previous: np.ndarray, current: np.ndarray, box: Box) -> float:
    """Median optical-flow magnitude near the target, normalized by target height."""
    height, width = previous.shape[:2]; x, y, w, h = box
    x1=max(0,int(x-w*.6)); y1=max(0,int(y-h*.35)); x2=min(width,int(x+w*1.6)); y2=min(height,int(y+h*1.35))
    if x2-x1<24 or y2-y1<24:return 0.0
    a=cv2.cvtColor(previous[y1:y2,x1:x2],cv2.COLOR_BGR2GRAY); b=cv2.cvtColor(current[y1:y2,x1:x2],cv2.COLOR_BGR2GRAY)
    scale=min(1.0,320/max(a.shape)); size=(max(16,round(a.shape[1]*scale)),max(16,round(a.shape[0]*scale)))
    if scale<1:a=cv2.resize(a,size); b=cv2.resize(b,size)
    flow=cv2.calcOpticalFlowFarneback(a,b,None,.5,3,15,3,5,1.2,0)
    magnitude=np.linalg.norm(flow,axis=2)
    return float(np.percentile(magnitude,70)/max(1.0,h*scale))


def interpolate_frames(previous: np.ndarray, current: np.ndarray, count: int) -> list[np.ndarray]:
    """Motion-compensated internal frames; never written to the final video."""
    if count<=0:return []
    h,w=previous.shape[:2]; scale=min(1.0,640/max(h,w)); size=(max(32,round(w*scale)),max(32,round(h*scale)))
    a=cv2.resize(previous,size) if scale<1 else previous; b=cv2.resize(current,size) if scale<1 else current
    ga=cv2.cvtColor(a,cv2.COLOR_BGR2GRAY); gb=cv2.cvtColor(b,cv2.COLOR_BGR2GRAY)
    forward=cv2.calcOpticalFlowFarneback(ga,gb,None,.5,4,21,4,7,1.5,0)
    backward=cv2.calcOpticalFlowFarneback(gb,ga,None,.5,4,21,4,7,1.5,0)
    grid_x,grid_y=np.meshgrid(np.arange(size[0],dtype=np.float32),np.arange(size[1],dtype=np.float32))
    result=[]
    for step in range(1,count+1):
        t=step/(count+1)
        wa=cv2.remap(a,grid_x-t*forward[...,0],grid_y-t*forward[...,1],cv2.INTER_LINEAR,borderMode=cv2.BORDER_REPLICATE)
        wb=cv2.remap(b,grid_x-(1-t)*backward[...,0],grid_y-(1-t)*backward[...,1],cv2.INTER_LINEAR,borderMode=cv2.BORDER_REPLICATE)
        middle=cv2.addWeighted(wa,1-t,wb,t,0)
        if scale<1:middle=cv2.resize(middle,(w,h),interpolation=cv2.INTER_CUBIC)
        result.append(middle)
    return result
