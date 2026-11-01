import type { PoseSequence } from '@/modules/pose/PoseTypes'
import type { TeachingStep } from '@/types/domain'

export interface AvatarPose { leftArm: number; rightArm: number; leftLeg: number; rightLeg: number; torso: number }
const REST_POSE: AvatarPose = { leftArm: -0.25, rightArm: 0.25, leftLeg: -0.08, rightLeg: 0.08, torso: 0 }

/** Maps reference-pose limb directions to the simple teaching avatar's joint rotations. */
export class PoseRetargeter {
  poseAt(sequence: PoseSequence | null, step: TeachingStep, elapsedSeconds: number): AvatarPose {
    if (!sequence?.frames.length) return REST_POSE
    const duration = Math.max(step.endTime - step.startTime, 0.01)
    const targetTimestamp = (step.startTime + (elapsedSeconds % duration)) * 1000
    const frames = sequence.frames.filter((frame) => frame.timestamp >= step.startTime * 1000 && frame.timestamp <= step.endTime * 1000)
    const frame = frames.reduce((nearest, candidate) => Math.abs(candidate.timestamp - targetTimestamp) < Math.abs(nearest.timestamp - targetTimestamp) ? candidate : nearest, frames[0])
    if (!frame) return REST_POSE
    const angle = (from: number, to: number, fallback: number) => {
      const start = frame.landmarks[from]
      const end = frame.landmarks[to]
      if (!start || !end) return fallback
      // Pose y grows downward, while Three.js y grows upward; cylinder rest direction is downward.
      return Math.atan2(-(end.y - start.y), end.x - start.x) + Math.PI / 2
    }
    const shoulderMid = midpoint(frame.landmarks[11], frame.landmarks[12])
    const hipMid = midpoint(frame.landmarks[23], frame.landmarks[24])
    const torso = shoulderMid && hipMid ? Math.atan2(-(shoulderMid.y - hipMid.y), shoulderMid.x - hipMid.x) - Math.PI / 2 : 0
    return {
      leftArm: angle(11, 15, REST_POSE.leftArm), rightArm: angle(12, 16, REST_POSE.rightArm),
      leftLeg: angle(23, 27, REST_POSE.leftLeg), rightLeg: angle(24, 28, REST_POSE.rightLeg), torso,
    }
  }
}

function midpoint(left: { x: number; y: number } | undefined, right: { x: number; y: number } | undefined) {
  return left && right ? { x: (left.x + right.x) / 2, y: (left.y + right.y) / 2 } : null
}
