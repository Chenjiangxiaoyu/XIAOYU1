import type { CameraService } from './CameraService'
import type { FileService } from './FileService'
import type { SpeechService } from './SpeechService'
import type { StorageService } from './StorageService'
export interface PlatformService { camera: CameraService; file: FileService; storage: StorageService; speech: SpeechService }
