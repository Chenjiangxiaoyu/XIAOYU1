export interface Landmark { x: number; y: number; z: number; visibility?: number; presence?: number }
export interface PoseFrame { timestamp: number; landmarks: Landmark[]; worldLandmarks?: Landmark[]; confidence: number }
export interface PoseCandidate { frame: PoseFrame; center: { x: number; y: number }; scale: number }
export type TrackingState = 'INITIALIZED' | 'TRACKED' | 'HOLD' | 'REJECTED'
export interface TrackingSelection { frame: PoseFrame | null; state: TrackingState; candidateCount: number }
export interface PoseSequence { duration: number; sampleFps: number; frames: PoseFrame[] }

export interface PoseAnalysisSummary {
  sampledFrames: number
  detectedFrames: number
  averageConfidence: number
  rejectedCandidates: number
  heldFrames: number
  fastMotionIntervals: number
  adaptiveSampledFrames: number
}

export interface PosePreprocessingReport {
  inputFrames: number
  acceptedFrames: number
  rejectedFrames: number
  lowConfidenceLandmarks: number
  outlierLandmarks: number
}
