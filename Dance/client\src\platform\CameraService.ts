export interface CameraService { open(): Promise<MediaStream>; close(stream: MediaStream): void }
