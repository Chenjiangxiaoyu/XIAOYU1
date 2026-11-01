# Post-Day-21 Improvement Roadmap

## 1. Real-World Validation and Calibration

Run the complete workflow with varied dance and fitness videos, multiple camera devices, lighting conditions, body types, loose clothing, partial occlusion, and multi-person scenes. Calibrate sampling thresholds, tracking thresholds, score thresholds, and the two-second completion rule against observed results rather than relying only on initial engineering defaults.

## 2. Dynamic Main-Subject Visual Cropping

The current reference-video crop is based on the learner's initial manual selection. Upgrade it to follow the selected subject over time using tracked pose centre, body scale, head/feet safety margins, and EMA-smoothed crop motion. This should reuse the old project's framing concepts without importing its desktop UI or video-export pipeline.

## 3. Mirror and Direction Controls

Add an explicit user choice between mirror practice and same-direction practice. The choice must consistently affect reference display, camera normalization, left/right joint mapping, 3D avatar orientation, and scoring.

## 4. Richer Motion Assessment

Extend landmark-distance scoring with joint-angle, movement-amplitude, direction, timing, and body-region-weighted scores. Feedback should explain the error, for example whether an arm is too low, insufficiently extended, or moving in the wrong direction.

## 5. Manual Course Editing

Allow a learner or instructor to merge or split automatically generated steps, adjust start/end times, select a representative keyframe, rename steps, and mark a step as demonstration-only. Automatic segmentation should be editable rather than treated as final truth.

## 6. Production 3D Avatar Integration

When a rigged GLB/GLTF model is provided, inspect its skeleton hierarchy, bind MediaPipe landmarks to model bones, handle coordinate systems and rest pose, and add model-specific calibration. Later improvements may include inverse kinematics, foot-contact stabilization, animation blending, and better torso/spine control.

## 7. Privacy, Data Lifecycle, and Export

Add a clear privacy screen, one-click local-data deletion, exportable training reports, and a way to reconnect a restored course to a user-selected source video. Any future cloud upload or account feature must be opt-in and must clearly state what is transmitted.

## 8. Performance and Device Adaptation

Introduce low/medium/high performance profiles, adaptive pose sampling budgets, optional 3D disablement, camera-resolution controls, and Web Worker offloading for preprocessing and scoring. Optimize mobile vertical layouts and provide framing guidance before practice begins.

## 9. Safer and Less Intrusive Coaching

Pause scoring when pose confidence is too low, prioritize framing guidance when the full body is missing, aggregate repeated errors, and avoid excessive speech interruptions. Support beginner, fitness, rehabilitation, and instructor modes with appropriate pace, threshold, and accessibility settings.

## 10. LLM as a Non-Critical Teaching Layer

If an LLM is added, use it only to improve action names, explanations, and reflective summaries. It must not decide identity tracking, pose correctness, score, completion, or safety-critical guidance.
