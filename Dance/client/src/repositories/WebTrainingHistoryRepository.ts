import type { TrainingHistory } from '@/types/domain'
import type { StorageService } from '@/platform/StorageService'
import type { TrainingHistoryRepository } from './TrainingHistoryRepository'

const STORAGE_KEY = 'dance-fitness.training-history'
export class WebTrainingHistoryRepository implements TrainingHistoryRepository {
  constructor(private readonly storage: StorageService) {}
  async list() { return (await this.storage.get<TrainingHistory[]>(STORAGE_KEY) ?? []).sort((left, right) => right.completedAt.localeCompare(left.completedAt)) }
  async save(record: TrainingHistory) { const records = await this.list(); await this.storage.set(STORAGE_KEY, [record, ...records]) }
}
