<script setup lang="ts">
import { useRouter } from 'vue-router'
const router = useRouter()
</script>

<template>
  <div class="placeholder-page">
    <h1>🔍 搜索</h1>
    <p>搜索功能开发中…</p>
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
.placeholder-page h1 { color: var(--gold); }
</style>