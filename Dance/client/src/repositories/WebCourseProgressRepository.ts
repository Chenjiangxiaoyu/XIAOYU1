import type { GeneratedCourse } from '@/types/domain'
import type { StorageService } from '@/platform/StorageService'

export interface SavedCourseProgress { course: GeneratedCourse; unlockedStepCount: number; passedStepIds: string[] }
const STORAGE_KEY = 'dance-fitness.course-progress'
export class WebCourseProgressRepository {
  constructor(private readonly storage: StorageService) {}
  load() { return this.storage.get<SavedCourseProgress>(STORAGE_KEY) }
  save(progress: SavedCourseProgress) { return this.storage.set(STORAGE_KEY, progress) }
}
