import type { VideoMetadata, VideoSource } from '@/types/domain'
import type { PoseExtractor } from '@/modules/pose/PoseExtractor'
import type { PoseAnalysisSummary, PoseSequence } from '@/modules/pose/PoseTypes'
import type { PersonTracker } from '@/modules/tracking/PersonTracker'

export const VIDEO_RULES = { maxBytes: 200 * 1024 * 1024, maxDurationSeconds: 60, recommendedMinDurationSeconds: 10, sampleFps: 10, fastMotionSampleFps: 30 }

export class VideoAnalyzer {
  async readMetadata(source: VideoSource): Promise<VideoMetadata> {
    const video = document.createElement('video')
    video.preload = 'metadata'; video.src = source.url
    await new Promise<void>((resolve, reject) => { video.onloadedmetadata = () => resolve(); video.onerror = () => reject(new Error('浏览器无法解码该视频')) })
    const metadata = { duration: video.duration, width: video.videoWidth, height: video.videoHeight, fileSize: source.size }
    video.removeAttribute('src'); video.load()
    return metadata
  }

  validate(source: VideoSource, metadata: VideoMetadata): string | null {
    if (source.mimeType !== 'video/mp4' && !source.name.toLowerCase().endsWith('.mp4')) return '第一版仅支持 MP4 视频。'
    if (source.size > VIDEO_RULES.maxBytes) return `视频不能超过 ${VIDEO_RULES.maxBytes / 1024 / 1024} MB。`
    if (!Number.isFinite(metadata.duration) || metadata.duration <= 0) return '视频时长无效。'
    if (metadata.duration > VIDEO_RULES.maxDurationSeconds) return `第一版暂只支持 ${VIDEO_RULES.maxDurationSeconds} 秒以内的视频。`
    if (!metadata.width || !metadata.height) return '无法读取视频画面尺寸。'
    return null
  }

  async extractPoseSequence(
    video: HTMLVideoElement,
    extractor: PoseExtractor,
    tracker: PersonTracker,
    onProgress: (completed: number, total: number) => void,
  ): Promise<{ sequence: PoseSequence; summary: PoseAnalysisSummary }> {
    const duration = video.duration
    const interval = 1 / VIDEO_RULES.sampleFps
    const baseTimes = Array.from({ length: Math.ceil(duration / interval) }, (_, index) => Math.min(index * interval, Math.max(0, duration - 0.001)))
    const coarse = await this.sample(video, extractor, tracker, baseTimes, (done) => onProgress(done, baseTimes.length * 2))
    const fastIntervals = this.findFastIntervals(coarse.frames)
    const sampleTimes = this.buildAdaptiveTimes(baseTimes, fastIntervals)
    // MediaPipe VIDEO timestamps must increase; restart its video state before the high-density second pass.
    extractor.close(); await extractor.initialize()
    const final = await this.sample(video, extractor, tracker, sampleTimes, (done) => onProgress(baseTimes.length + done, baseTimes.length + sampleTimes.length))
    const frames = final.frames
    const averageConfidence = frames.length ? frames.reduce((total, frame) => total + frame.confidence, 0) / frames.length : 0
    return { sequence: { duration, sampleFps: VIDEO_RULES.sampleFps, frames }, summary: { sampledFrames: baseTimes.length, adaptiveSampledFrames: sampleTimes.length, fastMotionIntervals: fastIntervals.length, detectedFrames: frames.length, averageConfidence, rejectedCandidates: final.rejectedCandidates, heldFrames: final.heldFrames } }
  }

  private async sample(video: HTMLVideoElement, extractor: PoseExtractor, tracker: PersonTracker, sampleTimes: number[], onProgress: (completed: number) => void) {
    const frames: PoseSequence['frames'] = []
    let rejectedCandidates = 0
    let heldFrames = 0
    video.pause()
    tracker.reset()
    for (let index = 0; index < sampleTimes.length; index += 1) {
      const timestamp = sampleTimes[index]
      await this.seekTo(video, timestamp)
      const selection = tracker.select(extractor.detectVideoCandidates(video, timestamp * 1000))
      if (selection.frame) frames.push(selection.frame)
      if (selection.state === 'REJECTED') rejectedCandidates += 1
      if (selection.state === 'HOLD') heldFrames += 1
      onProgress(index + 1)
      if (index % 5 === 0) await new Promise<void>((resolve) => requestAnimationFrame(() => resolve()))
    }
    return { frames, rejectedCandidates, heldFrames }
  }

  private findFastIntervals(frames: PoseSequence['frames']) {
    const fast: Array<{ start: number; end: number }> = []
    for (let index = 1; index < frames.length; index += 1) {
      const previous = frames[index - 1]; const current = frames[index]
      const scale = Math.max(this.distance(previous.landmarks[11], previous.landmarks[12]), this.distance(previous.landmarks[23], previous.landmarks[24]), 0.05)
      const joints = [11, 12, 13, 14, 15, 16, 23, 24, 25, 26, 27, 28]
      const displacement = joints.reduce((total, joint) => total + this.distance(previous.landmarks[joint], current.landmarks[joint]) / scale, 0) / joints.length
      if (displacement >= 0.18) fast.push({ start: previous.timestamp / 1000, end: current.timestamp / 1000 })
    }
    return fast
  }

  private buildAdaptiveTimes(baseTimes: number[], fastIntervals: Array<{ start: number; end: number }>) {
    const times = new Set(baseTimes.map((time) => time.toFixed(4)))
    for (const interval of fastIntervals) for (let time = interval.start + 1 / VIDEO_RULES.fastMotionSampleFps; time < interval.end; time += 1 / VIDEO_RULES.fastMotionSampleFps) times.add(time.toFixed(4))
    return [...times].map(Number).sort((left, right) => left - right)
  }

  private distance(first: { x: number; y: number; z: number } | undefined, second: { x: number; y: number; z: number } | undefined) {
    return first && second ? Math.hypot(first.x - second.x, first.y - second.y, first.z - second.z) : 0
  }

  private async seekTo(video: HTMLVideoElement, time: number): Promise<void> {
    if (Math.abs(video.currentTime - time) < 0.005 && video.readyState >= HTMLMediaElement.HAVE_CURRENT_DATA) return
    await new Promise<void>((resolve, reject) => {
      const cleanup = () => { video.removeEventListener('seeked', finish); video.removeEventListener('error', fail) }
      const finish = () => { cleanup(); resolve() }
      const fail = () => { cleanup(); reject(new Error('视频采样时发生解码错误')) }
      video.addEventListener('seeked', finish, { once: true })
      video.addEventListener('error', fail, { once: true })
      video.currentTime = time
    })
  }
}
