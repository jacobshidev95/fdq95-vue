<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { api } from '@/api/client'
import { useI18nStore } from '@/stores/i18n'

const route = useRoute()
const router = useRouter()
const i18n = useI18nStore()

const userId = computed(() => String(route.params.userId || ''))
const videos = ref<
  Array<{
    id: string
    title: string
    url: string
    thumbnail_url: string | null
    duration_sec: number
    views: number
    likes: number
    hearts: number
    created_at: string
  }>
>([])
const playing = ref<string | null>(null)

async function load() {
  const { data } = await api.get(`/api/videos/user/${userId.value}`)
  videos.value = data
}

onMounted(load)

function playVideo(v: { id: string }) {
  playing.value = playing.value === v.id ? null : v.id
}
</script>

<template>
  <div class="videos-page">
    <div class="top-bar">
      <button class="back-btn" @click="router.push(`/profile/${userId}`)">←</button>
      <span class="title">{{ i18n.t('video_list') }} — @{{ userId }}</span>
    </div>

    <div v-if="videos.length === 0" class="empty">
      {{ i18n.t('no_videos_yet') }}
    </div>

    <ul class="video-list">
      <li v-for="v in videos" :key="v.id" class="video-item">
        <div class="video-thumb" @click="playVideo(v)">
          <span class="play-tri">▶</span>
          <span class="duration">{{ v.duration_sec }}s</span>
        </div>
        <div class="video-meta">
          <div class="video-title">{{ v.title }}</div>
          <div class="video-stats">
            {{ v.views }} views · {{ v.likes }} 👍 · {{ v.hearts }} ❤️
          </div>
        </div>
      </li>
    </ul>
  </div>
</template>

<style scoped>
.videos-page {
  width: 100%;
  max-width: 720px;
  padding: 1rem 1.25rem 3rem;
}
.top-bar {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  margin-bottom: 1rem;
}
.back-btn {
  background: transparent;
  border: 1px solid var(--border);
  color: var(--text);
  border-radius: 6px;
  padding: 0.35rem 0.75rem;
  cursor: pointer;
}
.title {
  color: var(--gold);
  font-weight: 700;
}
.empty {
  color: var(--text-dim);
  text-align: center;
  margin-top: 3rem;
}
.video-list {
  list-style: none;
  padding: 0;
  margin: 0;
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
}
.video-item {
  display: flex;
  gap: 0.85rem;
  background: var(--bg-soft);
  border: 1px solid var(--border);
  border-radius: 8px;
  padding: 0.6rem;
}
.video-thumb {
  flex: 0 0 120px;
  height: 68px;
  background: linear-gradient(135deg, #444, #222);
  border-radius: 6px;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  position: relative;
}
.play-tri {
  color: rgba(255, 255, 255, 0.8);
  font-size: 1.5rem;
}
.duration {
  position: absolute;
  bottom: 4px;
  right: 6px;
  background: rgba(0, 0, 0, 0.7);
  color: #fff;
  padding: 0 4px;
  border-radius: 3px;
  font-size: 0.7rem;
}
.video-meta {
  flex: 1;
  min-width: 0;
}
.video-title {
  color: #fff;
  font-weight: 600;
  font-size: 0.92rem;
  margin-bottom: 0.25rem;
}
.video-stats {
  color: var(--text-dim);
  font-size: 0.78rem;
}
</style>