import type { PoseFrame, PoseSequence } from '@/modules/pose/PoseTypes'
import { DEFAULT_POSE_PREPROCESSING, PosePreprocessor } from '@/modules/pose/PosePreprocessor'
import type { TeachingStep } from '@/types/domain'

const MATCH_JOINTS = [11, 12, 13, 14, 15, 16, 23, 24, 25, 26, 27, 28]
export interface StepMatch { referenceFrame: PoseFrame; progress: number; completed: boolean }

/** Monotonic local search aligns live practice to an ordered reference step without using an ML model. */
export class StepProgressMatcher {
  private readonly preprocessor = new PosePreprocessor()
  private activeStepId = ''
  private lastIndex = 0

  reset() { this.activeStepId = ''; this.lastIndex = 0 }

  match(cameraFrame: PoseFrame, sequence: PoseSequence, step: TeachingStep): StepMatch | null {
    const live = this.preprocessor.process({ duration: 0, sampleFps: 20, frames: [cameraFrame] }, { ...DEFAULT_POSE_PREPROCESSING, mirrorX: true }).sequence.frames[0]
    const frames = sequence.frames.filter((frame) => frame.timestamp >= step.startTime * 1000 && frame.timestamp <= step.endTime * 1000)
    if (!live || !frames.length) return null
    if (this.activeStepId !== step.id) { this.activeStepId = step.id; this.lastIndex = 0 }
    const windowEnd = Math.min(frames.length - 1, this.lastIndex + 12)
    let bestIndex = this.lastIndex
    let bestDistance = Number.POSITIVE_INFINITY
    for (let index = this.lastIndex; index <= windowEnd; index += 1) {
      const distance = this.distance(live, frames[index])
      if (distance < bestDistance) { bestDistance = distance; bestIndex = index }
    }
    this.lastIndex = bestIndex
    const progress = frames.length === 1 ? 1 : bestIndex / (frames.length - 1)
    return { referenceFrame: frames[bestIndex], progress, completed: progress >= 0.9 }
  }

  private distance(live: PoseFrame, reference: PoseFrame) {
    let total = 0
    let count = 0
    for (const index of MATCH_JOINTS) {
      const current = live.landmarks[index]
      const target = reference.landmarks[index]
      if (!current || !target) continue
      total += Math.hypot(current.x - target.x, current.y - target.y, current.z - target.z)
      count += 1
    }
    return count ? total / count : Number.POSITIVE_INFINITY
  }
}
