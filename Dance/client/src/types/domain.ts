export interface VideoSource { id: string; name: string; mimeType: string; size: number; url: string }
export interface CourseSummary { id: string; title: string; createdAt: string; stepCount: number }
export interface TeachingStep {
  id: string
  index: number
  title: string
  startTime: number
  endTime: number
  keyframeTime: number
  importantJoints: string[]
  teachingHint: string
  recommendedPlaybackRate: number
}
export interface GeneratedCourse extends CourseSummary {
  sourceVideoName: string
  steps: TeachingStep[]
}
export interface TrainingHistory { id: string; courseId: string; stepId: string; stepIndex: number; completedAt: string; score: number; progress: number; stableMilliseconds: number }
export type AnalysisStatus = 'idle' | 'validating' | 'analyzing' | 'ready' | 'failed'
export type TrainingStatus = 'idle' | 'preparing' | 'training' | 'completed' | 'failed'
export interface VideoMetadata { duration: number; width: number; height: number; fileSize: number }
export interface SubjectRegion { x: number; y: number; width: number; height: number }
