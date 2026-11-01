<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import type { TrainingHistory } from '@/types/domain'
import { webPlatform } from '@/platform/web'
import { WebTrainingHistoryRepository } from '@/repositories/WebTrainingHistoryRepository'
import { PracticeRecommendationEngine } from '@/modules/coaching/PracticeRecommendation'

const records = ref<TrainingHistory[]>([])
const averageScore = computed(() => records.value.length ? Math.round(records.value.reduce((total, record) => total + record.score, 0) / records.value.length) : 0)
const latest = computed(() => records.value[0] ?? null)
const passedSteps = computed(() => new Set(records.value.map((record) => record.stepId)).size)
const recommendation = computed(() => new PracticeRecommendationEngine().recommend(records.value))
onMounted(async () => { records.value = await new WebTrainingHistoryRepository(webPlatform.storage).list() })
</script>

<template>
  <section class="page"><h1>训练报告</h1>
    <el-empty v-if="!records.length" description="还没有可生成的训练报告。完成一个步骤后再回来查看。" />
    <template v-else><el-alert title="报告基于本浏览器中已通过的动作步骤记录生成，不包含摄像头视频或身份信息。" type="info" :closable="false" /><div class="cards"><el-card shadow="never"><el-statistic title="已通过关卡" :value="passedSteps" /></el-card><el-card shadow="never"><el-statistic title="平均通过分" :value="averageScore" suffix=" / 100" /></el-card><el-card shadow="never"><el-statistic title="记录次数" :value="records.length" /></el-card></div><el-alert class="recommendation" :title="recommendation.title" :description="recommendation.detail" :type="recommendation.kind === 'review' ? 'warning' : 'success'" :closable="false" /><el-card v-if="latest" shadow="never" class="latest"><h2>最近一次通过</h2><p>第 {{ latest.stepIndex }} 关 · {{ latest.score }} 分 · 动作进度 {{ (latest.progress * 100).toFixed(0) }}%</p><p>完成时间：{{ new Date(latest.completedAt).toLocaleString() }}</p></el-card></template>
  </section>
</template>

<style scoped>.cards { display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 16px; margin-top: 16px; }.recommendation, .latest { margin-top: 16px; }.latest h2 { margin-top: 0; } @media (max-width: 700px) { .cards { grid-template-columns: 1fr; } }</style>
