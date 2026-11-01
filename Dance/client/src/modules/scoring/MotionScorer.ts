import type { PoseFrame, PoseSequence } from '@/modules/pose/PoseTypes'
import { DEFAULT_POSE_PREPROCESSING, PosePreprocessor } from '@/modules/pose/PosePreprocessor'
import type { TeachingStep } from '@/types/domain'

const SCORING_JOINTS = [11, 12, 13, 14, 15, 16, 23, 24, 25, 26, 27, 28]
const JOINT_NAMES: Record<number, string> = { 11: '左肩', 12: '右肩', 13: '左肘', 14: '右肘', 15: '左腕', 16: '右腕', 23: '左髋', 24: '右髋', 25: '左膝', 26: '右膝', 27: '左踝', 28: '右踝' }

export interface MotionScore { overall: number; jointScores: Array<{ joint: string; score: number }>; feedback: string[] }

/** Deterministic pose-distance score. It deliberately uses no LLM or image appearance data. */
export class MotionScorer {
  private readonly preprocessor = new PosePreprocessor()

  score(cameraFrame: PoseFrame, referenceSequence: PoseSequence, step: TeachingStep): MotionScore | null {
    const reference = referenceSequence.frames.reduce((nearest, frame) => Math.abs(frame.timestamp - step.keyframeTime * 1000) < Math.abs(nearest.timestamp - step.keyframeTime * 1000) ? frame : nearest, referenceSequence.frames[0])
    return reference ? this.scoreAgainstFrame(cameraFrame, reference) : null
  }

  scoreAgainstFrame(cameraFrame: PoseFrame, reference: PoseFrame): MotionScore | null {
    const processed = this.preprocessor.process({ duration: 0, sampleFps: 20, frames: [cameraFrame] }, { ...DEFAULT_POSE_PREPROCESSING, mirrorX: true }).sequence.frames[0]
    if (!processed) return null
    const jointScores = SCORING_JOINTS.flatMap((index) => {
      const live = processed.landmarks[index]
      const target = reference.landmarks[index]
      if (!live || !target) return []
      const distance = Math.hypot(live.x - target.x, live.y - target.y, live.z - target.z)
      return [{ joint: JOINT_NAMES[index], score: Math.round(Math.max(0, 1 - distance / 1.2) * 100) }]
    })
    if (!jointScores.length) return null
    const overall = Math.round(jointScores.reduce((total, item) => total + item.score, 0) / jointScores.length)
    const feedback = [...jointScores].sort((left, right) => left.score - right.score).slice(0, 3).filter((item) => item.score < 75).map((item) => `${item.joint}与标准关键帧差异较大（${item.score} 分）`)
    return { overall, jointScores, feedback: feedback.length ? feedback : ['动作接近标准关键帧，保持当前姿势。'] }
  }
}
