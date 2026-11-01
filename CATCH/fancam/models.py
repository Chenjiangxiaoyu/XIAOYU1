from __future__ import annotations

from dataclasses import asdict, dataclass, field
from enum import Enum
from pathlib import Path
import json


class SegmentKind(str, Enum):
    KEEP = "keep"
    SKIP = "skip"
    FULL_FRAME = "full_frame"


@dataclass
class Segment:
    """Timeline unit reserved for the later editor and segmented exports."""

    start_frame: int
    end_frame: int
    kind: SegmentKind = SegmentKind.KEEP
    label: str = ""

    def includes(self, frame: int) -> bool:
        return self.start_frame <= frame <= self.end_frame


@dataclass
class CropSettings:
    ratio_width: int = 9
    ratio_height: int = 16
    output_width: int = 1080
    output_height: int = 1920
    subject_scale: float = 2.15
    smoothing: float = 0.88
    look_ahead: float = 0.0
    lock_zoom: bool = True
    verification_stride: int = 5
    show_debug_overlay: bool = True
    stabilize_camera: bool = True
    position_dead_zone: float = 0.06
    scale_dead_zone: float = 0.12
    arm_margin: float = 1.25


@dataclass
class Project:
    source: str
    selected_frame: int
    initial_box: tuple[float, float, float, float]
    settings: CropSettings = field(default_factory=CropSettings)
    segments: list[Segment] = field(default_factory=list)

    def save(self, path: str | Path) -> None:
        data = asdict(self)
        Path(path).write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")

    @classmethod
    def load(cls, path: str | Path) -> "Project":
        data = json.loads(Path(path).read_text(encoding="utf-8"))
        data["settings"] = CropSettings(**data.get("settings", {}))
        data["segments"] = [Segment(**{**s, "kind": SegmentKind(s.get("kind", "keep"))}) for s in data.get("segments", [])]
        data["initial_box"] = tuple(data["initial_box"])
        return cls(**data)
