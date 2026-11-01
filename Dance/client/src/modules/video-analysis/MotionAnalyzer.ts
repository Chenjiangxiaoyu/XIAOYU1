import type { PoseSequence } from '@/modules/pose/PoseTypes'

export interface MotionSample { timestamp: number; energy: number }
export interface MotionAnalysis { samples: MotionSample[]; averageEnergy: number; peakEnergy: number; quietThreshold: number }

const IMPORTANT_JOINTS = [11, 12, 13, 14, 15, 16, 23, 24, 25, 26, 27, 28]

/** Measures body-relative joint velocity from preprocessed pose frames. */
export class MotionAnalyzer {
  analyze(sequence: PoseSequence): MotionAnalysis {
    const samples: MotionSample[] = []
    for (let index = 1; index < sequence.frames.length; index += 1) {
      const previous = sequence.frames[index - 1]
      const current = sequence.frames[index]
      const elapsedSeconds = Math.max(0.001, (current.timestamp - previous.timestamp) / 1000)
      const distances = IMPORTANT_JOINTS.map((joint) => {
        const before = previous.landmarks[joint]; const after = current.landmarks[joint]
        return before && after ? Math.hypot(after.x - before.x, after.y - before.y, after.z - before.z) / elapsedSeconds : 0
      })
      samples.push({ timestamp: current.timestamp, energy: distances.reduce((total, distance) => total + distance, 0) / distances.length })
    }
    const energies = samples.map((sample) => sample.energy).sort((left, right) => left - right)
    const quietThreshold = energies.length ? energies[Math.floor((energies.length - 1) * 0.35)] : 0
    return { samples, averageEnergy: energies.length ? energies.reduce((total, energy) => total + energy, 0) / energies.length : 0, peakEnergy: energies.at(-1) ?? 0, quietThreshold }
  }
}
