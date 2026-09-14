<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { LATEST_UPLOADS, hueFor } from '@/data/mockVideos'
import { useI18nStore } from '@/stores/i18n'

const i18n = useI18nStore()

const PAGE_SIZE = 10
const ROTATE_MS = 3000
const totalPages = Math.ceil(LATEST_UPLOADS.length / PAGE_SIZE)

const pageIndex = ref(0)
let timer: number | null = null

const currentPage = computed(() =>
  LATEST_UPLOADS.slice(
    pageIndex.value * PAGE_SIZE,
    (pageIndex.value + 1) * PAGE_SIZE,
  ),
)

onMounted(() => {
  timer = window.setInterval(() => {
    pageIndex.value = (pageIndex.value + 1) % totalPages
  }, ROTATE_MS)
})

onUnmounted(() => {
  if (timer !== null) window.clearInterval(timer)
})
</script>

<template>
  <aside class="ticker-panel">
    <h3 class="panel-title">{{ i18n.t('latest_uploads') }}</h3>

    <ul class="video-list">
      <li v-for="v in currentPage" :key="v.id" class="video-item">
        <div
          class="thumb"
          :style="{
            background: `linear-gradient(135deg, hsl(${hueFor(v.id + 180)},55%,35%), hsl(${hueFor(v.id + 180)},55%,20%))`,
          }"
        >
          {{ v.id }}
        </div>
        <div class="meta">
          <div class="vtitle">{{ v.title }}</div>
          <div class="vviews">{{ v.views.toLocaleString() }} views</div>
        </div>
      </li>
    </ul>

    <div class="page-dots">
      <span
        v-for="(_, i) in totalPages"
        :key="i"
        class="dot"
        :class="{ active: i === pageIndex }"
      />
    </div>
  </aside>
</template>

<style scoped>
.ticker-panel {
  display: flex;
  flex-direction: column;
  padding: 0.75rem;
  background: #1a1a1a;
  border-left: 1px solid var(--border);
  overflow-y: auto;
}
.panel-title {
  margin: 0 0 0.5rem;
  font-size: 0.85rem;
  color: var(--gold);
  text-transform: uppercase;
  letter-spacing: 0.08em;
}

.video-list {
  list-style: none;
  padding: 0;
  margin: 0;
  flex: 1;
}
.video-item {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.35rem 0;
  border-bottom: 1px solid #262626;
}
.video-item:last-child {
  border-bottom: none;
}

.thumb {
  flex: 0 0 40px;
  height: 26px;
  border-radius: 4px;
  color: #fff;
  font-size: 0.75rem;
  font-weight: 700;
  display: flex;
  align-items: center;
  justify-content: center;
}

.meta {
  min-width: 0;
  flex: 1;
}
.vtitle {
  font-size: 0.78rem;
  color: var(--text);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
.vviews {
  font-size: 0.68rem;
  color: var(--text-dim);
}

.page-dots {
  display: flex;
  justify-content: center;
  gap: 4px;
  padding-top: 0.5rem;
}
.dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: #444;
  transition: background 0.2s;
}
.dot.active {
  background: var(--gold);
}
</style>