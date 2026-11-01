<script setup lang="ts">
import { onMounted, ref } from 'vue'
import type { TrainingHistory } from '@/types/domain'
import { webPlatform } from '@/platform/web'
import { WebTrainingHistoryRepository } from '@/repositories/WebTrainingHistoryRepository'

const records = ref<TrainingHistory[]>([])
onMounted(async () => { records.value = await new WebTrainingHistoryRepository(webPlatform.storage).list() })
</script>

<template>
  <section class="page"><h1>训练历史</h1>
    <el-empty v-if="!records.length" description="尚无通过记录。完成一个教学步骤后，记录会保存在此浏览器中。" />
    <el-table v-else :data="records" border><el-table-column label="步骤" width="90"><template #default="scope">第 {{ scope.row.stepIndex }} 关</template></el-table-column><el-table-column prop="score" label="通过分数" width="110" /><el-table-column label="动作进度" width="120"><template #default="scope">{{ (scope.row.progress * 100).toFixed(0) }}%</template></el-table-column><el-table-column label="稳定时长" width="120"><template #default="scope">{{ (scope.row.stableMilliseconds / 1000).toFixed(1) }} 秒</template></el-table-column><el-table-column label="完成时间"><template #default="scope">{{ new Date(scope.row.completedAt).toLocaleString() }}</template></el-table-column></el-table>
  </section>
</template>
