<script setup lang="ts">
import { useRoute, useRouter } from 'vue-router'
const route = useRoute()
const router = useRouter()
const videoId = route.params.videoId as string
</script>

<template>
  <div class="placeholder-page">
    <h1>💬 评论</h1>
    <p>视频 {{ videoId }} 的评论页面开发中…</p>
    <button class="btn btn-outline" @click="router.back()">返回</button>
  </div>
</template>

<style scoped>
.placeholder-page {
  max-width: 640px;
  margin: 0 auto;
  padding: 3rem 1.25rem;
  text-align: center;
  color: var(--text);
}
</style>