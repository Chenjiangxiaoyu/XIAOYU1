import type { GeneratedCourse, TeachingStep, VideoSource } from '@/types/domain'
import type { PoseSequence } from '@/modules/pose/PoseTypes'
import type { StepCandidate } from '@/modules/video-analysis/StepSegmenter'

const JOINT_NAMES: Record<number, string> = {
  11: '左肩', 12: '右肩', 13: '左肘', 14: '右肘', 15: '左腕', 16: '右腕',
  23: '左髋', 24: '右髋', 25: '左膝', 26: '右膝', 27: '左踝', 28: '右踝',
}

/** Builds a deterministic course draft. Semantic naming can refine this later, but never replaces measured timing. */
export class CourseBuilder {
  build(source: VideoSource, sequence: PoseSequence, candidates: StepCandidate[]): GeneratedCourse {
    const medianPeakEnergy = [...candidates].map((candidate) => candidate.peakEnergy).sort((left, right) => left - right)[Math.floor(candidates.length / 2)] ?? 0
    const steps = candidates.map((candidate) => this.buildStep(candidate, sequence, medianPeakEnergy))
    return { id: `course-${Date.now()}`, title: `${source.name.replace(/\.[^/.]+$/, '')} 教学课程`, sourceVideoName: source.name, createdAt: new Date().toISOString(), stepCount: steps.length, steps }
  }

  private buildStep(candidate: StepCandidate, sequence: PoseSequence, medianPeakEnergy: number): TeachingStep {
    const frames = sequence.frames.filter((frame) => frame.timestamp / 1000 >= candidate.startTime && frame.timestamp / 1000 <= candidate.endTime)
    const motionByJoint = new Map<number, number>()
    for (let frameIndex = 1; frameIndex < frames.length; frameIndex += 1) {
      const previous = frames[frameIndex - 1]
      const current = frames[frameIndex]
      for (const jointIndex of Object.keys(JOINT_NAMES).map(Number)) {
        const before = previous.landmarks[jointIndex]
        const after = current.landmarks[jointIndex]
        if (!before || !after) continue
        const distance = Math.hypot(after.x - before.x, after.y - before.y, after.z - before.z)
        motionByJoint.set(jointIndex, (motionByJoint.get(jointIndex) ?? 0) + distance)
      }
    }
    const importantJoints = [...motionByJoint.entries()].sort(([, left], [, right]) => right - left).slice(0, 3).map(([index]) => JOINT_NAMES[index])
    const focus = importantJoints.length ? importantJoints.join('、') : '全身节奏与重心'
    const energyRatio = medianPeakEnergy > 0 ? candidate.peakEnergy / medianPeakEnergy : 1
    const recommendedPlaybackRate = energyRatio >= 1.8 ? 0.5 : energyRatio >= 1.25 ? 0.75 : 1
    return { id: `step-${candidate.index}-${Math.round(candidate.startTime * 1000)}`, index: candidate.index, title: `动作步骤 ${candidate.index}`, startTime: candidate.startTime, endTime: candidate.endTime, keyframeTime: candidate.keyframeTime, importantJoints, teachingHint: `先观察这一段的标准动作，重点关注${focus}的连贯变化。`, recommendedPlaybackRate }
  }
}
