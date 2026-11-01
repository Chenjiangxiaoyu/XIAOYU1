import type { VideoSource } from '@/types/domain'
import type { FileService } from '../FileService'
export class WebFileService implements FileService {
  selectVideo(): Promise<VideoSource | null> {
    return new Promise((resolve) => {
      const input = document.createElement('input')
      input.type = 'file'
      input.accept = 'video/mp4'
      input.addEventListener('change', () => {
        const file = input.files?.item(0)
        resolve(file ? { id: crypto.randomUUID(), name: file.name, mimeType: file.type, size: file.size, url: URL.createObjectURL(file) } : null)
      }, { once: true })
      input.click()
    })
  }
  release(source: VideoSource) { URL.revokeObjectURL(source.url) }
}
