import type { MotionAnalysis } from './MotionAnalyzer'

export interface StepCandidate { index: number; startTime: number; endTime: number; keyframeTime: number; peakEnergy: number }

/** Turns motion-energy valleys into conservative candidate teaching steps. */
export class StepSegmenter {
  segment(analysis: MotionAnalysis, duration: number): StepCandidate[] {
    if (!analysis.samples.length) return []
    const boundaries = [0]
    const minStepSeconds = 1.5
    for (let index = 1; index < analysis.samples.length - 1; index += 1) {
      const current = analysis.samples[index]
      const previous = analysis.samples[index - 1]
      const next = analysis.samples[index + 1]
      const seconds = current.timestamp / 1000
      if (current.energy <= analysis.quietThreshold && current.energy <= previous.energy && current.energy < next.energy && seconds - boundaries.at(-1)! >= minStepSeconds) boundaries.push(seconds)
    }
    if (duration - boundaries.at(-1)! >= 0.8) boundaries.push(duration)
    if (boundaries.length === 1) boundaries.push(duration)
    return boundaries.slice(0, -1).map((startTime, index) => {
      const endTime = boundaries[index + 1]
      const withinStep = analysis.samples.filter((sample) => sample.timestamp / 1000 >= startTime && sample.timestamp / 1000 <= endTime)
      const peak = withinStep.reduce((best, sample) => sample.energy > best.energy ? sample : best, withinStep[0])
      return { index: index + 1, startTime, endTime, keyframeTime: peak ? peak.timestamp / 1000 : startTime, peakEnergy: peak?.energy ?? 0 }
    })
  }
}
