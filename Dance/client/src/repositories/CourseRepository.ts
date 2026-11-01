import type { CourseSummary } from '@/types/domain'
export interface CourseRepository { list(): Promise<CourseSummary[]>; get(id: string): Promise<CourseSummary | null>; save(course: CourseSummary): Promise<void> }
