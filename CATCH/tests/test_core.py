import json
import tempfile
import unittest
from pathlib import Path
import numpy as np

from fancam.crop import SmoothCropper
from fancam.models import CropSettings, Project, Segment, SegmentKind
from fancam.arbiter import TrackingArbiter
from fancam.verifier import VerificationResult
from fancam.analysis import AnalysisResult, FrameAnalysis, rebuild_crop_windows, replace_from_frame, roundtrip_excursion_start
from fancam.processor import _keep_ranges, _render_full_frame
from fancam.interpolation import interpolate_frames, local_motion_score
from fancam.camera import BodyAwareCameraStabilizer, CameraTarget


class CropTests(unittest.TestCase):
    def test_detects_unverified_tracker_roundtrip(self):
        def item(index,x,state="CSRT-ONLY"):
            box=(x,20,40,100); return FrameAnalysis(index,box,box,state,"test")
        frames=[item(0,100,"VERIFIED"),item(1,110),item(2,190),item(3,105)]
        self.assertEqual(roundtrip_excursion_start(frames,(102,20,40,100),100,30),0)

    def test_does_not_reject_verified_real_roundtrip(self):
        def item(index,x,state="CSRT-ONLY"):
            box=(x,20,40,100); return FrameAnalysis(index,box,box,state,"test")
        frames=[item(0,100,"VERIFIED"),item(1,110),item(2,190,"VERIFIED"),item(3,105)]
        self.assertIsNone(roundtrip_excursion_start(frames,(102,20,40,100),100,30))

    def test_crop_stays_inside_frame_and_keeps_ratio(self):
        settings = CropSettings(9, 16, 1080, 1920, 2.0, 0.0)
        cropper = SmoothCropper(1920, 1080, settings)
        crop = cropper.update((1780, 100, 120, 600))
        self.assertGreaterEqual(crop.x, 0)
        self.assertLessEqual(crop.x + crop.width, 1920)
        self.assertLessEqual(crop.y + crop.height, 1080)
        self.assertAlmostEqual(crop.width / crop.height, 9 / 16, places=2)

    def test_smoothing_reduces_jump(self):
        settings = CropSettings(smoothing=0.9)
        cropper = SmoothCropper(1920, 1080, settings)
        a = cropper.update((100, 100, 200, 600))
        b = cropper.update((1200, 100, 200, 600))
        self.assertLess(b.x - a.x, 1100)

    def test_full_frame_output_preserves_entire_source_with_letterbox(self):
        frame = np.full((90, 160, 3), (30, 80, 140), dtype=np.uint8)
        rendered = _render_full_frame(frame, (90, 160))
        self.assertEqual(rendered.shape, (160, 90, 3))
        self.assertTrue(np.all(rendered[80, 45] == frame[45, 80]))
        self.assertTrue(np.all(rendered[0, 0] == (18, 18, 18)))

    def test_internal_interpolation_creates_tracking_frames_only(self):
        first=np.zeros((72,96,3),dtype=np.uint8); second=np.zeros_like(first); first[25:45,12:32]=255; second[25:45,44:64]=255
        middle=interpolate_frames(first,second,2)
        self.assertEqual(len(middle),2)
        self.assertEqual(middle[0].shape,first.shape)
        self.assertGreater(local_motion_score(first,second,(10,20,24,30)),0.02)

    def test_body_camera_locks_small_jitter_and_reserves_arm_span(self):
        stabilizer=BodyAwareCameraStabilizer((100,50,80,200))
        landmarks=[(140.0,130.0,0.0) for _ in range(33)]
        landmarks[11]=(120,110,.9); landmarks[12]=(160,110,.9); landmarks[23]=(125,170,.9); landmarks[24]=(155,170,.9)
        landmarks[15]=(60,120,.9); landmarks[16]=(220,120,.9)
        verification=VerificationResult(True,.9,.8,(140,140),(100,50,80,200),landmarks,None)
        first=stabilizer.update((100,50,80,200),verification)
        second=stabilizer.update((104,52,80,200),verification)
        self.assertEqual(first.box[:2],second.box[:2])
        self.assertGreaterEqual(second.min_view_width,200)

    def test_body_camera_keeps_visible_feet_and_bottom_safety_margin(self):
        landmarks=[(320.0,300.0,0.0) for _ in range(33)]
        landmarks[0]=(320,100,.9); landmarks[2]=(310,105,.9); landmarks[5]=(330,105,.9)
        landmarks[11]=(270,260,.9); landmarks[12]=(370,260,.9)
        landmarks[23]=(285,470,.9); landmarks[24]=(355,470,.9)
        landmarks[15]=(170,300,.9); landmarks[16]=(470,300,.9)
        for i,x in ((27,285),(28,355),(29,280),(30,360),(31,275),(32,365)):
            landmarks[i]=(x,800,.9)
        verification=VerificationResult(True,.9,.8,(320,365),(160,100,320,700),landmarks,None)
        target=BodyAwareCameraStabilizer((250,100,140,700)).update((250,100,140,700),verification)
        crop=SmoothCropper(640,1080,CropSettings(9,16,1080,1920,smoothing=0)).update(
            target.box,target.min_view_width,True,target.min_view_height)
        self.assertGreaterEqual(crop.y+crop.height,880)
        self.assertLessEqual(crop.y,70)

    def test_manual_roi_size_does_not_determine_anatomy_view_width(self):
        landmarks=[(140.0,130.0,0.0) for _ in range(33)]
        landmarks[11]=(120,110,.9); landmarks[12]=(160,110,.9); landmarks[23]=(125,170,.9); landmarks[24]=(155,170,.9); landmarks[15]=(60,120,.9); landmarks[16]=(220,120,.9)
        verification=VerificationResult(True,.9,.8,(140,140),(100,50,80,200),landmarks,None)
        narrow=BodyAwareCameraStabilizer((125,70,30,120)).update((125,70,30,120),verification)
        wide=BodyAwareCameraStabilizer((60,20,160,280)).update((60,20,160,280),verification)
        self.assertAlmostEqual(narrow.min_view_width,wide.min_view_width)

    def test_stabilized_crop_changes_are_smoothed(self):
        settings=CropSettings(9,16,1080,1920,smoothing=.5)
        cropper=SmoothCropper(1920,1080,settings); box=(800,300,100,300)
        widths=[cropper.update(box,value,True).width for value in (400,600,600)]
        self.assertLessEqual(widths[0],widths[1]); self.assertLessEqual(widths[1],widths[2])

    def test_preview_and_export_rebuild_identical_crop_path(self):
        settings=CropSettings(9,16,180,320,smoothing=.9)
        frames=[FrameAnalysis(i,(100+i*5,50,80,200),(100+i*5,50,80,200),"VERIFIED","test",camera_target=CameraTarget((100+i*5,50,80,200),320)) for i in range(5)]
        rebuild_crop_windows(frames,640,360,settings); first=[(f.crop_window.x,f.crop_window.y,f.crop_window.width,f.crop_window.height) for f in frames]
        rebuild_crop_windows(frames,640,360,settings); second=[(f.crop_window.x,f.crop_window.y,f.crop_window.width,f.crop_window.height) for f in frames]
        self.assertEqual(first,second)

    def test_camera_shrinks_only_after_repeated_smaller_anatomy(self):
        def pose(shoulder_width):
            half=shoulder_width/2; landmarks=[(140.0,130.0,0.0) for _ in range(33)]
            landmarks[11]=(140-half,110,.9); landmarks[12]=(140+half,110,.9); landmarks[23]=(125,170,.9); landmarks[24]=(155,170,.9)
            return VerificationResult(True,.9,.8,(140,140),(100,50,80,200),landmarks,None)
        stabilizer=BodyAwareCameraStabilizer((100,50,80,200)); large=stabilizer.update((100,50,80,200),pose(80)).min_view_width
        first_small=stabilizer.update((100,50,80,200),pose(40)).min_view_width
        self.assertEqual(first_small,large)
        result=first_small
        for _ in range(4):result=stabilizer.update((100,50,80,200),pose(40)).min_view_width
        self.assertLess(result,large)

    def test_camera_does_not_follow_csrt_ahead_of_unmoved_torso(self):
        landmarks=[(140.0,130.0,0.0) for _ in range(33)]
        landmarks[11]=(120,110,.9); landmarks[12]=(160,110,.9); landmarks[23]=(125,170,.9); landmarks[24]=(155,170,.9)
        verification=VerificationResult(True,.9,.8,(140,140),(100,50,80,200),landmarks,None)
        stabilizer=BodyAwareCameraStabilizer((100,50,80,200)); locked=stabilizer.update((100,50,80,200),verification)
        csrt_ahead=stabilizer.update((190,50,80,200),None)
        self.assertEqual(locked.box[:2],csrt_ahead.box[:2])


class ProjectTests(unittest.TestCase):
    def test_project_round_trip_and_future_segments(self):
        project = Project("demo.mp4", 10, (1, 2, 3, 4), segments=[Segment(10, 30), Segment(31, 40, SegmentKind.SKIP, "遮挡")])
        with tempfile.TemporaryDirectory() as d:
            path = Path(d) / "demo.fancam.json"
            project.save(path)
            loaded = Project.load(path)
        self.assertEqual(loaded.initial_box, (1, 2, 3, 4))
        self.assertEqual(loaded.segments[1].kind, SegmentKind.SKIP)

    def test_manual_reframe_keeps_prefix_and_replaces_suffix(self):
        def frame(index, x, state="CSRT-ONLY"):
            box = (x, 10, 20, 60)
            return FrameAnalysis(index, box, box, state, "test")
        original = AnalysisResult([frame(i, i) for i in range(6)], [], 30, 0, 6, 0, 0)
        replacement = AnalysisResult([frame(i, 100 + i) for i in range(3, 5)], [], 30, 3, 6, 0, 0)
        merged = replace_from_frame(original, replacement, 3)
        self.assertEqual([item.final_box[0] for item in merged.frames], [0, 1, 2, 103, 104, 5])
        self.assertEqual(merged.source_start_frame, 0)

    def test_deleted_segments_become_discontinuous_audio_ranges(self):
        project = Project("demo.mp4", 0, (0, 0, 10, 10), segments=[
            Segment(10, 19, SegmentKind.SKIP), Segment(30, 39, SegmentKind.SKIP)
        ])
        self.assertEqual(_keep_ranges(project, 0, 49, 10), [(0.0, 1.0), (2.0, 3.0), (4.0, 5.0)])

    def test_full_frame_segment_round_trips_in_project(self):
        project = Project("demo.mp4", 0, (0, 0, 10, 10), segments=[Segment(5, 12, SegmentKind.FULL_FRAME)])
        with tempfile.TemporaryDirectory() as d:
            path = Path(d) / "full-frame.fancam.json"; project.save(path); loaded = Project.load(path)
        self.assertEqual(loaded.segments[0].kind, SegmentKind.FULL_FRAME)


class ArbiterTests(unittest.TestCase):
    def test_rejects_expanded_csrt_box_and_keeps_locked_size(self):
        arbiter = TrackingArbiter((100, 50, 80, 200))
        decision = arbiter.decide(True, (80, 20, 190, 310), None)
        self.assertEqual(decision.state, "HOLD")
        self.assertEqual(decision.box[2:], (80.0, 200.0))

    def test_human_verification_corrects_and_requests_reinitialize(self):
        arbiter = TrackingArbiter((100, 50, 80, 200))
        verification = VerificationResult(True, 0.9, 0.8, (260, 170), (220, 50, 80, 220), [], None)
        decision = arbiter.decide(True, (100, 50, 180, 300), verification)
        self.assertEqual(decision.state, "CORRECTED")
        self.assertTrue(decision.reinitialize)
        self.assertAlmostEqual(decision.box[0] + decision.box[2] / 2, 260)

    def test_verified_candidate_blends_centers_but_never_zooms(self):
        arbiter = TrackingArbiter((100, 50, 80, 200))
        verification = VerificationResult(True, 0.85, 0.75, (152, 150), (112, 50, 80, 200), [], None)
        decision = arbiter.decide(True, (108, 50, 88, 205), verification)
        self.assertEqual(decision.state, "VERIFIED")
        self.assertEqual(decision.box[2:], (80.0, 200.0))

    def test_rejects_pose_that_jumps_to_a_neighbouring_dancer(self):
        arbiter = TrackingArbiter((100, 50, 80, 200))
        nearby = VerificationResult(True, 0.9, 0.8, (145, 150), (105, 50, 80, 200), [], None)
        arbiter.decide(True, (104, 50, 80, 200), nearby)
        wrong_person = VerificationResult(True, 0.95, 0.9, (275, 150), (235, 50, 80, 200), [], None)
        decision = arbiter.decide(True, (108, 50, 80, 200), wrong_person)
        self.assertEqual(decision.state, "POSE-REJECTED")
        self.assertFalse(decision.reinitialize)
        self.assertLess(decision.box[0], 150)


if __name__ == "__main__":
    unittest.main()
