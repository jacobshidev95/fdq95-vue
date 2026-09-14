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
    activity_id: string
    title: string
    url: string
    duration_sec: number
    created_at: string
  }>
>([])

async function load() {
  const { data } = await api.get(
    `/api/videos/activity/user/${userId.value}`,
  )
  videos.value = data
}

onMounted(load)
</script>

<template>
  <div class="page">
    <div class="top-bar">
      <button class="back-btn" @click="router.push(`/profile/${userId}`)">←</button>
      <span class="title">{{ i18n.t('activity_replay') }} — @{{ userId }}</span>
    </div>

    <p v-if="videos.length === 0" class="empty">
      {{ i18n.t('no_activity_replays') }}
    </p>

    <ul class="list">
      <li v-for="v in videos" :key="v.id" class="item">
        <span class="play">▶</span>
        <div class="meta">
          <div class="name">{{ v.title }}</div>
          <div class="sub">
            Activity {{ v.activity_id }} · {{ v.duration_sec }}s
          </div>
        </div>
      </li>
    </ul>
  </div>
</template>

<style scoped>
.page {
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
  padding: 0.35rem 0.75rem;
  border-radius: 6px;
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
.list {
  list-style: none;
  padding: 0;
  margin: 0;
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}
.item {
  display: flex;
  gap: 0.75rem;
  background: var(--bg-soft);
  border: 1px solid var(--border);
  border-radius: 8px;
  padding: 0.65rem 0.85rem;
  cursor: pointer;
}
.item:hover {
  border-color: var(--gold);
}
.play {
  font-size: 1.2rem;
  color: var(--gold);
}
.name {
  color: #fff;
  font-weight: 600;
}
.sub {
  color: var(--text-dim);
  font-size: 0.78rem;
}
</style>