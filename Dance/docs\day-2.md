# Day 2 — MP4 and Pose technical validation

The `/analyze` page now accepts a local MP4, checks its size, duration, dimensions, and browser decodability, then previews it without uploading it to the server.

Use **验证当前帧 Pose** after moving the video to a frame where the full person is visible. The browser initializes MediaPipe Pose Landmarker and reports the landmark count and average visibility for that frame. This is a technical-risk check only; frame-sequence sampling, smoothing, segmentation, scoring, and 3D retargeting remain out of scope.

The WASM runtime and Lite pose model are fetched from their official public distribution URLs at first use. A future deployment task will mirror these assets to a stable domestic-accessible source before release.
