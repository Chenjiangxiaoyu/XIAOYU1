import type { CameraService } from '../CameraService'
export class WebCameraService implements CameraService {
  open() { return navigator.mediaDevices.getUserMedia({ video: { facingMode: 'user', width: { ideal: 1280 }, height: { ideal: 720 } }, audio: false }) }
  close(stream: MediaStream) { stream.getTracks().forEach((track) => track.stop()) }
}
