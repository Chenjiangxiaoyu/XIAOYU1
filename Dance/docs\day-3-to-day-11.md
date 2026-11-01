# Days 3–11 — Pose Analysis, Teaching Course, and 3D Demonstration

This document consolidates the development record for Days 3 through 11. Video analysis and camera pose recognition run locally in the browser whenever possible. Apart from the health check, video and pose data are not sent to the Express server.

## Day 3 — MP4 to PoseSequence

`/analyze` can process a validated MP4 at 10 FPS. Each sampled video frame is passed to `PoseExtractor`, which converts the MediaPipe result into the internal `PoseFrame` format. Successful frames are collected in a `PoseSequence` containing source timestamps, normalized landmarks, optional world landmarks, and confidence values.

The result panel reports sampled frames, detected pose frames, and average visibility. Frames with no detected person are never fabricated; they are absent from the sequence and reflected by the detected-frame ratio. This establishes a measurable baseline for confidence filtering, outlier handling, normalization, and smoothing.

## Day 4 — Pose Preprocessing

The **Preprocess PoseSequence** action on `/analyze` preserves the raw sequence and produces a separate processed sequence for subsequent motion analysis and scoring. Processing is performed in this order:

1. Drop frames whose average confidence is below `0.45`.
2. Use a landmark visibility threshold of `0.35`; where a prior stable point exists, a low-visibility landmark reuses that point.
3. Centre every pose at the hip midpoint, with the shoulder midpoint as fallback, then scale by the largest available shoulder width, hip width, or torso length.
4. Suppress implausible normalized joint jumps larger than `0.65` body-scale units by retaining the prior stable point.
5. Apply exponential moving-average smoothing: `smoothed = previous × 0.6 + current × 0.4`.

The mirror option is available in preprocessing configuration but remains disabled for uploaded reference MP4s. It will be enabled selectively for mirrored camera input later.

## Day 5 — Camera Pose Verification

The `/training` page opens the user's camera through `WebCameraService` only after they click **Start Camera** and grant browser permission. The live stream goes directly to the existing browser-side `PoseExtractor`. The page displays a mirrored preview, a 33-landmark pose overlay when a person is detected, detection FPS, average landmark visibility, and landmark count.

The stream stops when the user clicks **Close Camera** or leaves the page. This phase does not record, score, upload, or persist camera video. Camera pose data remains only in runtime state for the current session.

## Day 7 — Shared Person Tracking

`PersonTracker` is shared by the imported-video and live-camera pipelines. MediaPipe Pose Landmarker is configured to produce up to three person candidates. The tracker initializes the main person from the highest-confidence candidate, then ranks later candidates by body-centre continuity, body-scale continuity, and confidence.

- A candidate too far from the trusted body centre or with an implausible scale change is rejected.
- If no candidate is detected, the tracker retains identity state briefly but never fabricates a `PoseFrame` for scoring.
- After five consecutive missing frames, it can reacquire the highest-confidence candidate.

MP4 analysis displays rejected-candidate and short-hold counts. Camera status reports temporary holds and rejected off-target candidates. This is the minimum browser-native adaptation of the old Fancam Maker tracking arbiter; segmentation, optical-flow interpolation, and manual repair remain deferred.

## Day 8 — Motion Energy and Candidate Steps

After preprocessing, `MotionAnalyzer` calculates motion energy and candidate teaching steps. It measures body-relative velocity between consecutive processed pose frames across the shoulders, elbows, wrists, hips, knees, and ankles, creating an energy time series independent of body position and approximate scale.

`StepSegmenter` finds conservative local minima below the bottom 35% energy threshold, requires at least 1.5 seconds between boundaries, and uses the highest-energy frame in each segment as its representative keyframe. The output is only an algorithmic time-range proposal. A future LLM may name and explain steps, but it must not determine their boundaries.

## Day 9 — Course Draft Generation

Candidate segments can be converted into an in-memory `GeneratedCourse`. Each teaching step contains traceable start and end times, a representative keyframe, important joints ranked by processed-pose displacement, and a deterministic teaching hint.

The course page presents this draft. No LLM or 3D retargeting is used at this stage. A future LLM may enrich action names and natural-language explanation, but cannot alter algorithmically measured time ranges, keyframes, or real-time scoring results.

## Day 10 — Step-by-Step Teaching Player

The course page can replay the imported video as a reference demonstration. When a user selects a teaching step, the player seeks to that step's start. When playback begins, it plays only the algorithmic time interval of the selected step and pauses automatically at the end.

The player uses the Day 9 course steps, playback ranges, and representative keyframes. It is the unified playback-control entry point for later 3D demonstration, allowing the presentation to change without changing the temporal meaning of step-by-step teaching.

## Day 11 — 3D Demonstration Layer

The course page adds a browser-side Three.js 3D avatar preview. The avatar emphasizes upper- or lower-body movement according to the important joints inferred from the active teaching step, and it shares the active-step and playback state from Day 10.

This is not retargeting of the source video and must not be treated as an exact reference motion. It establishes a replaceable WebGL presentation layer and step-control interface. The next stage will convert the processed reference `PoseSequence` into skeletal rotations that drive this avatar.
