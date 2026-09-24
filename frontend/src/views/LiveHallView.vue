<script setup lang="ts">
import { nextTick, onBeforeUnmount, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { liveApi, type LiveSession } from '@/api/live'

const router = useRouter()
const sessions = ref<LiveSession[]>([])
const loading = ref(true)
const scrollRoot = ref<HTMLElement | null>(null)
const cardRefs = ref<HTMLElement[]>([])
let observer: IntersectionObserver | null = null

async function load() {
  try {
    sessions.value = await liveApi.listActive(30, 0)
  } catch {
    sessions.value = []
  } finally {
    loading.value = false
  }
}

function setCardRef(el: any, idx: number) {
  if (el) cardRefs.value[idx] = el as HTMLElement
}

function enterSession(s: LiveSession) {
  router.push(`/live/${s.room_id}`)
}

onMounted(async () => {
  await load()
  await nextTick()
  observer = new IntersectionObserver(
    entries => {
      for (const e of entries) {
        if (e.isIntersecting) {
          // 当前可见卡片（可用于将来加自动播放等）
        }
      }
    },
    { threshold: 0.6, root: scrollRoot.value }
  )
  cardRefs.value.forEach(el => el && observer!.observe(el))
})

onBeforeUnmount(() => {
  if (observer) observer.disconnect()
})
</script>

<template>
  <div class="hall-root" ref="scrollRoot">
    <div class="hall-top">
      <button class="back-btn" @click="router.back()">‹</button>
      <span class="hall-title">直播</span>
    </div>

    <div v-if="loading" class="hall-empty">加载中…</div>
    <div v-else-if="sessions.length === 0" class="hall-empty">
      <p>暂无正在直播的房间</p>
      <button class="go-btn" @click="router.push('/settings/go-live')">
        去开播
      </button>
    </div>

    <div
      v-for="(s, idx) in sessions"
      :key="s.room_id + idx"
      :ref="(el) => setCardRef(el, idx)"
      class="hall-card"
      @click="enterSession(s)"
    >
      <div class="hall-live-badge">● LIVE</div>
      <div class="hall-card-inner">
        <img
          v-if="s.host_avatar_url"
          :src="s.host_avatar_url"
          class="hall-avatar"
          alt=""
        />
        <div v-else class="hall-avatar placeholder">
          {{ (s.host_display_name || '?')[0] }}
        </div>

        <div class="hall-host-name">
          {{ s.host_display_name }}
          <span class="hall-host-id">@{{ s.host_user_id }}</span>
        </div>

        <div class="hall-card-title">{{ s.title || '未命名直播' }}</div>
        <div v-if="s.category" class="hall-card-cat"># {{ s.category }}</div>

        <div class="hall-stats">
          <span>👁 {{ s.viewer_count }}</span>
          <span>{{ new Date(s.started_at).toLocaleTimeString() }}</span>
        </div>

        <button class="hall-enter">进入直播间</button>
      </div>
    </div>
  </div>
</template>

<style scoped>
.hall-root {
  width: 100vw;
  height: 100vh;
  height: 100dvh;
  overflow-y: scroll;
  scroll-snap-type: y mandatory;
  background: #000;
  color: #fff;
  scrollbar-width: none;
}
.hall-root::-webkit-scrollbar { display: none; }

.hall-top {
  position: fixed;
  top: 0; left: 0; right: 0;
  z-index: 100;
  display: flex;
  align-items: center;
  gap: 0.6rem;
  padding: 0.6rem 0.8rem;
  background: linear-gradient(to bottom, rgba(0, 0, 0, 0.7), transparent);
  pointer-events: none;
}
.hall-top .back-btn,
.hall-top .hall-title { pointer-events: auto; }
.back-btn {
  background: rgba(0, 0, 0, 0.4);
  border: none;
  color: #fff;
  font-size: 1.6rem;
  line-height: 1;
  border-radius: 50%;
  width: 2rem; height: 2rem;
  cursor: pointer;
}
.hall-title { font-weight: 700; font-size: 1rem; }

.hall-empty {
  display: flex; flex-direction: column;
  align-items: center; justify-content: center;
  height: 100vh; gap: 1rem;
  color: rgba(255, 255, 255, 0.7);
}
.go-btn {
  background: #8b5cf6; color: #fff; border: none;
  padding: 0.6rem 1.2rem; border-radius: 8px;
  font-size: 0.9rem; cursor: pointer;
}

.hall-card {
  position: relative;
  width: 100%;
  height: 100vh;
  height: 100dvh;
  scroll-snap-align: start;
  scroll-snap-stop: always;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  background: linear-gradient(135deg, #1a1a2e, #16213e);
}
.hall-card-inner {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 0.6rem;
  padding: 1.5rem;
  text-align: center;
  max-width: 90vw;
}
.hall-live-badge {
  position: absolute;
  top: 3.5rem; left: 1rem;
  background: #e74c3c; color: #fff;
  padding: 0.25rem 0.6rem;
  border-radius: 12px;
  font-size: 0.72rem;
  font-weight: 700;
}
.hall-avatar {
  width: 100px; height: 100px;
  border-radius: 50%;
  object-fit: cover;
  border: 3px solid #8b5cf6;
}
.hall-avatar.placeholder {
  display: flex; align-items: center; justify-content: center;
  background: #8b5cf6; font-size: 2.5rem; font-weight: 700;
}
.hall-host-name { font-size: 1.1rem; font-weight: 600; }
.hall-host-id { opacity: 0.5; font-size: 0.8rem; margin-left: 0.3rem; }
.hall-card-title { font-size: 1.2rem; font-weight: 700; margin-top: 0.3rem; }
.hall-card-cat { color: #c4b5fd; font-size: 0.85rem; }
.hall-stats {
  display: flex; gap: 1rem;
  font-size: 0.85rem; opacity: 0.8;
}
.hall-enter {
  margin-top: 1rem;
  background: #8b5cf6; color: #fff; border: none;
  padding: 0.7rem 1.8rem;
  border-radius: 24px;
  font-size: 0.95rem; font-weight: 600;
  cursor: pointer;
}
</style>