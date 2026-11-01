import type { TrainingHistory } from '@/types/domain'

export interface PracticeRecommendation { title: string; detail: string; targetStepIndex: number | null; kind: 'next' | 'review' }
export class PracticeRecommendationEngine {
  recommend(records: TrainingHistory[]): PracticeRecommendation {
    if (!records.length) return { title: '从第一关开始练习', detail: '先完成第一关的标准动作与摄像头校准，系统才能积累本地练习记录。', targetStepIndex: 1, kind: 'next' }
    const lowest = [...records].sort((left, right) => left.score - right.score)[0]
    const latest = records[0]
    if (lowest.score < 82) return { title: `建议复练第 ${lowest.stepIndex} 关`, detail: `这是已通过记录中分数最低的一关（${lowest.score} 分）。复练时让分数稳定高于 82 分。`, targetStepIndex: lowest.stepIndex, kind: 'review' }
    return { title: `可以尝试第 ${latest.stepIndex + 1} 关`, detail: `最近一次第 ${latest.stepIndex} 关达到 ${latest.score} 分，动作稳定性良好。`, targetStepIndex: latest.stepIndex + 1, kind: 'next' }
  }
}
