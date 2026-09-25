<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { liveApi, type LiveReplay } from '@/api/live'
import { useI18nStore } from '@/stores/i18n'

const route = useRoute()
const router = useRouter()
const i18n = useI18nStore()

const userId = computed(() => (route.params.userId as string) || '')
const replays = ref<LiveReplay[]>([])
const loading = ref(false)
const loadError = ref('')

async function load() {
  if (!userId.value) return
  loading.value = true
  loadError.value = ''
  try {
    replays.value = await liveApi.listReplays(userId.value)
  } catch (e: any) {
    const status = e?.response?.status
    if (status === 404) loadError.value = `用户 @${userId.value} 不存在`
    else loadError.value = e?.response?.data?.detail || i18n.t('load_failed')
  } finally {
    loading.value = false
  }
}

onMounted(load)
watch(userId, load)

function openReplay(r: LiveReplay) {
  if (r.recorded_video_url) {
    window.open(r.recorded_video_url, '_blank', 'noopener,noreferrer')
  } else {
    // 无录制视频 → 回放当时的直播间（若主播还在线会显示已结束）
    router.push(`/live/${r.room_id}`)
  }
}

function fmtTime(iso: string | null): string {
  if (!iso) return '—'
  try {
    return new Date(iso).toLocaleString()
  } catch {
    return iso
  }
}

function fmtDuration(started: string, ended: string | null): string {
  if (!started || !ended) return '—'
  const s = new Date(started).getTime()
  const e = new Date(ended).getTime()
  const sec = Math.max(0, Math.floor((e - s) / 1000))
  const m = Math.floor(sec / 60)
  const h = Math.floor(m / 60)
  if (h > 0) return `${h}h ${m % 60}m`
  if (m > 0) return `${m}m ${sec % 60}s`
  return `${sec}s`
}
</script>

<template>
  <div class="replays-page">
    <header class="top-bar">
      <button class="back-btn" @click="router.back()">‹</button>
      <h1 class="page-title">{{ i18n.t('live_replay') }}</h1>
      <span class="spacer" />
    </header>

    <div class="scroll-body">
      <div v-if="loading" class="state">加载中…</div>

      <div v-else-if="loadError" class="state error">
        <p>{{ loadError }}</p>
        <button class="retry-btn" @click="load">重试</button>
      </div>

      <div v-else-if="replays.length === 0" class="state">
        <p>{{ i18n.t('live_replay_empty') }}</p>
      </div>

      <ul v-else class="replay-list">
        <li
          v-for="r in replays"
          :key="r.id"
          class="replay-card"
          @click="openReplay(r)"
        >
          <div class="replay-thumb">
            <span class="replay-play">▶</span>
          </div>
          <div class="replay-meta">
            <div class="replay-title">{{ r.title || 'Untitled' }}</div>
            <div class="replay-sub">
              <span v-if="r.category" class="replay-cat"># {{ r.category }}</span>
              <span class="replay-stat">👁 {{ r.viewer_count }}</span>
            </div>
            <div class="replay-time">
              {{ fmtTime(r.started_at) }} · {{ fmtDuration(r.started_at, r.ended_at) }}
            </div>
          </div>
        </li>
      </ul>
    </div>
  </div>
</template>

<style scoped>
.replays-page {
  display: flex;
  flex-direction: column;
  width: 100%;
  min-height: 100vh;
  background: #000;
  color: #fff;
}
.top-bar {
  display: flex;
  align-items: center;
  padding: 0.8rem 1rem;
  background: #000;
  position: sticky;
  top: 0;
  z-index: 10;
  flex-shrink: 0;
}
.back-btn {
  background: transparent;
  border: none;
  color: #fff;
  font-size: 2rem;
  line-height: 1;
  cursor: pointer;
  width: 36px;
  height: 36px;
  border-radius: 6px;
  padding: 0;
}
.back-btn:hover { background: rgba(255, 255, 255, 0.08); }
.page-title {
  flex: 1;
  text-align: right;
  margin: 0;
  font-size: 1rem;
  font-weight: 500;
}
.spacer { width: 36px; }

.scroll-body {
  flex: 1 1 auto;
  padding: 0.5rem 0.75rem 2rem;
  overflow-y: auto;
}

.state {
  padding: 3rem 1rem;
  text-align: center;
  color: rgba(255, 255, 255, 0.6);
}
.state.error { color: #ff8a80; }
.retry-btn {
  margin-top: 0.8rem;
  background: #8b5cf6;
  color: #fff;
  border: none;
  padding: 0.5rem 1.2rem;
  border-radius: 8px;
  cursor: pointer;
}

.replay-list {
  list-style: none;
  margin: 0;
  padding: 0;
  display: flex;
  flex-direction: column;
  gap: 0.6rem;
}
.replay-card {
  display: flex;
  gap: 0.75rem;
  background: #1a1a1a;
  border: 1px solid rgba(255, 255, 255, 0.08);
  border-radius: 10px;
  padding: 0.65rem;
  cursor: pointer;
  transition: border-color 0.15s;
}
.replay-card:hover { border-color: #8b5cf6; }

.replay-thumb {
  flex: 0 0 100px;
  height: 64px;
  background: linear-gradient(135deg, #1f1f3a, #2a1f4a);
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
}
.replay-play {
  color: #fff;
  font-size: 1.4rem;
  opacity: 0.85;
}

.replay-meta {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: 0.2rem;
}
.replay-title {
  font-size: 0.95rem;
  font-weight: 600;
  color: #fff;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
.replay-sub {
  display: flex;
  gap: 0.6rem;
  font-size: 0.78rem;
  color: rgba(255, 255, 255, 0.55);
}
.replay-cat { color: #c4b5fd; }
.replay-stat { color: rgba(255, 255, 255, 0.6); }
.replay-time {
  font-size: 0.72rem;
  color: rgba(255, 255, 255, 0.4);
}
</style>