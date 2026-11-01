import type { PlatformService } from '../PlatformService'
import { WebCameraService } from './WebCameraService'
import { WebFileService } from './WebFileService'
import { WebSpeechService } from './WebSpeechService'
import { WebStorageService } from './WebStorageService'
export const webPlatform: PlatformService = { camera: new WebCameraService(), file: new WebFileService(), storage: new WebStorageService(), speech: new WebSpeechService() }
