<script setup lang="ts">
import { RouterLink, RouterView } from 'vue-router'
</script>

<template>
  <el-container class="app-shell">
    <el-header class="header"><RouterLink to="/">AI 舞蹈健身教学</RouterLink><span>Phase 0 · 基础工程</span></el-header>
    <el-container>
      <el-aside width="180px"><el-menu router default-active="/"><el-menu-item index="/">首页</el-menu-item><el-menu-item index="/analyze">视频分析</el-menu-item><el-menu-item index="/course">课程</el-menu-item><el-menu-item index="/training">训练</el-menu-item><el-menu-item index="/report">报告</el-menu-item><el-menu-item index="/history">历史</el-menu-item><el-menu-item index="/debug">调试</el-menu-item></el-menu></el-aside>
      <el-main><RouterView /></el-main>
    </el-container>
  </el-container>
</template>
