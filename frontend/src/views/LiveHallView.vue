<script setup lang="ts">
import { computed, nextTick, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { liveApi, type LiveSession } from '@/api/live'
import CategorySelect from '@/components/CategorySelect.vue'
import { useI18nStore } from '@/stores/i18n'

const route = useRoute()
const router = useRouter()
const i18n = useI18nStore()

const sessions = ref<LiveSession[]>([])
const allSessions = ref<LiveSession[]>([])
const loading = ref(true)
const scrollRoot = ref<HTMLElement | null>(null)
const cardRefs = ref<HTMLElement[]>([])
let observer: IntersectionObserver | null = null

// ★ 当前是否是活动大厅
const isActivityHall = computed(() => route.path.startsWith('/activity'))

// ★ 分类筛选：从 URL query 初始化
const categoryFilter = ref<string | null>(
  (route.query.category as string) || (isActivityHall.value ? 'activity' : null),
)

// ★ 监听 URL query 变化
watch(
  () => route.query.category,
  (val) => {
    const next = (val as string) || null
    if (next !== categoryFilter.value) {
      categoryFilter.value = next
      applyFilter()
    }
  },
)

// ★ 监听筛选器变化：更新 URL + 重新过滤
watch(categoryFilter, (val) => {
  const current = (route.query.category as string) || null
  if (val !== current) {
    const query = val ? { category: val } : {}
    router.replace({ path: route.path, query })
  }
  applyFilter()
})

// ★ 路由从 /live 切到 /activity（或反之）时重置筛选
watch(
  () => route.path,
  () => {
    if (isActivityHall.value && categoryFilter.value !== 'activity') {
      categoryFilter.value = 'activity'
    } else if (!isActivityHall.value && categoryFilter.value === 'activity') {
      categoryFilter.value = null
    }
    load()
  },
)

function applyFilter() {
  if (!categoryFilter.value) {
    sessions.value = allSessions.value.slice()
  } else {
    sessions.value = allSessions.value.filter(
      (s) => s.category === categoryFilter.value,
    )
  }
  nextTick(() => {
    if (observer) {
      observer.disconnect()
      cardRefs.value.forEach((el) => el && observer!.observe(el))
    }
  })
}

async function load() {
  loading.value = true
  try {
    const data = await liveApi.listActive(100, 0)
    allSessions.value = data
    applyFilter()
  } catch {
    allSessions.value = []
    sessions.value = []
  } finally {
    loading.value = false
  }
}

function setCardRef(el: any, idx: number) {
  if (el) cardRefs.value[idx] = el as HTMLElement
}

function enterSession(s: LiveSession) {
  if (isActivityHall.value) {
    router.push(`/activity/${s.room_id}`)
  } else {
    router.push(`/live/${s.room_id}`)
  }
}

// ★★★ 根据当前路径分流：活动 → 创建活动；直播 → 创建直播
function goCreate() {
  if (isActivityHall.value) {
    router.push('/settings/launch-activity')
  } else {
    router.push('/settings/go-live')
  }
}

function goCategoryAll() {
  if (isActivityHall.value) {
    // 活动大厅无法看"全部"，因为活动本身就是 category=activity
    // 这里保留切换逻辑，但活动视图下筛选器固定显示活动
    return
  }
  categoryFilter.value = null
}

onMounted(async () => {
  await load()
  await nextTick()
  observer = new IntersectionObserver(
    (entries) => {
      for (const e of entries) {
        if (e.isIntersecting) {
          // 当前可见卡片（可用于将来加自动播放等）
        }
      }
    },
    { threshold: 0.6, root: scrollRoot.value },
  )
  cardRefs.value.forEach((el) => el && observer!.observe(el))
})

onBeforeUnmount(() => {
  if (observer) observer.disconnect()
})
</script>

<template>
  <div class="hall-root" ref="scrollRoot">
    <div class="hall-top">
      <button class="back-btn" @click="router.back()">‹</button>
      <span class="hall-title">
        {{ isActivityHall ? (i18n.t('activity') || 'Activity') : (i18n.t('live') || 'Live') }}
      </span>
      <!-- 直播大厅显示分类筛选；活动大厅固定筛选 -->
      <div v-if="!isActivityHall" class="hall-filter">
        <CategorySelect
          v-model="categoryFilter"
          storage-key="fdq95_live_hall_filter"
          :placeholder="i18n.t('all_categories') || 'All'"
          :include-all="true"
          :all-label="i18n.t('all_categories') || 'All'"
        />
      </div>
    </div>

    <div v-if="loading" class="hall-empty">
      {{ i18n.t('video_loading') || 'Loading…' }}
    </div>

    <div v-else-if="sessions.length === 0" class="hall-empty">
      <p v-if="categoryFilter && !isActivityHall">
        {{ i18n.t('no_lives_in_category') || 'No live streams in this category' }}
      </p>
      <p v-else-if="isActivityHall">
        {{ i18n.t('no_activities') || 'No activities yet' }}
      </p>
      <p v-else>
        {{ i18n.t('no_lives') || 'No live streams yet' }}
      </p>

      <div class="hall-empty-actions">
        <button
          v-if="categoryFilter && !isActivityHall"
          class="go-btn ghost"
          @click="goCategoryAll"
        >
          {{ i18n.t('show_all') || 'Show all' }}
        </button>
        <button class="go-btn" @click="goCreate">
          {{ isActivityHall ? (i18n.t('activity_create') || 'Launch Activity') : (i18n.t('live_open') || 'Go Live') }}
        </button>
      </div>
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

        <div class="hall-card-title">{{ s.title || '—' }}</div>
        <div v-if="s.category" class="hall-card-cat"># {{ s.category }}</div>

        <div class="hall-stats">
          <span>👁 {{ s.viewer_count }}</span>
          <span>{{ new Date(s.started_at).toLocaleTimeString() }}</span>
        </div>

        <button class="hall-enter">
          {{ isActivityHall ? (i18n.t('activity_enter') || 'Enter Activity') : (i18n.t('live_enter') || 'Enter Live') }}
        </button>
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
  background: linear-gradient(to bottom, rgba(0, 0, 0, 0.75), transparent);
  pointer-events: none;
}
.hall-top .back-btn,
.hall-top .hall-title,
.hall-top .hall-filter { pointer-events: auto; }

.back-btn {
  background: rgba(0, 0, 0, 0.4);
  border: none;
  color: #fff;
  font-size: 1.6rem;
  line-height: 1;
  border-radius: 50%;
  width: 2rem; height: 2rem;
  cursor: pointer;
  flex-shrink: 0;
}
.hall-title {
  font-weight: 700;
  font-size: 1rem;
  flex-shrink: 0;
}

.hall-filter {
  margin-left: auto;
  width: 140px;
  max-width: 45%;
  flex-shrink: 0;
}
.hall-filter :deep(.cat-trigger) {
  background: rgba(0, 0, 0, 0.5);
  border-color: rgba(255, 255, 255, 0.25);
  padding: 0.3rem 0.5rem;
  font-size: 0.8rem;
}

.hall-empty {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 100vh;
  height: 100dvh;
  gap: 1rem;
  color: rgba(255, 255, 255, 0.7);
  padding: 0 2rem;
  text-align: center;
}
.hall-empty-actions {
  display: flex;
  gap: 0.6rem;
  flex-wrap: wrap;
  justify-content: center;
}
.go-btn {
  background: #8b5cf6;
  color: #fff;
  border: none;
  padding: 0.6rem 1.2rem;
  border-radius: 8px;
  font-size: 0.9rem;
  cursor: pointer;
}
.go-btn.ghost {
  background: transparent;
  border: 1px solid rgba(255, 255, 255, 0.3);
  color: rgba(255, 255, 255, 0.85);
}
.go-btn.ghost:hover { border-color: #8b5cf6; color: #c4b5fd; }

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
  background: #e74c3c;
  color: #fff;
  padding: 0.25rem 0.6rem;
  border-radius: 12px;
  font-size: 0.72rem;
  font-weight: 700;
}
.hall-avatar {
  width: 100px;
  height: 100px;
  border-radius: 50%;
  object-fit: cover;
  border: 3px solid #8b5cf6;
}
.hall-avatar.placeholder {
  display: flex;
  align-items: center;
  justify-content: center;
  background: #8b5cf6;
  font-size: 2.5rem;
  font-weight: 700;
}
.hall-host-name { font-size: 1.1rem; font-weight: 600; }
.hall-host-id { opacity: 0.5; font-size: 0.8rem; margin-left: 0.3rem; }
.hall-card-title { font-size: 1.2rem; font-weight: 700; margin-top: 0.3rem; }
.hall-card-cat { color: #c4b5fd; font-size: 0.85rem; }
.hall-stats {
  display: flex;
  gap: 1rem;
  font-size: 0.85rem;
  opacity: 0.8;
}
.hall-enter {
  margin-top: 1rem;
  background: #8b5cf6;
  color: #fff;
  border: none;
  padding: 0.7rem 1.8rem;
  border-radius: 24px;
  font-size: 0.95rem;
  font-weight: 600;
  cursor: pointer;
}
</style>