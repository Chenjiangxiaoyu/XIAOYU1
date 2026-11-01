import type { Landmark, PoseFrame, PosePreprocessingReport, PoseSequence } from './PoseTypes'

export interface PosePreprocessingConfig {
  minFrameConfidence: number
  minLandmarkVisibility: number
  maxNormalizedJointJump: number
  emaPreviousWeight: number
  mirrorX: boolean
}

export const DEFAULT_POSE_PREPROCESSING: PosePreprocessingConfig = {
  minFrameConfidence: 0.45,
  minLandmarkVisibility: 0.35,
  maxNormalizedJointJump: 0.65,
  emaPreviousWeight: 0.6,
  mirrorX: false,
}

/** Produces a stable, body-centred sequence while retaining the raw sequence in the store. */
export class PosePreprocessor {
  process(sequence: PoseSequence, config: PosePreprocessingConfig = DEFAULT_POSE_PREPROCESSING): { sequence: PoseSequence; report: PosePreprocessingReport } {
    const report: PosePreprocessingReport = { inputFrames: sequence.frames.length, acceptedFrames: 0, rejectedFrames: 0, lowConfidenceLandmarks: 0, outlierLandmarks: 0 }
    const output: PoseFrame[] = []
    let priorNormalized: Landmark[] | undefined
    let priorSmoothed: Landmark[] | undefined

    for (const frame of sequence.frames) {
      if (frame.confidence < config.minFrameConfidence || frame.landmarks.length < 25) { report.rejectedFrames += 1; continue }
      const normalized = this.normalizeLandmarks(frame.landmarks, config.mirrorX)
      const cleaned = normalized.map((landmark, index) => {
        const previous = priorNormalized?.[index]
        const lowConfidence = (landmark.visibility ?? 1) < config.minLandmarkVisibility
        const jump = previous ? this.distance(landmark, previous) : 0
        if ((lowConfidence || jump > config.maxNormalizedJointJump) && previous) {
          if (lowConfidence) report.lowConfidenceLandmarks += 1
          if (jump > config.maxNormalizedJointJump) report.outlierLandmarks += 1
          return { ...previous, visibility: landmark.visibility }
        }
        if (lowConfidence) report.lowConfidenceLandmarks += 1
        return landmark
      })
      const smoothed = cleaned.map((current, index) => this.ema(priorSmoothed?.[index], current, config.emaPreviousWeight))
      output.push({ timestamp: frame.timestamp, landmarks: smoothed, worldLandmarks: frame.worldLandmarks ? this.normalizeLandmarks(frame.worldLandmarks, config.mirrorX) : undefined, confidence: frame.confidence })
      priorNormalized = cleaned; priorSmoothed = smoothed; report.acceptedFrames += 1
    }
    return { sequence: { duration: sequence.duration, sampleFps: sequence.sampleFps, frames: output }, report }
  }

  private normalizeLandmarks(landmarks: Landmark[], mirrorX: boolean): Landmark[] {
    const hipCenter = this.midpoint(landmarks[23], landmarks[24])
    const shoulderCenter = this.midpoint(landmarks[11], landmarks[12])
    const center = hipCenter ?? shoulderCenter ?? { x: 0, y: 0, z: 0 }
    const shoulderWidth = this.distance(landmarks[11], landmarks[12])
    const hipWidth = this.distance(landmarks[23], landmarks[24])
    const torsoLength = shoulderCenter && hipCenter ? this.distance(shoulderCenter, hipCenter) : 0
    const scale = Math.max(shoulderWidth, hipWidth, torsoLength, 0.05)
    return landmarks.map((landmark) => ({ ...landmark, x: (mirrorX ? center.x - landmark.x : landmark.x - center.x) / scale, y: (landmark.y - center.y) / scale, z: (landmark.z - center.z) / scale }))
  }

  private midpoint(first?: Landmark, second?: Landmark): Landmark | null {
    if (!first || !second) return null
    return { x: (first.x + second.x) / 2, y: (first.y + second.y) / 2, z: (first.z + second.z) / 2 }
  }

  private distance(first?: Landmark, second?: Landmark): number {
    if (!first || !second) return 0
    return Math.hypot(first.x - second.x, first.y - second.y, first.z - second.z)
  }

  private ema(previous: Landmark | undefined, current: Landmark, previousWeight: number): Landmark {
    if (!previous) return current
    const currentWeight = 1 - previousWeight
    return { ...current, x: previous.x * previousWeight + current.x * currentWeight, y: previous.y * previousWeight + current.y * currentWeight, z: previous.z * previousWeight + current.z * currentWeight }
  }
}
