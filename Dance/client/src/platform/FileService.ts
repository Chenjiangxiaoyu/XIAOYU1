import type { VideoSource } from '@/types/domain'
export interface FileService { selectVideo(): Promise<VideoSource | null>; release(source: VideoSource): void }
