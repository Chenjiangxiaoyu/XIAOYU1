<script setup lang="ts">
import { computed, nextTick, onBeforeUnmount, ref, watch } from 'vue'
import { ElMessage } from 'element-plus'
import { PoseExtractor } from '@/modules/pose/PoseExtractor'
import { PersonTracker } from '@/modules/tracking/PersonTracker'
import { MotionScorer, type MotionScore } from '@/modules/scoring/MotionScorer'
import { StepProgressMatcher } from '@/modules/scoring/StepProgressMatcher'
import { WebTrainingHistoryRepository } from '@/repositories/WebTrainingHistoryRepository'
import { WebCourseProgressRepository } from '@/repositories/WebCourseProgressRepository'
import AvatarPreview from '@/components/teaching/AvatarPreview.vue'
import { webPlatform } from '@/platform/web'
import { useTeachingStore } from '@/stores/teaching'

const store = useTeachingStore()
const extractor = new PoseExtractor()
const personTracker = new PersonTracker()
const motionScorer = new MotionScorer()
const stepMatcher = new StepProgressMatcher()
const historyRepository = new WebTrainingHistoryRepository(webPlatform.storage)
const courseProgressRepository = new WebCourseProgressRepository(webPlatform.storage)
const video = ref<HTMLVideoElement>()
const referenceVideo = ref<HTMLVideoElement>()
const canvas = ref<HTMLCanvasElement>()
const stream = ref<MediaStream | null>(null)
const isRunning = ref(false)
const isStarting = ref(false)
const status = ref('摄像头尚未启动。')
const fps = ref(0)
const confidence = ref(0)
const motionScore = ref<MotionScore | null>(null)
const stepProgress = ref(0)
const stableMilliseconds = ref(0)
const passedThisSession = ref(false)
const isPracticing = ref(false)
const activeStep = computed(() => store.generatedCourse?.steps[store.currentStep] ?? null)
const cropStyle = computed(() => {
  const region = store.manualSubjectRegion
  if (!region) return {}
  return { width: `${100 / region.width}%`, maxWidth: 'none', transform: `translate(${-region.x / region.width * 100}%, ${-region.y / region.height * 100}%)`, transformOrigin: 'top left' }
})
watch(() => activeStep.value?.id, () => { stepMatcher.reset(); motionScore.value = null; stepProgress.value = 0; stableMilliseconds.value = 0; passedThisSession.value = false; isPracticing.value = false; stopReferenceDemo() })
let animationId: number | null = null
let previousTimestamp = 0
let fpsWindowStart = 0
let fpsFrames = 0
let stableSince = 0

const CONNECTIONS: Array<[number, number]> = [[11, 12], [11, 13], [13, 15], [12, 14], [14, 16], [11, 23], [12, 24], [23, 24], [23, 25], [25, 27], [24, 26], [26, 28], [0, 11], [0, 12]]

async function startCamera() {
  if (isRunning.value || isStarting.value) return
  isStarting.value = true; status.value = '正在请求摄像头与加载姿态模型…'
  try {
    stream.value = await webPlatform.camera.open()
    await nextTick()
    if (!video.value) throw new Error('摄像头预览初始化失败')
    video.value.srcObject = stream.value
    await new Promise<void>((resolve) => { video.value!.onloadeddata = () => resolve() })
    resizeCanvas()
    await extractor.initialize()
    isRunning.value = true; store.trainingStatus = 'training'; status.value = '实时 Pose 检测中。'
    previousTimestamp = 0; fpsWindowStart = performance.now(); fpsFrames = 0
    detectLoop(performance.now())
  } catch (error) {
    stopCamera()
    store.trainingStatus = 'failed'; status.value = '无法启动摄像头。'
    ElMessage.error(error instanceof Error ? error.message : '摄像头或 Pose 模型启动失败')
  } finally { isStarting.value = false }
}

function detectLoop(timestamp: number) {
  if (!isRunning.value || !video.value) return
  if (timestamp - previousTimestamp >= 50 && video.value.readyState >= HTMLMediaElement.HAVE_CURRENT_DATA) {
    previousTimestamp = timestamp
    const selection = personTracker.select(extractor.detectVideoCandidates(video.value, timestamp))
    const frame = selection.frame
    store.cameraPoseFrame = frame
    if (isPracticing.value && frame && activeStep.value && store.processedPoseSequence) {
      const match = stepMatcher.match(frame, store.processedPoseSequence, activeStep.value)
      const rawScore = match ? motionScorer.scoreAgainstFrame(frame, match.referenceFrame) : null
      stepProgress.value = match?.progress ?? 0
      if (rawScore) {
        const previous = motionScore.value?.overall
        motionScore.value = { ...rawScore, overall: Math.round(previous === undefined ? rawScore.overall : previous * 0.7 + rawScore.overall * 0.3) }
        evaluateCompletion(timestamp)
      }
    } else { motionScore.value = null; stepProgress.value = 0 }
    confidence.value = frame?.confidence ?? 0
    status.value = selection.state === 'REJECTED' ? '已拒绝偏离当前练习者的候选人体。' : selection.state === 'HOLD' ? '暂时未确认练习者，保持身份状态。' : '实时 Pose 检测中。'
    drawPose(frame?.landmarks ?? [])
    fpsFrames += 1
    if (timestamp - fpsWindowStart >= 1000) { fps.value = Math.round((fpsFrames * 1000) / (timestamp - fpsWindowStart)); fpsFrames = 0; fpsWindowStart = timestamp }
  }
  animationId = requestAnimationFrame(detectLoop)
}

function prepareReferenceDemo() {
  if (!referenceVideo.value || !activeStep.value) return
  referenceVideo.value.pause()
  referenceVideo.value.currentTime = activeStep.value.startTime
  referenceVideo.value.playbackRate = 1
}

function playReferenceDemo() {
  if (!referenceVideo.value || !activeStep.value) return
  prepareReferenceDemo()
  void referenceVideo.value.play()
}

function handleReferenceTimeUpdate() {
  if (!referenceVideo.value || !activeStep.value) return
  if (referenceVideo.value.currentTime >= activeStep.value.endTime) {
    referenceVideo.value.pause()
    referenceVideo.value.currentTime = activeStep.value.endTime
  }
}

function stopReferenceDemo() { referenceVideo.value?.pause() }

function beginPractice() {
  if (!isRunning.value) { ElMessage.warning('请先启动摄像头，再开始本关练习。'); return }
  stopReferenceDemo()
  stepMatcher.reset(); motionScore.value = null; stepProgress.value = 0; stableMilliseconds.value = 0; stableSince = 0
  isPracticing.value = true
  status.value = `正在练习第 ${activeStep.value?.index ?? ''} 关。`
}

function pausePractice() { isPracticing.value = false; status.value = '本关练习已暂停，可先观看左侧示范。' }

function evaluateCompletion(timestamp: number) {
  if (!activeStep.value || !store.generatedCourse || !motionScore.value || passedThisSession.value) return
  if (stepProgress.value < 0.9 || motionScore.value.overall < 75) { stableSince = 0; stableMilliseconds.value = 0; return }
  if (!stableSince) stableSince = timestamp
  stableMilliseconds.value = Math.round(timestamp - stableSince)
  if (stableMilliseconds.value < 2000) return
  passedThisSession.value = true
  if (!store.passedStepIds.includes(activeStep.value.id)) store.passedStepIds.push(activeStep.value.id)
  store.unlockedStepCount = Math.min(store.generatedCourse.stepCount, Math.max(store.unlockedStepCount, activeStep.value.index + 1))
  void courseProgressRepository.save({ course: store.generatedCourse, unlockedStepCount: store.unlockedStepCount, passedStepIds: store.passedStepIds })
  void historyRepository.save({ id: `attempt-${Date.now()}`, courseId: store.generatedCourse.id, stepId: activeStep.value.id, stepIndex: activeStep.value.index, completedAt: new Date().toISOString(), score: motionScore.value.overall, progress: stepProgress.value, stableMilliseconds: stableMilliseconds.value })
  ElMessage.success(`第 ${activeStep.value.index} 步已通过，${activeStep.value.index < store.generatedCourse.stepCount ? '下一步已解锁。' : '课程全部步骤已解锁。'}`)
}

function resizeCanvas() {
  if (!video.value || !canvas.value) return
  canvas.value.width = video.value.videoWidth
  canvas.value.height = video.value.videoHeight
}

function drawPose(landmarks: Array<{ x: number; y: number; visibility?: number }>) {
  const context = canvas.value?.getContext('2d')
  if (!canvas.value || !context) return
  context.clearRect(0, 0, canvas.value.width, canvas.value.height)
  if (!landmarks.length) return
  context.strokeStyle = '#42d392'; context.lineWidth = Math.max(2, canvas.value.width / 400)
  for (const [from, to] of CONNECTIONS) {
    if (!landmarks[from] || !landmarks[to]) continue
    context.beginPath(); context.moveTo(landmarks[from].x * canvas.value.width, landmarks[from].y * canvas.value.height); context.lineTo(landmarks[to].x * canvas.value.width, landmarks[to].y * canvas.value.height); context.stroke()
  }
  context.fillStyle = '#ffd166'
  for (const point of landmarks) { if ((point.visibility ?? 1) < 0.35) continue; context.beginPath(); context.arc(point.x * canvas.value.width, point.y * canvas.value.height, Math.max(3, canvas.value.width / 220), 0, Math.PI * 2); context.fill() }
}

function stopCamera() {
  if (animationId !== null) cancelAnimationFrame(animationId)
  animationId = null; isRunning.value = false; isPracticing.value = false; stopReferenceDemo(); personTracker.reset(); stepMatcher.reset(); store.trainingStatus = 'idle'; store.cameraPoseFrame = null; confidence.value = 0; fps.value = 0; motionScore.value = null; stepProgress.value = 0; stableSince = 0; stableMilliseconds.value = 0
  if (stream.value) webPlatform.camera.close(stream.value)
  stream.value = null
  if (video.value) video.value.srcObject = null
  const context = canvas.value?.getContext('2d'); if (canvas.value && context) context.clearRect(0, 0, canvas.value.width, canvas.value.height)
  if (status.value !== '无法启动摄像头。') status.value = '摄像头已关闭。'
}

onBeforeUnmount(() => { stopCamera(); extractor.close() })
</script>

<template>
  <section class="page">
    <h1>实时动作练习</h1>
    <el-alert title="按关练习：先观看左侧“当前关”示范，再启动摄像头并点击“开始本关练习”。系统只对当前关评分，不会要求你跟完整段视频。" type="info" :closable="false" />
    <el-card class="training-card" shadow="never">
      <div class="actions"><el-button type="primary" :loading="isStarting" :disabled="isRunning" @click="startCamera">启动摄像头</el-button><el-button :disabled="!isRunning" @click="stopCamera">关闭摄像头</el-button><el-button type="success" :disabled="!isRunning || !activeStep || isPracticing" @click="beginPractice">开始本关练习</el-button><el-button :disabled="!isPracticing" @click="pausePractice">暂停练习</el-button><span>{{ status }}</span></div>
      <div v-show="stream" class="training-split"><div class="demo-stage"><h2>{{ activeStep ? `第 ${activeStep.index} 关标准示范` : '标准示范' }}</h2><div v-if="store.demonstrationMode === 'video' && store.sourceVideo" class="reference-crop"><video ref="referenceVideo" :src="store.sourceVideo.url" class="reference-video" :style="cropStyle" preload="metadata" @loadedmetadata="prepareReferenceDemo" @timeupdate="handleReferenceTimeUpdate" /></div><AvatarPreview v-else-if="activeStep" :step="activeStep" :playing="false" :reference-sequence="store.processedPoseSequence" /><el-empty v-else description="请先生成课程并选择步骤" /><el-button v-if="store.demonstrationMode === 'video' && activeStep" class="demo-button" @click="playReferenceDemo">观看第 {{ activeStep.index }} 关示范</el-button><p class="demo-hint">示范只播放当前关的时间片段，到该关结束自动暂停。</p></div><div class="camera-stage"><h2>我的摄像头</h2><video ref="video" autoplay playsinline muted class="camera-video" @loadedmetadata="resizeCanvas" /><canvas ref="canvas" class="pose-overlay" /></div></div>
      <el-descriptions v-if="isRunning" :column="3" border class="metrics"><el-descriptions-item label="检测 FPS">{{ fps }}</el-descriptions-item><el-descriptions-item label="平均可见度">{{ (confidence * 100).toFixed(1) }}%</el-descriptions-item><el-descriptions-item label="关键点状态">{{ store.cameraPoseFrame ? `${store.cameraPoseFrame.landmarks.length} 个` : '未检测到人物' }}</el-descriptions-item></el-descriptions>
      <el-alert v-if="isRunning && !activeStep" class="score-panel" title="请先在“分析”生成课程草稿，并在“课程”选择一个教学步骤，才能开始动作评分。" type="warning" :closable="false" />
      <template v-if="isRunning && motionScore && activeStep"><el-descriptions title="当前步骤动作评分" :column="4" border class="score-panel"><el-descriptions-item label="练习步骤">第 {{ activeStep.index }} 步</el-descriptions-item><el-descriptions-item label="总分"><el-tag :type="motionScore.overall >= 75 ? 'success' : 'warning'">{{ motionScore.overall }} / 100</el-tag></el-descriptions-item><el-descriptions-item label="动作进度"><el-tag :type="stepProgress >= 0.9 ? 'success' : 'info'">{{ (stepProgress * 100).toFixed(0) }}%</el-tag></el-descriptions-item><el-descriptions-item label="稳定通过">{{ (stableMilliseconds / 1000).toFixed(1) }} / 2.0 秒</el-descriptions-item></el-descriptions><el-progress class="progress" :percentage="Math.round(stepProgress * 100)" :status="stepProgress >= 90 ? 'success' : undefined" /><div class="joint-scores"><el-tag v-for="joint in motionScore.jointScores" :key="joint.joint" :type="joint.score >= 75 ? 'success' : 'warning'">{{ joint.joint }} {{ joint.score }}</el-tag></div><el-alert v-for="item in motionScore.feedback" :key="item" class="feedback" :title="item" :type="motionScore.overall >= 75 ? 'success' : 'warning'" :closable="false" /></template>
    </el-card>
  </section>
</template>

<style scoped>
.training-card { margin-top: 16px; }.actions, .joint-scores { display: flex; align-items: center; flex-wrap: wrap; gap: 12px; }.training-split { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 16px; margin-top: 18px; }.demo-stage, .camera-stage { position: relative; min-width: 0; background: #111827; overflow: hidden; color: white; }.demo-stage h2, .camera-stage h2 { font-size: 14px; margin: 10px; }.reference-crop { aspect-ratio: 3 / 4; overflow: hidden; }.reference-video, .camera-video, .pose-overlay { display: block; width: 100%; }.camera-video, .pose-overlay { transform: scaleX(-1); }.pose-overlay { position: absolute; inset: 34px 0 0; height: calc(100% - 34px); pointer-events: none; }.demo-button { margin: 12px 10px 0; }.demo-hint { color: #d1d5db; font-size: 12px; margin: 8px 10px 12px; }.metrics, .score-panel, .progress, .joint-scores, .feedback { margin-top: 18px; } @media (max-width: 760px) { .training-split { grid-template-columns: 1fr; } }
</style>
