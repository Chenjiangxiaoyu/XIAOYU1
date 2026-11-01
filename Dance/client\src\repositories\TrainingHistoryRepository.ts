import type { TrainingHistory } from '@/types/domain'
export interface TrainingHistoryRepository { list(): Promise<TrainingHistory[]>; save(record: TrainingHistory): Promise<void> }
