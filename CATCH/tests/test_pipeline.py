import tempfile
import unittest
from pathlib import Path

import cv2
import numpy as np

from fancam.models import CropSettings, Project, Segment, SegmentKind
from fancam.processor import process_project
from fancam.analysis import analyze_project


class PipelineTests(unittest.TestCase):
    def test_synthetic_video_exports_mp4(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            source = root / "source.mp4"
            output = root / "fancam.mp4"
            writer = cv2.VideoWriter(str(source), cv2.VideoWriter_fourcc(*"mp4v"), 12, (320, 180))
            rng = np.random.default_rng(7)
            texture = rng.integers(20, 240, (60, 30, 3), dtype=np.uint8)
            for i in range(24):
                frame = np.full((180, 320, 3), 35, dtype=np.uint8)
                x = 30 + i * 3
                frame[60:120, x:x+30] = texture
                writer.write(frame)
            writer.release()
            project = Project(str(source), 0, (30, 60, 30, 60), CropSettings(9, 16, 180, 320, 2.2, 0.85),
                              [Segment(8, 11, SegmentKind.SKIP, "人物出画"),
                               Segment(12, 15, SegmentKind.FULL_FRAME, "原始全景")])
            short_analysis = analyze_project(project, end_frame=5, include_unanalyzed_tail=True)
            self.assertEqual(len(short_analysis.frames), 24)
            self.assertTrue(all(frame.state != "UNANALYZED" for frame in short_analysis.frames[:6]))
            self.assertTrue(all(frame.state == "UNANALYZED" for frame in short_analysis.frames[6:]))
            result = process_project(project, output)
            self.assertTrue(output.exists())
            self.assertGreater(output.stat().st_size, 1000)
            cap = cv2.VideoCapture(str(output))
            self.assertEqual(int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)), 180)
            self.assertEqual(int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT)), 320)
            self.assertEqual(int(cap.get(cv2.CAP_PROP_FRAME_COUNT)), 20)
            cap.set(cv2.CAP_PROP_POS_FRAMES, 8)
            ok, full_frame = cap.read()
            self.assertTrue(ok)
            self.assertLess(float(full_frame[5, 5].mean()), 28)
            cap.release()
            self.assertEqual(result.processed_frames, 20)


if __name__ == "__main__":
    unittest.main()
