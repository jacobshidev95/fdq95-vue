<script setup lang="ts">
import { useRoute, useRouter } from 'vue-router'
const route = useRoute()
const router = useRouter()
const videoId = route.params.videoId as string

function shareToWeChat() {
  const url = window.location.origin + `/videos/${videoId}`
  window.location.href = `weixin://dl/business/?u=${encodeURIComponent(url)}`
}
function shareToWhatsApp() {
  const url = encodeURIComponent(window.location.origin + `/videos/${videoId}`)
  window.open(`https://wa.me/?text=${url}`, '_blank')
}
</script>

<template>
  <div class="placeholder-page">
    <h1>分享视频</h1>
    <div class="share-row">
      <button class="btn btn-primary" @click="shareToWeChat">微信</button>
      <button class="btn btn-primary" @click="shareToWhatsApp">WhatsApp</button>
    </div>
    <button class="btn btn-outline" @click="router.back()">取消</button>
  </div>
</template>

<style scoped>
.placeholder-page {
  max-width: 420px;
  margin: 0 auto;
  padding: 3rem 1.25rem;
  text-align: center;
  color: var(--text);
}
.share-row { display: flex; gap: 0.75rem; justify-content: center; margin: 1.5rem 0; }
</style>