<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { ElMessage } from 'element-plus'
import { useTeachingStore } from '@/stores/teaching'
import AvatarPreview from '@/components/teaching/AvatarPreview.vue'
import { webPlatform } from '@/platform/web'
import { WebCourseProgressRepository } from '@/repositories/WebCourseProgressRepository'

const store = useTeachingStore()
const formatTime = (seconds: number) => `${seconds.toFixed(1)}s`
const player = ref<HTMLVideoElement>()
const playingStep = ref(false)
const slowMotionDialogVisible = ref(false)
const activeStep = computed(() => store.generatedCourse?.steps[store.currentStep] ?? null)
onMounted(async () => {
  if (store.generatedCourse) return
  const saved = await new WebCourseProgressRepository(webPlatform.storage).load()
  if (!saved) return
  store.generatedCourse = saved.course
  store.unlockedStepCount = saved.unlockedStepCount
  store.passedStepIds = saved.passedStepIds
})

function selectStep(index: number, autoplay = false) {
  if (index >= store.unlockedStepCount) return
  const step = store.generatedCourse?.steps[index]
  const video = player.value
  if (!step || !video) return
  store.currentStep = index
  playingStep.value = false
  video.currentTime = step.startTime
  video.playbackRate = 1
  if (autoplay) playActiveStep()
}

function playActiveStep() {
  if (!activeStep.value || !player.value) return
  if ((activeStep.value.recommendedPlaybackRate ?? 1) < 1) { slowMotionDialogVisible.value = true; return }
  startPlayback(1)
}

function startPlayback(rate: number) {
  if (!activeStep.value || !player.value) return
  player.value.currentTime = activeStep.value.startTime
  player.value.playbackRate = rate
  playingStep.value = true
  slowMotionDialogVisible.value = false
  void player.value.play()
}

function handleTimeUpdate() {
  const video = player.value
  const step = activeStep.value
  if (!video || !step || !playingStep.value) return
  if (video.currentTime >= step.endTime) {
    video.pause()
    video.currentTime = step.endTime
    playingStep.value = false
  }
}

function handlePlaybackError() {
  ElMessage.error('当前标准动作视频无法播放，请返回“分析”重新选择视频。')
}
</script>

<template>
  <section class="page">
    <h1>教学课程</h1>
    <el-empty v-if="!store.generatedCourse" description="尚未生成课程草稿，请先在“分析”完成视频分段。">
      <RouterLink to="/analyze"><el-button type="primary">前往视频分析</el-button></RouterLink>
    </el-empty>
    <template v-else>
      <el-alert title="这是由本地姿态与时间分段生成的课程草稿。动作名称与自然语言讲解将在后续接入 LLM 后增强，不会改变已测得的时间范围和关键帧。" type="info" :closable="false" />
      <el-card shadow="never" class="course-card"><h2>{{ store.generatedCourse.title }}</h2><p>来源：{{ store.generatedCourse.sourceVideoName }} · {{ store.generatedCourse.stepCount }} 个教学步骤</p></el-card>
      <el-card shadow="never" class="mode-card"><h2>选择教学方式</h2><el-radio-group v-model="store.demonstrationMode"><el-radio-button value="video">原视频教学</el-radio-button><el-radio-button value="avatar">3D 人物模型教学</el-radio-button></el-radio-group><p class="hint">训练页会将所选示范放在左侧，摄像头画面放在右侧。未来导入正式 3D 骨架模型后，会自动替换当前的简易角色。</p></el-card>
      <el-card v-if="store.sourceVideo && activeStep" shadow="never" class="player-card">
        <h2>标准动作分步回放</h2>
        <video ref="player" :src="store.sourceVideo.url" class="video-player" controls preload="metadata" @timeupdate="handleTimeUpdate" @error="handlePlaybackError" />
        <div class="player-controls"><el-button type="primary" @click="playActiveStep">播放第 {{ activeStep.index }} 步片段</el-button><span>片段：{{ formatTime(activeStep.startTime) }} – {{ formatTime(activeStep.endTime) }}；推荐 {{ activeStep.recommendedPlaybackRate ?? 1 }}× 播放，结束后自动暂停。</span></div>
      </el-card>
      <el-dialog v-model="slowMotionDialogVisible" title="检测到快动作" width="min(92vw, 420px)"><p>这一关的动作峰值高于本视频的常规水平。你可以选择慢放观察，也可以正常播放。</p><template #footer><el-button @click="startPlayback(1)">正常 1×</el-button><el-button v-if="activeStep?.recommendedPlaybackRate === 0.5" @click="startPlayback(0.75)">0.75×</el-button><el-button type="primary" @click="startPlayback(activeStep?.recommendedPlaybackRate ?? 1)">建议 {{ activeStep?.recommendedPlaybackRate }}×</el-button></template></el-dialog>
      <el-alert v-if="!store.sourceVideo && activeStep" title="已恢复课程与解锁进度。原始视频和标准 Pose 序列不会被浏览器长期保存；如需播放标准视频或进行实时评分，请在“分析”重新导入该视频。" type="warning" :closable="false" />
      <el-card v-if="activeStep" shadow="never" class="avatar-card">
        <div class="avatar-heading"><div><h2>3D 动作示范预览</h2><p>角色由当前步骤内的处理后标准 Pose 序列驱动；它是轻量骨架映射，后续可替换为完整人体绑定。</p></div><el-tag type="success">Pose 重定向已接入</el-tag></div>
        <AvatarPreview :step="activeStep" :playing="playingStep" :reference-sequence="store.processedPoseSequence" />
      </el-card>
      <el-timeline class="steps">
        <el-timeline-item v-for="step in store.generatedCourse.steps" :key="step.id" :timestamp="`${formatTime(step.startTime)} – ${formatTime(step.endTime)}`" placement="top">
          <el-card shadow="never" :class="{ active: store.currentStep === step.index - 1 }"><div class="step-heading"><h3>{{ step.title }} <el-tag v-if="store.passedStepIds.includes(step.id)" type="success" size="small">已通过</el-tag><el-tag v-else-if="step.index > store.unlockedStepCount" type="info" size="small">未解锁</el-tag></h3><el-button size="small" :type="store.currentStep === step.index - 1 ? 'primary' : 'default'" :disabled="step.index > store.unlockedStepCount" @click="selectStep(step.index - 1)">查看此片段</el-button></div><p>动作片段：{{ formatTime(step.startTime) }} – {{ formatTime(step.endTime) }} · 推荐 {{ step.recommendedPlaybackRate ?? 1 }}×</p><p>代表关键帧：{{ formatTime(step.keyframeTime) }}</p><p>重点关节：{{ step.importantJoints.length ? step.importantJoints.join('、') : '全身节奏与重心' }}</p><p class="hint">{{ step.teachingHint }}</p></el-card>
        </el-timeline-item>
      </el-timeline>
    </template>
  </section>
</template>

<style scoped>
.course-card, .player-card, .avatar-card, .steps { margin-top: 16px; }.course-card h2, h3 { margin-top: 0; }.video-player { display: block; width: min(100%, 720px); max-height: 430px; background: #111827; }.player-controls, .step-heading, .avatar-heading { display: flex; align-items: center; gap: 12px; margin-top: 12px; }.avatar-heading { justify-content: space-between; margin-top: 0; }.avatar-heading p { color: #4b5563; margin-bottom: 0; }.step-heading { justify-content: space-between; margin-top: 0; }.active { border-color: var(--el-color-primary); }.hint { color: #4b5563; }
</style>
