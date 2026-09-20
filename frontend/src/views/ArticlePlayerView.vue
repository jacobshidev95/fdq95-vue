<script setup lang="ts">
import { computed, onMounted, onBeforeUnmount, ref, watch, nextTick } from 'vue'
import { useRouter } from 'vue-router'
import { api } from '@/api/client'
import { useAuthStore } from '@/stores/auth'
import { useI18nStore } from '@/stores/i18n'

const router = useRouter()
const auth = useAuthStore()
const i18n = useI18nStore()

type FeedTab = 'following' | 'friends' | 'recommend' | 'activity'

const FEED_TABS = computed<{ key: FeedTab; label: string; icon: string }[]>(() => [
  { key: 'following', label: i18n.t('video_tab_following'), icon: '👀' },
  { key: 'friends',   label: i18n.t('video_tab_friends'),   icon: '👥' },
  { key: 'recommend', label: i18n.t('video_tab_recommend'), icon: '✨' },
  { key: 'activity',  label: i18n.t('video_tab_activity'),  icon: '🎉' },
])

const activeTab = ref<FeedTab>('recommend')

interface ArticleBlock {
  type: 'text' | 'image' | 'video'
  content: string
  caption?: string
}

interface ArticleItem {
  id: string
  owner_user_id: string
  owner_string_id: string
  owner_display_name: string
  owner_avatar_url: string | null
  title: string
  blocks: ArticleBlock[]
  like_count: number
  love_count: number
  comment_count: number
  is_liked: boolean
  is_loved: boolean
  is_following_owner: boolean
  created_at: string
}

const articles = ref<ArticleItem[]>([])
const currentIndex = ref(0)
const loading = ref(false)
const loadError = ref('')

const currentArticle = computed<ArticleItem | null>(
  () => articles.value[currentIndex.value] ?? null,
)

const articleScrollEl = ref<HTMLElement | null>(null)

async function loadFeed() {
  loading.value = true
  loadError.value = ''
  articles.value = []
  currentIndex.value = 0
  try {
    const { data } = await api.get('/api/articles/feed', {
      params: { tab: activeTab.value, limit: 20 },
    })
    articles.value = Array.isArray(data) ? data : data?.articles ?? []
  } catch (e: any) {
    const status = e?.response?.status
    if (status === 404) articles.value = []
    else if (status === 401) loadError.value = i18n.t('article_login_to_view')
    else loadError.value = e?.response?.data?.detail || i18n.t('article_load_failed')
  } finally {
    loading.value = false
  }
}

function nextArticle() {
  if (currentIndex.value < articles.value.length - 1) currentIndex.value++
}
function prevArticle() {
  if (currentIndex.value > 0) currentIndex.value--
}

function selectTab(tab: FeedTab) {
  if (activeTab.value === tab) return
  activeTab.value = tab
  loadFeed()
}

function onWheel(e: WheelEvent) {
  const el = articleScrollEl.value
  if (!el) return
  const atTop = el.scrollTop <= 0
  const atBottom = el.scrollTop + el.clientHeight >= el.scrollHeight - 1
  if (e.deltaY > 0 && atBottom) nextArticle()
  else if (e.deltaY < 0 && atTop) prevArticle()
}

let touchStartY = 0
function onTouchStart(e: TouchEvent) {
  touchStartY = e.touches[0].clientY
}
function onTouchEnd(e: TouchEvent) {
  const el = articleScrollEl.value
  if (!el) return
  const deltaY = touchStartY - e.changedTouches[0].clientY
  if (Math.abs(deltaY) < 50) return
  const atTop = el.scrollTop <= 0
  const atBottom = el.scrollTop + el.clientHeight >= el.scrollHeight - 1
  if (deltaY > 0 && atBottom) nextArticle()
  else if (deltaY < 0 && atTop) prevArticle()
}

function onKey(e: KeyboardEvent) {
  if (e.key === 'ArrowDown' || e.key === 'ArrowRight') nextArticle()
  else if (e.key === 'ArrowUp' || e.key === 'ArrowLeft') prevArticle()
}

watch(currentIndex, async () => {
  await nextTick()
  if (articleScrollEl.value) articleScrollEl.value.scrollTop = 0
})

function goSearch() { router.push('/search') }
function goSettings() { router.push('/settings') }
function goVideos() { router.push('/videos') }

async function onAvatarClick() {
  if (!currentArticle.value) return
  router.push(`/profile/${currentArticle.value.owner_string_id}`)
}
async function onToggleFollow() {
  const a = currentArticle.value
  if (!a) return
  try {
    if (a.is_following_owner) {
      await api.delete(`/api/social/follow/${a.owner_string_id}`)
      a.is_following_owner = false
    } else {
      await api.post(`/api/social/follow/${a.owner_string_id}`)
      a.is_following_owner = true
    }
  } catch (e) { console.warn('[ArticlePlayer] follow failed', e) }
}
async function onToggleLike() {
  const a = currentArticle.value
  if (!a) return
  try {
    if (a.is_liked) {
      await api.delete(`/api/articles/${a.id}/like`)
      a.is_liked = false; a.like_count = Math.max(0, a.like_count - 1)
    } else {
      await api.post(`/api/articles/${a.id}/like`)
      a.is_liked = true; a.like_count += 1
    }
  } catch (e) { console.warn('[ArticlePlayer] like failed', e) }
}
async function onToggleLove() {
  const a = currentArticle.value
  if (!a) return
  try {
    if (a.is_loved) {
      await api.delete(`/api/articles/${a.id}/love`)
      a.is_loved = false; a.love_count = Math.max(0, a.love_count - 1)
    } else {
      await api.post(`/api/articles/${a.id}/love`)
      a.is_loved = true; a.love_count += 1
    }
  } catch (e) { console.warn('[ArticlePlayer] love failed', e) }
}
function onShare() {
  const a = currentArticle.value
  if (!a) return
  router.push(`/articles/${a.id}/share`)
}
function onComment() {
  const a = currentArticle.value
  if (!a) return
  router.push(`/articles/${a.id}/comments`)
}

onMounted(() => {
  loadFeed()
  window.addEventListener('keydown', onKey)
})
onBeforeUnmount(() => {
  window.removeEventListener('keydown', onKey)
})
</script>

<template>
  <div class="article-page">
    <header class="top-bar">
      <div class="tab-group">
        <button
          v-for="t in FEED_TABS"
          :key="t.key"
          class="tab-btn"
          :class="{ active: activeTab === t.key }"
          @click="selectTab(t.key)"
        >
          <span class="tab-icon">{{ t.icon }}</span>
          <span class="tab-label">{{ t.label }}</span>
        </button>
      </div>
      <div class="right-actions">
        <button class="icon-btn" :title="i18n.t('tab_search')" @click="goSearch">🔍</button>
        <button class="icon-btn" :title="i18n.t('tab_settings')" @click="goSettings">⚙️</button>
        <button class="icon-btn video-btn" :title="i18n.t('video_btn')" @click="goVideos">▶</button>
      </div>
    </header>

    <main class="article-wrap">
      <div v-if="loading" class="state-layer">{{ i18n.t('video_loading') }}</div>

      <div v-else-if="loadError" class="state-layer error">
        <p>{{ loadError }}</p>
        <button class="btn btn-primary" @click="loadFeed">
          {{ i18n.t('video_retry') }}
        </button>
      </div>

      <div v-else-if="!currentArticle" class="state-layer">
        <p>{{ i18n.t('article_empty') }}</p>
        <p class="hint">{{ i18n.t('article_feed_not_ready') }}</p>
      </div>

      <template v-else>
        <div
          ref="articleScrollEl"
          class="article-scroll"
          @wheel.prevent="onWheel"
          @touchstart.passive="onTouchStart"
          @touchend.passive="onTouchEnd"
        >
          <article class="article-body">
            <h1 class="article-title">{{ currentArticle.title }}</h1>

            <div class="article-meta">
              <span class="owner-avatar">
                {{ currentArticle.owner_string_id.slice(-2).toUpperCase() }}
              </span>
              <span class="owner-id">@{{ currentArticle.owner_string_id }}</span>
              <span class="owner-name">{{ currentArticle.owner_display_name }}</span>
            </div>

            <div class="article-blocks">
              <template v-for="(block, i) in currentArticle.blocks" :key="i">
                <p v-if="block.type === 'text'" class="article-text">
                  {{ block.content }}
                </p>

                <figure v-else-if="block.type === 'image'" class="article-image">
                  <img :src="block.content" :alt="block.caption || ''" />
                  <figcaption v-if="block.caption">{{ block.caption }}</figcaption>
                </figure>

                <figure v-else-if="block.type === 'video'" class="article-video">
                  <video :src="block.content" controls playsinline />
                  <figcaption v-if="block.caption">{{ block.caption }}</figcaption>
                </figure>
              </template>
            </div>
          </article>
        </div>

        <button
          class="nav-arrow up"
          :disabled="currentIndex <= 0"
          @click="prevArticle"
        >▲</button>
        <button
          class="nav-arrow down"
          :disabled="currentIndex >= articles.length - 1"
          @click="nextArticle"
        >▼</button>

        <div class="article-counter">
          {{ currentIndex + 1 }} / {{ articles.length }}
        </div>
      </template>
    </main>

    <footer v-if="currentArticle" class="bottom-bar">
      <button class="avatar-btn" @click="onAvatarClick">
        <img
          v-if="currentArticle.owner_avatar_url"
          :src="currentArticle.owner_avatar_url"
          alt="avatar"
        />
        <span v-else class="avatar-fallback">
          {{ currentArticle.owner_string_id.slice(-2).toUpperCase() }}
        </span>
      </button>

      <button
        class="action-btn follow-btn"
        :class="{ following: currentArticle.is_following_owner }"
        @click="onToggleFollow"
      >
        {{ currentArticle.is_following_owner ? i18n.t('unfollow') : i18n.t('follow') }}
      </button>

      <button
        class="action-btn icon-action"
        :class="{ active: currentArticle.is_liked }"
        @click="onToggleLike"
      >
        👍<span class="count">{{ currentArticle.like_count }}</span>
      </button>

      <button class="action-btn icon-action" @click="onShare">↗</button>

      <button
        class="action-btn icon-action"
        :class="{ loved: currentArticle.is_loved }"
        @click="onToggleLove"
      >
        ❤<span class="count">{{ currentArticle.love_count }}</span>
      </button>

      <button class="comment-btn" @click="onComment">
        💬 {{ i18n.t('comment_placeholder') }}
      </button>
    </footer>
  </div>
</template>

<style scoped>
.article-page {
  display: flex;
  flex-direction: column;
  width: 100%;
  height: 100vh;
  height: 100dvh;
  max-height: 100vh;
  max-height: 100dvh;
  background: #000;
  color: #fff;
  overflow: hidden;
}

.top-bar {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 1rem;
  padding: 0.5rem 1rem;
  background: rgba(0, 0, 0, 0.85);
  flex: 0 0 auto;
  border-bottom: 1px solid rgba(255, 255, 255, 0.08);
  flex-wrap: wrap;
}
.tab-group { display: flex; gap: 0.4rem; flex-wrap: wrap; }
.tab-btn {
  background: transparent; border: none;
  color: rgba(255, 255, 255, 0.65);
  font-size: 0.95rem;
  padding: 0.35rem 0.6rem;
  border-radius: 6px;
  cursor: pointer;
  display: flex; align-items: center; gap: 0.3rem;
  transition: all 0.15s;
}
.tab-btn:hover { color: #fff; background: rgba(255, 255, 255, 0.06); }
.tab-btn.active {
  color: var(--gold, #e5b80b);
  background: rgba(229, 184, 11, 0.12);
  font-weight: 600;
}
.tab-icon { font-size: 0.9rem; }
.right-actions { display: flex; gap: 0.4rem; align-items: center; flex-wrap: wrap; }
.icon-btn {
  background: transparent;
  border: 1px solid rgba(255, 255, 255, 0.15);
  color: #fff;
  width: 34px; height: 34px;
  border-radius: 50%;
  font-size: 0.95rem;
  cursor: pointer;
  display: flex; align-items: center; justify-content: center;
}
.icon-btn:hover { border-color: var(--gold, #e5b80b); }
.video-btn { border-color: rgba(229, 184, 11, 0.5); }
.video-btn:hover { border-color: var(--gold, #e5b80b); background: rgba(229, 184, 11, 0.12); }

.article-wrap {
  flex: 1 1 auto;
  min-height: 0;
  position: relative;
  display: flex;
  align-items: stretch;
  justify-content: center;
  overflow: hidden;
}

.state-layer {
  text-align: center;
  color: rgba(255, 255, 255, 0.7);
  padding: 2rem;
  margin: auto;
}
.state-layer.error { color: #ff8a80; }
.state-layer .hint { font-size: 0.85rem; color: rgba(255, 255, 255, 0.4); margin-top: 0.5rem; }
.state-layer button { margin-top: 1rem; }

.article-scroll {
  width: 100%;
  max-width: 760px;
  height: 100%;
  overflow-y: auto;
  overflow-x: hidden;
  padding: 1.25rem 1.25rem 1.5rem;
  box-sizing: border-box;
  -webkit-overflow-scrolling: touch;
}
.article-scroll::-webkit-scrollbar { width: 8px; }
.article-scroll::-webkit-scrollbar-track { background: rgba(255, 255, 255, 0.03); }
.article-scroll::-webkit-scrollbar-thumb {
  background: rgba(255, 255, 255, 0.15);
  border-radius: 4px;
}

.article-body { width: 100%; }
.article-title {
  font-size: 1.4rem;
  font-weight: 700;
  color: #fff;
  margin: 0 0 0.75rem;
  line-height: 1.3;
  word-break: break-word;
}
.article-meta {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  font-size: 0.8rem;
  color: rgba(255, 255, 255, 0.55);
  margin-bottom: 1rem;
  padding-bottom: 0.75rem;
  border-bottom: 1px solid rgba(255, 255, 255, 0.08);
}
.owner-avatar {
  width: 26px; height: 26px;
  border-radius: 50%;
  background: hsl(210, 60%, 45%);
  color: #fff;
  display: flex; align-items: center; justify-content: center;
  font-size: 0.62rem; font-weight: 700;
  flex-shrink: 0;
}
.owner-id { color: var(--gold, #e5b80b); }
.owner-name { color: rgba(255, 255, 255, 0.7); }

.article-blocks { display: flex; flex-direction: column; gap: 0.9rem; }
.article-text {
  font-size: 0.98rem;
  line-height: 1.7;
  color: rgba(255, 255, 255, 0.9);
  margin: 0;
  white-space: pre-line;
  word-break: break-word;
}
.article-image { margin: 0; text-align: center; }
.article-image img {
  max-width: 100%;
  border-radius: 8px;
  display: block;
  margin: 0 auto;
}
.article-image figcaption {
  font-size: 0.75rem;
  color: rgba(255, 255, 255, 0.5);
  margin-top: 0.3rem;
  font-style: italic;
}
.article-video { margin: 0; text-align: center; }
.article-video video {
  max-width: 100%;
  border-radius: 8px;
  display: block;
  margin: 0 auto;
  background: #000;
}
.article-video figcaption {
  font-size: 0.75rem;
  color: rgba(255, 255, 255, 0.5);
  margin-top: 0.3rem;
  font-style: italic;
}

.nav-arrow {
  position: absolute;
  right: 0.75rem;
  background: rgba(0, 0, 0, 0.6);
  color: #fff;
  border: 1px solid rgba(255, 255, 255, 0.15);
  width: 36px; height: 36px;
  border-radius: 50%;
  font-size: 0.9rem;
  cursor: pointer;
  z-index: 5;
}
.nav-arrow.up { top: 0.75rem; }
.nav-arrow.down { bottom: 0.75rem; }
.nav-arrow:disabled { opacity: 0.25; cursor: not-allowed; }

.article-counter {
  position: absolute;
  top: 0.6rem;
  left: 50%;
  transform: translateX(-50%);
  background: rgba(0, 0, 0, 0.5);
  color: #fff;
  font-size: 0.72rem;
  padding: 0.12rem 0.55rem;
  border-radius: 10px;
  pointer-events: none;
}

.bottom-bar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 0.5rem;
  padding: 0.5rem 0.9rem;
  background: rgba(0, 0, 0, 0.9);
  flex: 0 0 auto;
  border-top: 1px solid rgba(255, 255, 255, 0.08);
}
.avatar-btn {
  width: 38px; height: 38px;
  border-radius: 50%;
  border: 2px solid var(--gold, #e5b80b);
  background: #333;
  overflow: hidden;
  cursor: pointer;
  flex-shrink: 0;
  display: flex; align-items: center; justify-content: center;
  color: #fff; font-weight: 700; font-size: 0.72rem;
}
.avatar-btn img { width: 100%; height: 100%; object-fit: cover; }
.action-btn {
  background: transparent; border: none; color: #fff;
  cursor: pointer;
  display: flex; align-items: center; gap: 0.2rem;
  padding: 0.3rem 0.45rem;
  border-radius: 6px;
  font-size: 1rem;
  transition: all 0.15s;
  flex-shrink: 0;
}
.action-btn:hover { background: rgba(255, 255, 255, 0.08); }

.follow-btn {
  background: #2ecc71; color: #fff;
  border: 1px solid #2ecc71;
  padding: 0.3rem 0.7rem;
  border-radius: 6px;
  font-weight: 600; font-size: 0.82rem;
}
.follow-btn:hover { background: #27ae60; border-color: #27ae60; }
.follow-btn.following { background: #666; border-color: #666; color: #ddd; }

.icon-action { font-size: 1.1rem; position: relative; }
.icon-action.active { color: #e5b80b; }
.icon-action.loved { color: #ff5e7e; }
.count { font-size: 0.7rem; color: rgba(255, 255, 255, 0.75); margin-left: 0.1rem; }

/* ★ 评论按钮：不伸展，宽度只到提示文字所需 */
.comment-btn {
  flex: 0 0 auto;
  max-width: 220px;
  background: rgba(255, 255, 255, 0.08);
  border: 1px solid rgba(255, 255, 255, 0.12);
  color: rgba(255, 255, 255, 0.7);
  padding: 0.4rem 0.85rem;
  border-radius: 20px;
  font-size: 0.83rem;
  text-align: left;
  cursor: pointer;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
.comment-btn:hover { background: rgba(255, 255, 255, 0.14); color: #fff; }

@media (max-width: 720px) {
  .tab-btn { font-size: 0.85rem; padding: 0.3rem 0.5rem; }
  .top-bar { gap: 0.5rem; padding: 0.4rem 0.7rem; }
  .comment-btn { max-width: 180px; }
}

@media (max-width: 480px) {
  .tab-label { display: none; }
  .tab-btn { padding: 0.28rem 0.45rem; }
  .tab-icon { font-size: 1rem; }
  .top-bar {
    padding: 0.28rem 0.5rem;
    gap: 0.25rem;
    flex-wrap: nowrap;
    overflow-x: auto;
  }
  .top-bar::-webkit-scrollbar { display: none; }
  .icon-btn { width: 28px; height: 28px; font-size: 0.8rem; }
  .right-actions { gap: 0.2rem; flex-shrink: 0; }

  .article-scroll { padding: 0.9rem 0.8rem 1rem; }
  .article-title { font-size: 1.15rem; }
  .article-text { font-size: 0.92rem; line-height: 1.65; }
  .article-blocks { gap: 0.7rem; }

  .nav-arrow { width: 30px; height: 30px; font-size: 0.75rem; }
  .nav-arrow.up { top: 0.4rem; }
  .nav-arrow.down { bottom: 0.4rem; }
  .article-counter { font-size: 0.66rem; padding: 0.1rem 0.45rem; top: 0.4rem; }

  .bottom-bar {
    gap: 0.2rem;
    padding: 0.32rem 0.5rem;
    flex-wrap: nowrap;
    overflow-x: auto;
  }
  .bottom-bar::-webkit-scrollbar { display: none; }
  .avatar-btn { width: 32px; height: 32px; font-size: 0.65rem; }
  .follow-btn {
    padding: 0.24rem 0.5rem;
    font-size: 0.7rem;
    flex-shrink: 0;
  }
  .action-btn {
    padding: 0.25rem 0.35rem;
    font-size: 0.92rem;
    flex-shrink: 0;
  }
  .count { display: none; }
  .comment-btn {
    font-size: 0.7rem;
    padding: 0.32rem 0.6rem;
    max-width: 140px;
    flex-shrink: 0;
  }
}

@media (max-width: 360px) {
  .follow-btn { font-size: 0.65rem; padding: 0.22rem 0.42rem; }
  .icon-action { font-size: 0.8rem; }
  .comment-btn { max-width: 110px; font-size: 0.66rem; }
}
</style>