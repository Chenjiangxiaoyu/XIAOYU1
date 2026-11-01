<script setup lang="ts">
import { computed } from 'vue'
import { useTeachingStore } from '@/stores/teaching'
const store = useTeachingStore()
const courseStatus = computed(() => store.generatedCourse ? `${store.generatedCourse.stepCount} 关，已解锁 ${store.unlockedStepCount} 关` : '尚未生成课程')
</script>
<template><section class="page"><h1>AI 3D 舞蹈健身自适应教学系统</h1><el-alert title="Day 21：本地端到端教学流程已集成。视频、Pose 与摄像头画面优先在浏览器处理，不上传训练视频。" type="success" :closable="false" /><div class="overview"><el-card shadow="never"><h2>当前课程</h2><p>{{ courseStatus }}</p><p>已通过 {{ store.passedStepIds.length }} 关</p><RouterLink to="/analyze"><el-button type="primary">导入并分析视频</el-button></RouterLink></el-card><el-card shadow="never"><h2>完整流程</h2><ol><li>导入 MP4，提取与预处理 Pose。</li><li>自动分段并生成教学课程。</li><li>使用 3D 示范和标准视频学习动作。</li><li>打开摄像头，进行实时匹配、评分与纠错。</li><li>通关、解锁并查看本地训练报告。</li></ol></el-card></div><el-card shadow="never" class="next"><h2>整体测试入口</h2><p>先到“运行自检”确认浏览器能力；再按“分析 → 课程 → 训练 → 报告”的顺序进行完整手动测试。</p><RouterLink to="/debug"><el-button>打开运行自检</el-button></RouterLink></el-card></section></template>
<style scoped>.overview { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 16px; margin-top: 16px; }.overview h2, .next h2 { margin-top: 0; }.overview ol { margin-bottom: 0; padding-left: 22px; line-height: 1.9; }.next { margin-top: 16px; } @media (max-width: 700px) { .overview { grid-template-columns: 1fr; } }</style>
