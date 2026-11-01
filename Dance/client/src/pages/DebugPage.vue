<script setup lang="ts">
import { computed } from 'vue'
import { useTeachingStore } from '@/stores/teaching'

const store = useTeachingStore()
const checks = computed(() => [
  { name: 'WebGL 3D 示范', ok: Boolean(document.createElement('canvas').getContext('webgl')), detail: '用于 Three.js 3D 角色预览。' },
  { name: '摄像头 API', ok: Boolean(navigator.mediaDevices?.getUserMedia), detail: '需要 HTTPS 或 localhost，并在首次使用时授予权限。' },
  { name: '浏览器语音', ok: 'speechSynthesis' in window, detail: '仅用于可选本地语音纠错。' },
  { name: '本地存储', ok: (() => { try { localStorage.getItem('dance-fitness.course-progress'); return true } catch { return false } })(), detail: '用于课程解锁、通关记录和报告。' },
  { name: '课程草稿', ok: Boolean(store.generatedCourse), detail: store.generatedCourse ? `已生成 ${store.generatedCourse.stepCount} 个步骤。` : '请先在“分析”中导入视频并生成课程。' },
  { name: '标准视频与 Pose', ok: Boolean(store.sourceVideo && store.processedPoseSequence), detail: store.sourceVideo && store.processedPoseSequence ? '可进行标准视频回放、3D 重定向与实时评分。' : '刷新后需要重新导入原始视频，才能回放或评分。' },
])
</script>

<template><section class="page"><h1>运行自检</h1><el-alert title="Day 20：此页只读取当前浏览器运行状态，不会启动摄像头、上传数据或修改训练记录。" type="info" :closable="false" /><el-descriptions class="summary" :column="3" border><el-descriptions-item label="已解锁关卡">{{ store.unlockedStepCount }}</el-descriptions-item><el-descriptions-item label="已通过关卡">{{ store.passedStepIds.length }}</el-descriptions-item><el-descriptions-item label="当前步骤">{{ store.generatedCourse ? `第 ${store.currentStep + 1} 关` : '无' }}</el-descriptions-item></el-descriptions><el-table :data="checks" border><el-table-column prop="name" label="检查项" width="160" /><el-table-column label="状态" width="100"><template #default="scope"><el-tag :type="scope.row.ok ? 'success' : 'warning'">{{ scope.row.ok ? '就绪' : '待处理' }}</el-tag></template></el-table-column><el-table-column prop="detail" label="说明" /></el-table></section></template>

<style scoped>.summary { margin: 16px 0; }</style>
