import { FilesetResolver, PoseLandmarker } from '@mediapipe/tasks-vision'
import type { Landmark, PoseCandidate, PoseFrame } from './PoseTypes'

const WASM_ROOT = 'https://cdn.jsdelivr.net/npm/@mediapipe/tasks-vision@latest/wasm'
const MODEL_URL = 'https://storage.googleapis.com/mediapipe-models/pose_landmarker/pose_landmarker_lite/float16/latest/pose_landmarker_lite.task'

/** Keeps MediaPipe types and model lifecycle outside of business modules. */
export class PoseExtractor {
  private landmarker: PoseLandmarker | null = null

  async initialize(): Promise<void> {
    if (this.landmarker) return
    const vision = await FilesetResolver.forVisionTasks(WASM_ROOT)
    this.landmarker = await PoseLandmarker.createFromOptions(vision, {
      baseOptions: { modelAssetPath: MODEL_URL }, runningMode: 'VIDEO', numPoses: 3,
    })
  }

  detectVideo(video: HTMLVideoElement, timestamp: number): PoseFrame | null {
    return this.detectVideoCandidates(video, timestamp)[0]?.frame ?? null
  }

  detectVideoCandidates(video: HTMLVideoElement, timestamp: number): PoseCandidate[] {
    if (!this.landmarker) throw new Error('PoseExtractor 尚未初始化')
    const result = this.landmarker.detectForVideo(video, timestamp)
    const convert = (items: Array<{ x: number; y: number; z: number; visibility?: number }>): Landmark[] => items.map(({ x, y, z, visibility }) => ({ x, y, z, visibility }))
    return result.landmarks.map((rawLandmarks, index) => {
      const landmarks = convert(rawLandmarks)
      const confidence = rawLandmarks.reduce((total, landmark) => total + (landmark.visibility ?? 0), 0) / rawLandmarks.length
      const center = this.centerOf(landmarks)
      return { frame: { timestamp, landmarks, worldLandmarks: result.worldLandmarks[index] ? convert(result.worldLandmarks[index]) : undefined, confidence }, center, scale: this.bodyScale(landmarks) }
    })
  }

  private centerOf(landmarks: Landmark[]): { x: number; y: number } {
    const midpoint = (first: number, second: number) => ({ x: (landmarks[first].x + landmarks[second].x) / 2, y: (landmarks[first].y + landmarks[second].y) / 2 })
    if (landmarks[23] && landmarks[24]) return midpoint(23, 24)
    if (landmarks[11] && landmarks[12]) return midpoint(11, 12)
    return { x: landmarks[0]?.x ?? 0.5, y: landmarks[0]?.y ?? 0.5 }
  }

  private bodyScale(landmarks: Landmark[]): number {
    const distance = (first: number, second: number) => landmarks[first] && landmarks[second] ? Math.hypot(landmarks[first].x - landmarks[second].x, landmarks[first].y - landmarks[second].y) : 0
    return Math.max(distance(11, 12), distance(23, 24), distance(11, 23), distance(12, 24), 0.05)
  }

  close(): void { this.landmarker?.close(); this.landmarker = null }
}
