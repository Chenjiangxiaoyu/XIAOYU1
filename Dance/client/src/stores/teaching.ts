import { defineStore } from 'pinia'
import type { AnalysisStatus, CourseSummary, GeneratedCourse, SubjectRegion, TrainingStatus, VideoMetadata, VideoSource } from '@/types/domain'
import type { PoseAnalysisSummary, PoseFrame, PosePreprocessingReport, PoseSequence } from '@/modules/pose/PoseTypes'
import type { MotionAnalysis } from '@/modules/video-analysis/MotionAnalyzer'
import type { StepCandidate } from '@/modules/video-analysis/StepSegmenter'

export const useTeachingStore = defineStore('teaching', {
  state: () => ({ currentCourse: null as CourseSummary | null, generatedCourse: null as GeneratedCourse | null, manualSubjectRegion: null as SubjectRegion | null, currentStep: 0, unlockedStepCount: 0, passedStepIds: [] as string[], teachingMode: 'step' as 'step' | 'full', demonstrationMode: 'video' as 'video' | 'avatar', analysisStatus: 'idle' as AnalysisStatus, trainingStatus: 'idle' as TrainingStatus, sourceVideo: null as VideoSource | null, videoMetadata: null as VideoMetadata | null, poseSequence: null as PoseSequence | null, processedPoseSequence: null as PoseSequence | null, poseAnalysisSummary: null as PoseAnalysisSummary | null, posePreprocessingReport: null as PosePreprocessingReport | null, motionAnalysis: null as MotionAnalysis | null, stepCandidates: [] as StepCandidate[], cameraPoseFrame: null as PoseFrame | null, analysisProgress: 0 }),
})
