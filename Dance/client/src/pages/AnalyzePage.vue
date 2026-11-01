<script setup lang="ts">
import { computed, onBeforeUnmount, ref } from 'vue'
import type { SubjectRegion } from '@/types/domain'
import { ElMessage } from 'element-plus'
import { VideoAnalyzer, VIDEO_RULES } from '@/modules/video-analysis/VideoAnalyzer'
import { PoseExtractor } from '@/modules/pose/PoseExtractor'
import { PosePreprocessor } from '@/modules/pose/PosePreprocessor'
import { PersonTracker } from '@/modules/tracking/PersonTracker'
import { MotionAnalyzer } from '@/modules/video-analysis/MotionAnalyzer'
import { StepSegmenter } from '@/modules/video-analysis/StepSegmenter'
import { CourseBuilder } from '@/modules/teaching/CourseBuilder'
import { WebCourseProgressRepository } from '@/repositories/WebCourseProgressRepository'
import { webPlatform } from '@/platform/web'
import { useTeachingStore } from '@/stores/teaching'

const store = useTeachingStore()
const analyzer = new VideoAnalyzer()
const extractor = new PoseExtractor()
const preprocessor = new PosePreprocessor()
const personTracker = new PersonTracker()
const motionAnalyzer = new MotionAnalyzer()
const stepSegmenter = new StepSegmenter()
const courseBuilder = new CourseBuilder()
const courseProgressRepository = new WebCourseProgressRepository(webPlatform.storage)
const video = ref<HTMLVideoElement>()
const manualRegion = ref<SubjectRegion | null>(null)
const selectionStart = ref<{ x: number; y: number } | null>(null)
const loading = ref(false)
const poseResult = ref<{ landmarkCount: number; confidence: number } | null>(null)
const validationMessage = computed(() => store.videoMetadata ? `已读取：${store.videoMetadata.width}×${store.videoMetadata.height}，${store.videoMetadata.duration.toFixed(1)} 秒` : '请选择一段 MP4 动作视频。')
const progressPercent = computed(() => Math.round(store.analysisProgress * 100))

async function chooseVideo() {
  try {
    store.analysisStatus = 'validating'
    const previous = store.sourceVideo
    const source = await webPlatform.file.selectVideo()
    if (!source) { store.analysisStatus = 'idle'; return }
    const metadata = await analyzer.readMetadata(source)
    const error = analyzer.validate(source, metadata)
    if (error) { webPlatform.file.release(source); store.analysisStatus = 'failed'; ElMessage.error(error); return }
    if (previous) webPlatform.file.release(previous)
    store.sourceVideo = source; store.videoMetadata = metadata; store.analysisStatus = 'ready'; store.poseSequence = null; store.processedPoseSequence = null; store.poseAnalysisSummary = null; store.posePreprocessingReport = null; store.motionAnalysis = null; store.stepCandidates = []; store.generatedCourse = null; store.analysisProgress = 0; poseResult.value = null
    if (metadata.duration < VIDEO_RULES.recommendedMinDurationSeconds) ElMessage.warning('视频较短，建议使用 10–60 秒、单人全身入镜的视频。')
  } catch (error) { store.analysisStatus = 'failed'; ElMessage.error(error instanceof Error ? error.message : '视频读取失败') }
}

async function analyzeFullVideo() {
  if (!video.value || !store.sourceVideo) return
  loading.value = true; store.analysisStatus = 'analyzing'; store.analysisProgress = 0; store.poseSequence = null; store.processedPoseSequence = null; store.poseAnalysisSummary = null; store.posePreprocessingReport = null; store.motionAnalysis = null; store.stepCandidates = []; store.generatedCourse = null
  try {
    await extractor.initialize()
    personTracker.setManualTarget(manualRegion.value)
    const result = await analyzer.extractPoseSequence(video.value, extractor, personTracker, (completed, total) => { store.analysisProgress = completed / total })
    store.poseSequence = result.sequence; store.poseAnalysisSummary = result.summary; store.analysisStatus = 'ready'
    ElMessage.success(`分析完成：${result.summary.detectedFrames}/${result.summary.adaptiveSampledFrames} 帧检测到人体，快动作区已加密采样。`)
  } catch (error) { store.analysisStatus = 'failed'; ElMessage.error(error instanceof Error ? error.message : '视频姿态分析失败') }
  finally { loading.value = false }
}

function point(event: PointerEvent) {
  const bounds = video.value!.getBoundingClientRect()
  return { x: Math.max(0, Math.min(1, (event.clientX - bounds.left) / bounds.width)), y: Math.max(0, Math.min(1, (event.clientY - bounds.top) / bounds.height)) }
}
function beginSelection(event: PointerEvent) { if (!video.value) return; selectionStart.value = point(event); manualRegion.value = null }
function updateSelection(event: PointerEvent) { if (!selectionStart.value) return; const end = point(event); manualRegion.value = { x: Math.min(selectionStart.value.x, end.x), y: Math.min(selectionStart.value.y, end.y), width: Math.abs(end.x - selectionStart.value.x), height: Math.abs(end.y - selectionStart.value.y) } }
function finishSelection() { selectionStart.value = null; if (manualRegion.value && (manualRegion.value.width < 0.03 || manualRegion.value.height < 0.03)) manualRegion.value = null; store.manualSubjectRegion = manualRegion.value }

function preprocessPoseSequence() {
  if (!store.poseSequence) return
  const result = preprocessor.process(store.poseSequence)
  store.processedPoseSequence = result.sequence; store.posePreprocessingReport = result.report
  store.motionAnalysis = null; store.stepCandidates = []; store.generatedCourse = null
  ElMessage.success(`预处理完成：保留 ${result.report.acceptedFrames}/${result.report.inputFrames} 帧。`)
}

function analyzeMotionAndSteps() {
  if (!store.processedPoseSequence) return
  store.motionAnalysis = motionAnalyzer.analyze(store.processedPoseSequence)
  store.stepCandidates = stepSegmenter.segment(store.motionAnalysis, store.processedPoseSequence.duration)
  ElMessage.success(`动作分析完成：生成 ${store.stepCandidates.length} 个候选教学步骤。`)
}

function buildCourseDraft() {
  if (!store.sourceVideo || !store.processedPoseSequence || !store.stepCandidates.length) return
  store.generatedCourse = courseBuilder.build(store.sourceVideo, store.processedPoseSequence, store.stepCandidates)
  store.currentStep = 0
  store.unlockedStepCount = 1
  store.passedStepIds = []
  void courseProgressRepository.save({ course: store.generatedCourse, unlockedStepCount: store.unlockedStepCount, passedStepIds: store.passedStepIds })
  ElMessage.success('教学课程草稿已生成，可前往“课程”查看。')
}

async function verifyPose() {
  if (!video.value || !store.sourceVideo) return
  loading.value = true; store.analysisStatus = 'analyzing'
  try {
    await extractor.initialize()
    const frame = extractor.detectVideo(video.value, performance.now())
    poseResult.value = frame ? { landmarkCount: frame.landmarks.length, confidence: frame.confidence } : null
    store.analysisStatus = 'ready'
    ElMessage.success(frame ? 'Pose Landmarker 已在当前视频帧检测到人体。' : '当前帧未检测到人体，请移动到人物完整出现的位置。')
  } catch (error) { store.analysisStatus = 'failed'; ElMessage.error(error instanceof Error ? error.message : 'Pose 初始化失败') }
  finally { loading.value = false }
}

onBeforeUnmount(() => extractor.close())
</script>

<template>
  <section class="page">
    <h1>MP4 姿态分析验证</h1>
    <el-alert title="快动作会先由 10 FPS 粗采样识别，再在高位移区以 30 FPS 加密提取 Pose，用于更精细的动作切分与 3D 重定向。" type="info" :closable="false" />
    <el-card class="analysis-card" shadow="never">
      <el-button type="primary" :loading="loading" @click="chooseVideo">选择 MP4 视频</el-button>
      <p>{{ validationMessage }}</p>
      <p class="hint">限制：MP4、单人、全身尽量完整、时长不超过 60 秒、文件不超过 200 MB；后续将以 {{ VIDEO_RULES.sampleFps }} FPS 做完整采样。</p>
      <div v-if="store.sourceVideo" class="selection-stage"><video ref="video" :src="store.sourceVideo.url" controls preload="metadata" class="video-preview" @pointerdown.prevent="beginSelection" @pointermove.prevent="updateSelection" @pointerup.prevent="finishSelection" @pointercancel="finishSelection" /><div v-if="manualRegion" class="subject-box" :style="{ left: `${manualRegion.x * 100}%`, top: `${manualRegion.y * 100}%`, width: `${manualRegion.width * 100}%`, height: `${manualRegion.height * 100}%` }" /></div>
      <p v-if="store.sourceVideo" class="hint">可在视频画面上拖拽框选主人物；分析时优先锁定框中的人物。未框选时，系统按置信度自动选择。</p>
      <div v-if="store.sourceVideo" class="actions"><el-button :disabled="loading" @click="verifyPose">验证当前帧 Pose</el-button><el-button type="success" :loading="loading" @click="analyzeFullVideo">分析整段视频</el-button><span v-if="poseResult">检测到 {{ poseResult.landmarkCount }} 个关键点，平均可见度 {{ (poseResult.confidence * 100).toFixed(0) }}%</span></div>
      <el-progress v-if="loading" :percentage="progressPercent" :stroke-width="12" class="progress" />
      <el-descriptions v-if="store.poseAnalysisSummary" title="PoseSequence 结果" :column="3" border class="result">
        <el-descriptions-item label="采样帧数">{{ store.poseAnalysisSummary.sampledFrames }}</el-descriptions-item>
        <el-descriptions-item label="加密后采样帧">{{ store.poseAnalysisSummary.adaptiveSampledFrames }}</el-descriptions-item>
        <el-descriptions-item label="快动作区间">{{ store.poseAnalysisSummary.fastMotionIntervals }}</el-descriptions-item>
        <el-descriptions-item label="有效 Pose 帧">{{ store.poseAnalysisSummary.detectedFrames }}</el-descriptions-item>
        <el-descriptions-item label="平均可见度">{{ (store.poseAnalysisSummary.averageConfidence * 100).toFixed(1) }}%</el-descriptions-item>
        <el-descriptions-item label="拒绝错误候选">{{ store.poseAnalysisSummary.rejectedCandidates }}</el-descriptions-item>
        <el-descriptions-item label="短时保持">{{ store.poseAnalysisSummary.heldFrames }}</el-descriptions-item>
      </el-descriptions>
      <div v-if="store.poseSequence" class="actions"><el-button type="warning" @click="preprocessPoseSequence">预处理 PoseSequence</el-button><span>原始序列保持不变，处理后的序列将用于后续分析。</span></div>
      <el-descriptions v-if="store.posePreprocessingReport" title="预处理结果" :column="3" border class="result">
        <el-descriptions-item label="输入 / 保留帧">{{ store.posePreprocessingReport.inputFrames }} / {{ store.posePreprocessingReport.acceptedFrames }}</el-descriptions-item>
        <el-descriptions-item label="剔除低置信度帧">{{ store.posePreprocessingReport.rejectedFrames }}</el-descriptions-item>
        <el-descriptions-item label="抑制异常关键点">{{ store.posePreprocessingReport.outlierLandmarks }}</el-descriptions-item>
      </el-descriptions>
      <div v-if="store.processedPoseSequence" class="actions"><el-button type="primary" @click="analyzeMotionAndSteps">分析动作能量与自动分段</el-button><span>仅用算法生成时间候选，后续才由 LLM 做动作语义命名。</span></div>
      <el-descriptions v-if="store.motionAnalysis" title="动作能量" :column="3" border class="result">
        <el-descriptions-item label="能量采样数">{{ store.motionAnalysis.samples.length }}</el-descriptions-item>
        <el-descriptions-item label="平均能量">{{ store.motionAnalysis.averageEnergy.toFixed(3) }}</el-descriptions-item>
        <el-descriptions-item label="峰值能量">{{ store.motionAnalysis.peakEnergy.toFixed(3) }}</el-descriptions-item>
      </el-descriptions>
      <el-table v-if="store.stepCandidates.length" :data="store.stepCandidates" class="result" size="small"><el-table-column prop="index" label="步骤" width="70" /><el-table-column label="时间范围"><template #default="scope">{{ scope.row.startTime.toFixed(1) }}s – {{ scope.row.endTime.toFixed(1) }}s</template></el-table-column><el-table-column label="代表关键帧"><template #default="scope">{{ scope.row.keyframeTime.toFixed(1) }}s</template></el-table-column><el-table-column label="峰值能量"><template #default="scope">{{ scope.row.peakEnergy.toFixed(3) }}</template></el-table-column></el-table>
      <div v-if="store.stepCandidates.length" class="actions"><el-button type="success" @click="buildCourseDraft">生成教学课程草稿</el-button><span>重点关节和提示由 Pose 运动量确定；后续 LLM 只做语义润色。</span></div>
    </el-card>
  </section>
</template>

<style scoped>
.analysis-card { margin-top: 16px; }.hint { color: #6b7280; font-size: 13px; }.selection-stage { position: relative; width: min(100%, 640px); }.video-preview { display: block; width: 100%; max-height: 420px; background: #111827; }.subject-box { position: absolute; border: 3px solid #22c55e; background: rgba(34, 197, 94, .12); pointer-events: none; }.actions { display: flex; align-items: center; gap: 12px; margin-top: 14px; }.progress, .result { margin-top: 18px; }
</style>
