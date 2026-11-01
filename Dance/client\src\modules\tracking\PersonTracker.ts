import type { PoseCandidate, TrackingSelection } from '@/modules/pose/PoseTypes'
import type { SubjectRegion } from '@/types/domain'

export interface PersonTrackerConfig { maxNormalizedDistance: number; maxScaleChange: number; reacquireAfterMissingFrames: number; centerSmoothing: number }
export const DEFAULT_PERSON_TRACKER_CONFIG: PersonTrackerConfig = { maxNormalizedDistance: 1.2, maxScaleChange: 0.6, reacquireAfterMissingFrames: 5, centerSmoothing: 0.65 }

/** Selects one consistent person from MediaPipe's candidate poses for both MP4 and camera streams. */
export class PersonTracker {
  private trusted: { center: { x: number; y: number }; scale: number } | null = null
  private missingFrames = 0
  private manualTarget: SubjectRegion | null = null
  private readonly config: PersonTrackerConfig

  constructor(config: PersonTrackerConfig = DEFAULT_PERSON_TRACKER_CONFIG) { this.config = config }
  reset() { this.trusted = null; this.missingFrames = 0 }
  setManualTarget(region: SubjectRegion | null) { this.manualTarget = region; this.reset() }

  select(candidates: PoseCandidate[]): TrackingSelection {
    if (!candidates.length) { this.missingFrames += 1; return { frame: null, state: 'HOLD', candidateCount: 0 } }
    if (!this.trusted || this.missingFrames >= this.config.reacquireAfterMissingFrames) {
      const selected = candidates.reduce((best, candidate) => this.initialScore(candidate) > this.initialScore(best) ? candidate : best)
      this.trusted = { center: selected.center, scale: selected.scale }; this.missingFrames = 0
      return { frame: selected.frame, state: 'INITIALIZED', candidateCount: candidates.length }
    }
    const ranked = candidates.map((candidate) => ({ candidate, distance: Math.hypot(candidate.center.x - this.trusted!.center.x, candidate.center.y - this.trusted!.center.y) / this.trusted!.scale, scaleChange: Math.abs(candidate.scale - this.trusted!.scale) / this.trusted!.scale }))
      .filter((item) => item.distance <= this.config.maxNormalizedDistance && item.scaleChange <= this.config.maxScaleChange)
      .sort((left, right) => (left.distance + left.scaleChange * 0.35 - left.candidate.frame.confidence * 0.15) - (right.distance + right.scaleChange * 0.35 - right.candidate.frame.confidence * 0.15))
    if (!ranked.length) { this.missingFrames += 1; return { frame: null, state: 'REJECTED', candidateCount: candidates.length } }
    const selected = ranked[0].candidate; const keep = this.config.centerSmoothing; const update = 1 - keep
    this.trusted = { center: { x: this.trusted.center.x * keep + selected.center.x * update, y: this.trusted.center.y * keep + selected.center.y * update }, scale: this.trusted.scale * keep + selected.scale * update }
    this.missingFrames = 0
    return { frame: selected.frame, state: 'TRACKED', candidateCount: candidates.length }
  }

  private initialScore(candidate: PoseCandidate) {
    if (!this.manualTarget) return candidate.frame.confidence
    const region = this.manualTarget
    const inside = candidate.center.x >= region.x && candidate.center.x <= region.x + region.width && candidate.center.y >= region.y && candidate.center.y <= region.y + region.height
    const distance = Math.hypot(candidate.center.x - (region.x + region.width / 2), candidate.center.y - (region.y + region.height / 2))
    return (inside ? 10 : 0) + candidate.frame.confidence - distance
  }
}
