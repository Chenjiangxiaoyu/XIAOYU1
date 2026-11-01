# AI 3D Dance Fitness Adaptive Teaching System

Phase 0 foundation for a web-first dance fitness teaching system. The current stage supplies project structure, routes, application state, web platform services, and a lightweight health API only.

Day 2 adds local MP4 validation and a single-frame browser-side MediaPipe Pose Landmarker verification at `/analyze`; it does not upload the video to the server.

Day 3 extends this to a configurable 10 FPS MP4-to-`PoseSequence` analysis pass, also fully browser-side.

Day 4 adds a non-destructive preprocessing pass: confidence filtering, body-centred scale normalization, outlier suppression, and EMA smoothing.

Day 5 adds an opt-in local camera Pose verification screen with a real-time skeleton overlay and performance diagnostics.

Day 7 adds a shared person-selection state machine for both imported videos and live camera streams.

Day 8 adds motion-energy analysis and conservative algorithmic candidate step segmentation.

Day 9 turns those candidate steps into an inspectable teaching-course draft with timestamps, keyframes, important joints, and deterministic teaching hints.

Day 10 adds a step-by-step reference-video player that seeks to a selected step and stops automatically at its algorithmic end time.

Day 11 adds a Three.js 3D demonstration layer connected to the active teaching step; precise Pose-to-skeleton retargeting remains a later milestone.

Day 12 adds a minimal processed-PoseSequence-to-avatar retargeter for the active teaching step.

Day 13 adds local deterministic camera-to-reference keyframe scoring for the active course step.

Day 14 adds monotonic step temporal matching, progress display, and smoothed real-time scoring.

Day 15 adds gated step completion, sequential unlocking, and local training records.

Day 16 adds browser-local history and a compact training report based on passed-step records.

The consolidated implementation record for Days 3–11 is in [`docs/day-3-to-day-11.md`](docs/day-3-to-day-11.md).

## Commands

- `npm install` — install all workspace dependencies.
- `npm run dev` — start frontend and backend together.
- `npm run build` — type-check and build both workspaces.

The frontend runs on `http://localhost:5173`, and the health endpoint is `http://localhost:3000/api/health`.
