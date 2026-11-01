import { createRouter, createWebHistory } from 'vue-router'
import HomePage from '@/pages/HomePage.vue'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    { path: '/', component: HomePage },
    { path: '/analyze', component: () => import('@/pages/AnalyzePage.vue') },
    { path: '/course', component: () => import('@/pages/CoursePage.vue') },
    { path: '/training', component: () => import('@/pages/TrainingPage.vue') },
    { path: '/report', component: () => import('@/pages/ReportPage.vue') },
    { path: '/history', component: () => import('@/pages/HistoryPage.vue') },
    { path: '/debug', component: () => import('@/pages/DebugPage.vue') },
  ],
})
export default router
