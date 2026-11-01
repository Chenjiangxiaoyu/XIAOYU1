import type { StorageService } from '../StorageService'
export class WebStorageService implements StorageService {
  async get<T>(key: string): Promise<T | null> { const value = localStorage.getItem(key); return value ? JSON.parse(value) as T : null }
  async set<T>(key: string, value: T) { localStorage.setItem(key, JSON.stringify(value)) }
  async remove(key: string) { localStorage.removeItem(key) }
}
