<script setup lang="ts">
defineProps<{ title: string; description: string }>()
</script>

<template>
  <section class="page"><h1>{{ title }}</h1><el-card shadow="never"><p>{{ description }}</p><el-tag type="info">Phase 0：页面与路由已就绪，业务功能尚未启用。</el-tag></el-card></section>
</template>
