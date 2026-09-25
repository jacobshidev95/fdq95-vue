<script setup lang="ts">
import { computed, onMounted, onBeforeUnmount, ref, watch, nextTick } from 'vue'
import { useRouter } from 'vue-router'
import { api } from '@/api/client'
import { useAuthStore } from '@/stores/auth'
import { useI18nStore } from '@/stores/i18n'

const router = useRouter()
const auth = useAuthStore()
const i18n = useI18nStore()

// ★ FeedTab 加 'live'
type FeedTab = 'following' | 'friends' | 'recommend' | 'live' | 'activity'

// ★ 5 个 tab：following / friends / recommend / live / activity
const FEED_TABS = computed<{ key: FeedTab; label: string; icon: string }[]>(() => [
  { key: 'following', label: i18n.t('video_tab_following'), icon: '👀' },
  { key: 'friends',   label: i18n.t('video_tab_friends'),   icon: '👥' },
  { key: 'recommend', label: i18n.t('video_tab_recommend'), icon: '✨' },
  { key: 'live',      label: i18n.t('live'),                icon: '📺' },
  { key: 'activity',  label: i18n.t('activity'),            icon: '🎉' },
])

const activeTab = ref<FeedTab>('recommend')

interface VideoItem {
  id: string
  owner_user_id: string
  owner_string_id: string
  owner_display_name: string
  owner_avatar_url: string | null
  video_url: string
  thumbnail_url: string | null
  caption: string | null
  like_count: number
  love_count: number
  comment_count: number
  is_liked: boolean
  is_loved: boolean
  is_following_owner: boolean
  created_at: string
}

const videos = ref<VideoItem[]>([])
const currentIndex = ref(0)
const loading = ref(false)
const loadError = ref('')
const isPaused = ref(false)

const currentTime = ref(0)
const duration = ref(0)

interface SubtitleSegment { start: number; end: number; text: string }
const subtitles = ref<SubtitleSegment[]>([])
const subtitleStatus = ref<'idle' | 'pending' | 'processing' | 'done' | 'failed'>('idle')
let subtitlePollTimer: number | null = null

const currentVideo = computed<VideoItem | null>(
  () => videos.value[currentIndex.value] ?? null,
)

const videoEl = ref<HTMLVideoElement | null>(null)

// ══════════════════════════════════════════════════════════════
// 视频源解析
// ══════════════════════════════════════════════════════════════
type VideoSource =
  | { type: 'embed'; platform: string; embedUrl: string; originalUrl: string }
  | { type: 'direct'; url: string }
  | { type: 'external'; platform: string; originalUrl: string }
  | { type: 'unknown'; url: string }

function parseYouTube(url: string): string | null {
  const m = url.match(
    /(?:youtube\.com\/(?:watch\?v=|embed\/|v\/|shorts\/)|youtu\.be\/)([A-Za-z0-9_-]{11})/,
  )
  if (!m) return null
  return `https://www.youtube-nocookie.com/embed/${m[1]}?rel=0&playsinline=1&modestbranding=1`
}
function parseBilibili(url: string): string | null {
  const bv = url.match(/bilibili\.com\/video\/(BV[A-Za-z0-9]{10})/)
  if (bv) return `https://player.bilibili.com/player.html?bvid=${bv[1]}&autoplay=0&high_quality=1`
  const av = url.match(/bilibili\.com\/video\/av(\d+)/)
  if (av) return `https://player.bilibili.com/player.html?aid=${av[1]}&autoplay=0&high_quality=1`
  return null
}
function parseTencent(url: string): string | null {
  const m = url.match(/v\.qq\.com\/x\/(?:page|cover)\/(?:[^/]+\/)?([a-zA-Z0-9]+)\.html/)
  return m ? `https://v.qq.com/txp/iframe/player.html?vid=${m[1]}` : null
}
function parseYouku(url: string): string | null {
  const m = url.match(/v\.youku\.com\/v_show\/id_([A-Za-z0-9=]+)\.html/)
  return m ? `https://player.youku.com/embed/${m[1]}` : null
}
function parseTikTok(url: string): string | null {
  const m = url.match(/tiktok\.com\/@[^/]+\/video\/(\d+)/)
  return m ? `https://www.tiktok.com/embed/v2/${m[1]}` : null
}
function parseVimeo(url: string): string | null {
  const m = url.match(/vimeo\.com\/(?:video\/)?(\d+)/)
  return m ? `https://player.vimeo.com/video/${m[1]}?autoplay=0` : null
}
function isDirectVideoUrl(url: string): boolean {
  return /\.(mp4|webm|ogg|mov)(\?|$|#)/i.test(url)
}
function detectDouyin(url: string): boolean {
  return /(?:douyin\.com\/video\/|iesdouyin\.com\/share\/video\/)/.test(url)
}
function detectKuaishou(url: string): boolean {
  return /(?:kuaishou\.com\/(?:short-video|fw)\/|v\.kuaishou\.com\/)/.test(url)
}
function detectWechat(url: string): boolean {
  return /(?:channels\.weixin\.qq\.com|mp\.weixin\.qq\.com\/s\/(?:finder|video))/i.test(url)
}
function detectHaokan(url: string): boolean {
  return /haokan\.baidu\.com\/v\?vid=/.test(url)
}

function parseVideoSource(url: string): VideoSource {
  if (!url) return { type: 'unknown', url: '' }

  const yt = parseYouTube(url)
  if (yt) return { type: 'embed', platform: 'YouTube', embedUrl: yt, originalUrl: url }

  const bl = parseBilibili(url)
  if (bl) return { type: 'embed', platform: 'Bilibili', embedUrl: bl, originalUrl: url }

  const tx = parseTencent(url)
  if (tx) return { type: 'embed', platform: 'Tencent', embedUrl: tx, originalUrl: url }

  const yk = parseYouku(url)
  if (yk) return { type: 'embed', platform: 'Youku', embedUrl: yk, originalUrl: url }

  const tt = parseTikTok(url)
  if (tt) return { type: 'embed', platform: 'TikTok', embedUrl: tt, originalUrl: url }

  const vm = parseVimeo(url)
  if (vm) return { type: 'embed', platform: 'Vimeo', embedUrl: vm, originalUrl: url }

  if (detectDouyin(url)) return { type: 'external', platform: '抖音', originalUrl: url }
  if (detectKuaishou(url)) return { type: 'external', platform: '快手', originalUrl: url }
  if (detectWechat(url)) return { type: 'external', platform: '微信视频号', originalUrl: url }
  if (detectHaokan(url)) return { type: 'external', platform: '好看视频', originalUrl: url }

  if (isDirectVideoUrl(url)) return { type: 'direct', url }

  return { type: 'unknown', url }
}

const currentVideoSource = computed<VideoSource>(() =>
  parseVideoSource(currentVideo.value?.video_url || ''),
)

const isEmbedVideo = computed(() => currentVideoSource.value.type === 'embed')
const isDirectVideo = computed(
  () =>
    currentVideoSource.value.type === 'direct' ||
    currentVideoSource.value.type === 'unknown',
)
const isExternalVideo = computed(() => currentVideoSource.value.type === 'external')

function openExternal() {
  const src = currentVideoSource.value
  if (src.type === 'embed' || src.type === 'external') {
    window.open(src.originalUrl, '_blank', 'noopener,noreferrer')
  }
}

// ══════════════════════════════════════════════════════════════

const progressPct = computed(() => {
  if (!duration.value) return 0
  return Math.min(100, (currentTime.value / duration.value) * 100)
})

const remainingTime = computed(() => {
  const rem = duration.value - currentTime.value
  return rem > 0 ? rem : 0
})

const currentSubtitle = computed(() => {
  const t = currentTime.value
  const seg = subtitles.value.find((s) => t >= s.start && t <= s.end)
  return seg?.text || ''
})

function formatTime(sec: number): string {
  if (!isFinite(sec) || sec < 0) sec = 0
  const s = Math.floor(sec % 60)
  const m = Math.floor((sec / 60) % 60)
  const h = Math.floor(sec / 3600)
  const pad = (n: number) => n.toString().padStart(2, '0')
  return h > 0 ? `${h}:${pad(m)}:${pad(s)}` : `${m}:${pad(s)}`
}

async function loadFeed() {
  loading.value = true
  loadError.value = ''
  videos.value = []
  currentIndex.value = 0
  try {
    const { data } = await api.get('/api/videos/feed', {
      params: { tab: activeTab.value, limit: 100 },
    })
    videos.value = Array.isArray(data) ? data : data?.videos ?? []
  } catch (e: any) {
    const status = e?.response?.status
    if (status === 404) loadError.value = i18n.t('video_feed_not_ready')
    else if (status === 401) loadError.value = i18n.t('video_login_to_view')
    else loadError.value = e?.response?.data?.detail || i18n.t('video_load_failed')
  } finally {
    loading.value = false
    await nextTick()
    playCurrent()
  }
}

async function loadSubtitles(videoId: string) {
  try {
    const { data } = await api.get(`/api/videos/${videoId}/subtitles`)
    subtitleStatus.value = data.status || 'pending'
    subtitles.value = data.segments || []
    if (data.status === 'pending' || data.status === 'processing') {
      if (subtitlePollTimer) clearTimeout(subtitlePollTimer)
      subtitlePollTimer = window.setTimeout(() => {
        if (currentVideo.value?.id === videoId) loadSubtitles(videoId)
      }, 5000)
    }
  } catch {
    subtitleStatus.value = 'failed'
  }
}

function playCurrent() {
  if (isEmbedVideo.value || isExternalVideo.value) return
  const el = videoEl.value
  if (!el || !currentVideo.value?.video_url) return
  el.load()
  el.play().then(() => { isPaused.value = false }).catch(() => { isPaused.value = true })
}

function togglePlay() {
  if (isEmbedVideo.value || isExternalVideo.value) return
  const el = videoEl.value
  if (!el) return
  if (el.paused) { el.play().catch(() => {}); isPaused.value = false }
  else { el.pause(); isPaused.value = true }
}

function onStageClick() {
  if (isEmbedVideo.value || isExternalVideo.value) return
  togglePlay()
}

function nextVideo() {
  if (currentIndex.value < videos.value.length - 1) currentIndex.value++
}
function prevVideo() {
  if (currentIndex.value > 0) currentIndex.value--
}

function onTimeUpdate() {
  const el = videoEl.value
  if (!el) return
  currentTime.value = el.currentTime
  if (el.duration && isFinite(el.duration)) duration.value = el.duration
}
function onLoadedMetadata() {
  const el = videoEl.value
  if (el && el.duration && isFinite(el.duration)) duration.value = el.duration
}
function onSeek(e: MouseEvent) {
  const bar = e.currentTarget as HTMLElement
  const rect = bar.getBoundingClientRect()
  const ratio = Math.max(0, Math.min(1, (e.clientX - rect.left) / rect.width))
  const el = videoEl.value
  if (el && el.duration && isFinite(el.duration)) el.currentTime = ratio * el.duration
}

function selectTab(tab: FeedTab) {
  if (activeTab.value === tab) return
  activeTab.value = tab
  loadFeed()
}

function onWheel(e: WheelEvent) {
  if (e.deltaY > 0) nextVideo()
  else if (e.deltaY < 0) prevVideo()
}

let touchStartY = 0
function onTouchStart(e: TouchEvent) {
  touchStartY = e.touches[0].clientY
}
function onTouchEnd(e: TouchEvent) {
  const deltaY = touchStartY - e.changedTouches[0].clientY
  if (Math.abs(deltaY) < 50) return
  if (deltaY > 0) nextVideo()
  else prevVideo()
}

function onKey(e: KeyboardEvent) {
  if (e.key === 'ArrowDown' || e.key === 'ArrowRight') nextVideo()
  else if (e.key === 'ArrowUp' || e.key === 'ArrowLeft') prevVideo()
  else if (e.key === ' ' && !isEmbedVideo.value && !isExternalVideo.value) {
    e.preventDefault()
    togglePlay()
  }
}

watch(currentIndex, async () => {
  currentTime.value = 0
  duration.value = 0
  subtitles.value = []
  subtitleStatus.value = 'idle'
  if (subtitlePollTimer) { clearTimeout(subtitlePollTimer); subtitlePollTimer = null }
  await nextTick()
  playCurrent()
  if (currentVideo.value && isDirectVideo.value) {
    loadSubtitles(currentVideo.value.id)
  }
})

function goSearch() { router.push('/search') }
function goSettings() { router.push('/settings') }
function goArticles() { router.push('/articles') }

// ★ 已移除 goLive()（Live 现在是 tab 而不是跳转）

async function onAvatarClick() {
  if (!currentVideo.value) return
  router.push(`/profile/${currentVideo.value.owner_string_id}`)
}
async function onToggleFollow() {
  const v = currentVideo.value
  if (!v) return
  try {
    if (v.is_following_owner) {
      await api.delete(`/api/social/follow/${v.owner_string_id}`)
      v.is_following_owner = false
    } else {
      await api.post(`/api/social/follow/${v.owner_string_id}`)
      v.is_following_owner = true
    }
  } catch (e) { console.warn('[VideoPlayer] follow failed', e) }
}
async function onToggleLike() {
  const v = currentVideo.value
  if (!v) return
  try {
    if (v.is_liked) {
      await api.delete(`/api/videos/${v.id}/like`)
      v.is_liked = false; v.like_count = Math.max(0, v.like_count - 1)
    } else {
      await api.post(`/api/videos/${v.id}/like`)
      v.is_liked = true; v.like_count += 1
    }
  } catch (e) { console.warn('[VideoPlayer] like failed', e) }
}
async function onToggleLove() {
  const v = currentVideo.value
  if (!v) return
  try {
    if (v.is_loved) {
      await api.delete(`/api/videos/${v.id}/love`)
      v.is_loved = false; v.love_count = Math.max(0, v.love_count - 1)
    } else {
      await api.post(`/api/videos/${v.id}/love`)
      v.is_loved = true; v.love_count += 1
    }
  } catch (e) { console.warn('[VideoPlayer] love failed', e) }
}
function onShare() {
  const v = currentVideo.value
  if (!v) return
  router.push(`/videos/${v.id}/share`)
}
function onComment() {
  const v = currentVideo.value
  if (!v) return
  router.push(`/videos/${v.id}/comments`)
}

onMounted(() => {
  loadFeed()
  window.addEventListener('keydown', onKey)
})

onBeforeUnmount(() => {
  window.removeEventListener('keydown', onKey)
  if (subtitlePollTimer) clearTimeout(subtitlePollTimer)
})
</script>

<template>
  <div class="video-page">
    <header class="top-bar">
      <div class="tab-group">
        <!-- ★ 5 个 tab 直接循环：following / friends / recommend / live / activity -->
        <button
          v-for="t in FEED_TABS"
          :key="t.key"
          class="tab-btn"
          :class="{
            active: activeTab === t.key,
            'live-btn': t.key === 'live',
            'activity-btn': t.key === 'activity',
          }"
          @click="selectTab(t.key)"
        >
          <span v-if="t.key === 'live'" class="live-dot" />
          <span v-else-if="t.key === 'activity'" class="activity-dot" />
          <span v-else class="tab-icon">{{ t.icon }}</span>
          <span class="tab-label">{{ t.label }}</span>
        </button>
      </div>
      <div class="right-actions">
        <button class="icon-btn" :title="i18n.t('tab_search')" @click="goSearch">🔍</button>
        <button class="icon-btn" :title="i18n.t('tab_settings')" @click="goSettings">⚙️</button>
        <button class="icon-btn article-btn" :title="i18n.t('article_btn')" @click="goArticles">
          📄
        </button>
      </div>
    </header>

    <main
      class="player-wrap"
      @wheel.prevent="onWheel"
      @touchstart.passive="onTouchStart"
      @touchend.passive="onTouchEnd"
    >
      <div v-if="loading" class="state-layer">{{ i18n.t('video_loading') }}</div>

      <div v-else-if="loadError" class="state-layer error">
        <p>{{ loadError }}</p>
        <button class="btn btn-primary" @click="loadFeed">
          {{ i18n.t('video_retry') }}
        </button>
      </div>

      <div v-else-if="!currentVideo" class="state-layer">
        <p>{{ i18n.t('no_videos_yet') }}</p>
        <p class="hint">{{ i18n.t('video_feed_not_ready') }}</p>
      </div>

      <div v-else class="video-stage" @click="onStageClick">
        <video
          v-if="isDirectVideo"
          ref="videoEl"
          class="video-el"
          :src="currentVideo.video_url"
          :poster="currentVideo.thumbnail_url || undefined"
          playsinline
          loop
          preload="auto"
          @timeupdate="onTimeUpdate"
          @loadedmetadata="onLoadedMetadata"
        />

        <div v-else-if="isEmbedVideo" class="embed-wrap">
          <iframe
            class="embed-video"
            :src="(currentVideoSource as any).embedUrl"
            frameborder="0"
            allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share; fullscreen"
            allowfullscreen
          />
        </div>

        <div v-else-if="isExternalVideo" class="external-card">
          <div class="external-platform">{{ (currentVideoSource as any).platform }}</div>
          <div class="external-icon">🎬</div>
          <p class="external-hint">此平台不支持嵌入播放，请点击下方按钮跳转观看</p>
          <button class="external-btn" @click.stop="openExternal">
            ▶ 在 {{ (currentVideoSource as any).platform }} 打开
          </button>
          <p class="external-url">{{ (currentVideoSource as any).originalUrl }}</p>
        </div>

        <div v-if="isDirectVideo && isPaused" class="pause-overlay">
          <span class="pause-icon">▶</span>
        </div>

        <div class="video-overlay-bottom">
          <p v-if="currentVideo.caption" class="overlay-caption">
            {{ currentVideo.caption }}
          </p>
          <p class="overlay-owner">
            <span class="owner-at">@{{ currentVideo.owner_string_id }}</span>
            <span class="owner-sep">·</span>
            <span class="owner-name">{{ currentVideo.owner_display_name }}</span>
          </p>
        </div>

        <div v-if="isDirectVideo && currentSubtitle" class="subtitle-overlay">
          <span class="subtitle-text">{{ currentSubtitle }}</span>
        </div>

        <button
          class="nav-arrow up"
          :disabled="currentIndex <= 0"
          @click.stop="prevVideo"
          :title="i18n.t('video_tab_previous') || 'Previous'"
        >▲</button>
        <button
          class="nav-arrow down"
          :disabled="currentIndex >= videos.length - 1"
          @click.stop="nextVideo"
          :title="i18n.t('video_tab_next') || 'Next'"
        >▼</button>

        <div class="video-counter">
          {{ currentIndex + 1 }} / {{ videos.length }}
        </div>
      </div>

      <template v-if="isEmbedVideo && currentVideo">
        <div class="swipe-zone top" title="向上滚动切换上一条">
          <span class="swipe-hint">↕ 滑动切换 · 上一条</span>
        </div>
        <div class="swipe-zone bottom" title="向下滚动切换下一条">
          <span class="swipe-hint">↕ 滑动切换 · 下一条</span>
        </div>
      </template>
    </main>

    <div v-if="currentVideo && isDirectVideo" class="progress-row">
      <span class="time-text">{{ formatTime(currentTime) }}</span>
      <div class="progress-track" @click="onSeek">
        <div class="progress-fill" :style="{ width: progressPct + '%' }">
          <div class="progress-thumb" :style="{ left: progressPct + '%' }"></div>
        </div>
      </div>
      <span class="time-text remaining">-{{ formatTime(remainingTime) }}</span>
    </div>

    <footer v-if="currentVideo" class="bottom-bar">
      <button class="avatar-btn" @click="onAvatarClick">
        <img
          v-if="currentVideo.owner_avatar_url"
          :src="currentVideo.owner_avatar_url"
          alt="avatar"
        />
        <span v-else class="avatar-fallback">
          {{ currentVideo.owner_string_id.slice(-2).toUpperCase() }}
        </span>
      </button>

      <button
        class="action-btn follow-btn"
        :class="{ following: currentVideo.is_following_owner }"
        @click="onToggleFollow"
      >
        {{ currentVideo.is_following_owner ? i18n.t('unfollow') : i18n.t('follow') }}
      </button>

      <button
        class="action-btn icon-action"
        :class="{ active: currentVideo.is_liked }"
        @click="onToggleLike"
      >
        👍<span class="count">{{ currentVideo.like_count }}</span>
      </button>

      <button class="action-btn icon-action" @click="onShare">↗</button>

      <button
        class="action-btn icon-action"
        :class="{ loved: currentVideo.is_loved }"
        @click="onToggleLove"
      >
        ❤<span class="count">{{ currentVideo.love_count }}</span>
      </button>

      <button class="comment-btn" @click="onComment">
        💬 {{ i18n.t('comment_placeholder') }}
      </button>
    </footer>
  </div>
</template>

<style scoped>
.video-page {
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
}
.tab-btn:hover { color: #fff; background: rgba(255, 255, 255, 0.06); }
.tab-btn.active {
  color: var(--gold, #e5b80b);
  background: rgba(229, 184, 11, 0.12);
  font-weight: 600;
}
.tab-icon { font-size: 0.9rem; }

/* ★ Live tab：红点脉冲 */
.live-btn { color: #ff4d4d; }
.live-btn.active {
  color: #fff;
  background: rgba(255, 77, 77, 0.25);
}
.live-dot {
  display: inline-block;
  width: 7px;
  height: 7px;
  border-radius: 50%;
  background: #ff4d4d;
  flex-shrink: 0;
  animation: livePulse 1.2s infinite;
}
@keyframes livePulse {
  0%, 100% { opacity: 1; transform: scale(1); }
  50%      { opacity: 0.4; transform: scale(0.8); }
}

/* ★ Activity tab：金点脉冲 */
.activity-btn { color: #e5b80b; }
.activity-btn.active {
  color: #111;
  background: rgba(229, 184, 11, 0.7);
}
.activity-dot {
  display: inline-block;
  width: 7px;
  height: 7px;
  border-radius: 50%;
  background: #e5b80b;
  flex-shrink: 0;
  animation: livePulse 1.2s infinite;
}

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
.article-btn { border-color: rgba(229, 184, 11, 0.5); }
.article-btn:hover { border-color: var(--gold, #e5b80b); background: rgba(229, 184, 11, 0.12); }

/* 其余样式与你原来的完全一致（略），保持不变即可 */

.player-wrap {
  flex: 1 1 auto;
  min-height: 0;
  position: relative;
  display: flex;
  align-items: center;
  justify-content: center;
  overflow: hidden;
  touch-action: pan-x;
}
.state-layer { text-align: center; color: rgba(255, 255, 255, 0.7); padding: 2rem; }
.state-layer.error { color: #ff8a80; }
.state-layer .hint { font-size: 0.85rem; color: rgba(255, 255, 255, 0.4); margin-top: 0.5rem; }
.state-layer button { margin-top: 1rem; }

.video-stage {
  position: relative;
  width: 100%; height: 100%;
  cursor: pointer;
  display: flex; align-items: center; justify-content: center;
}
.video-el { max-width: 100%; max-height: 100%; object-fit: contain; background: #000; }

.embed-wrap {
  position: relative; width: 100%; height: 100%;
  display: flex; align-items: center; justify-content: center;
  background: #000; cursor: default;
}
.embed-video {
  height: 100%; width: auto;
  aspect-ratio: 16 / 9;
  max-width: 100%; max-height: 100%;
  border: none; background: #000; display: block;
}

.swipe-zone {
  position: absolute; left: 0; right: 0; height: 36px; z-index: 6;
  display: flex; align-items: center; justify-content: center;
  background: linear-gradient(to bottom, rgba(0,0,0,0.55), rgba(0,0,0,0));
  pointer-events: auto; user-select: none; cursor: ns-resize;
}
.swipe-zone.top { top: 0; }
.swipe-zone.bottom {
  bottom: 0;
  background: linear-gradient(to top, rgba(0,0,0,0.55), rgba(0,0,0,0));
}
.swipe-hint { color: rgba(255,255,255,0.6); font-size: 0.7rem; letter-spacing: 0.05em; }

.external-card {
  display: flex; flex-direction: column; align-items: center; justify-content: center;
  gap: 0.75rem; padding: 2rem 1.5rem; max-width: 420px;
  background: #1a1a1a; border: 1px solid rgba(255,255,255,0.1);
  border-radius: 12px; text-align: center; cursor: default;
}
.external-platform { font-size: 0.8rem; color: var(--gold, #e5b80b); font-weight: 700; letter-spacing: 0.05em; text-transform: uppercase; }
.external-icon { font-size: 3rem; opacity: 0.8; }
.external-hint { font-size: 0.85rem; color: rgba(255,255,255,0.65); margin: 0; line-height: 1.5; }
.external-btn { background: #8b5cf6; color: #fff; border: none; border-radius: 8px; padding: 0.65rem 1.5rem; font-weight: 700; font-size: 0.9rem; cursor: pointer; margin-top: 0.25rem; }
.external-btn:hover { background: #7c3aed; }
.external-url { font-size: 0.7rem; color: rgba(255,255,255,0.35); font-family: ui-monospace, monospace; word-break: break-all; max-width: 100%; margin: 0; }

.pause-overlay {
  position: absolute; inset: 0;
  display: flex; align-items: center; justify-content: center;
  background: rgba(0,0,0,0.35); pointer-events: none;
}
.pause-icon { font-size: 4rem; color: rgba(255,255,255,0.85); text-shadow: 0 2px 12px rgba(0,0,0,0.6); }

.video-overlay-bottom {
  position: absolute; left: 0; right: 0; bottom: 0;
  padding: 1.25rem 3.5rem 0.6rem 1rem;
  background: linear-gradient(to top, rgba(0,0,0,0.85) 0%, rgba(0,0,0,0.4) 55%, rgba(0,0,0,0) 100%);
  pointer-events: none; text-shadow: 0 1px 4px rgba(0,0,0,0.9);
}
.overlay-caption { font-size: 0.92rem; font-weight: 600; color: #fff; margin: 0 0 0.15rem; line-height: 1.3; word-break: break-word; }
.overlay-owner { font-size: 0.75rem; color: rgba(255,255,255,0.85); margin: 0; display: flex; gap: 0.3rem; flex-wrap: wrap; }
.owner-at { color: var(--gold, #e5b80b); font-weight: 600; }
.owner-sep { color: rgba(255,255,255,0.4); }
.owner-name { color: rgba(255,255,255,0.85); }

.subtitle-overlay {
  position: absolute; left: 50%; bottom: 3.5rem; transform: translateX(-50%);
  max-width: 90%; background: rgba(0,0,0,0.75);
  border-radius: 6px; padding: 0.35rem 0.8rem;
  pointer-events: none; text-align: center;
}
.subtitle-text { color: #fff; font-size: 0.95rem; line-height: 1.35; font-weight: 500; text-shadow: 0 1px 3px rgba(0,0,0,0.9); word-break: break-word; }

.nav-arrow {
  position: absolute; right: 0.75rem;
  background: rgba(0,0,0,0.55); color: #fff;
  border: 1px solid rgba(255,255,255,0.15);
  width: 40px; height: 40px; border-radius: 50%; font-size: 1rem; cursor: pointer; z-index: 6;
}
.nav-arrow.up { top: 0.75rem; }
.nav-arrow.down { bottom: 0.75rem; }
.nav-arrow:hover:not(:disabled) { border-color: var(--gold, #e5b80b); background: rgba(0,0,0,0.8); }
.nav-arrow:disabled { opacity: 0.25; cursor: not-allowed; }

.video-counter {
  position: absolute; top: 0.6rem; left: 50%; transform: translateX(-50%);
  background: rgba(0,0,0,0.5); color: #fff;
  font-size: 0.72rem; padding: 0.12rem 0.55rem; border-radius: 10px;
  pointer-events: none; z-index: 5;
}

.progress-row {
  display: flex; align-items: center; gap: 0.6rem;
  padding: 0.4rem 1rem; background: rgba(0,0,0,0.9);
  flex: 0 0 auto; border-top: 1px solid rgba(255,255,255,0.06);
}
.time-text { color: rgba(255,255,255,0.75); font-size: 0.78rem; font-family: ui-monospace, monospace; min-width: 42px; text-align: center; flex-shrink: 0; }
.time-text.remaining { color: rgba(255,255,255,0.9); }
.progress-track { flex: 1 1 auto; height: 6px; background: rgba(255,255,255,0.15); border-radius: 3px; position: relative; cursor: pointer; transition: height 0.15s; }
.progress-track:hover { height: 8px; }
.progress-fill { height: 100%; background: var(--gold, #e5b80b); border-radius: 3px; position: relative; transition: width 0.1s linear; }
.progress-thumb { position: absolute; top: 50%; transform: translate(-50%, -50%); width: 14px; height: 14px; background: var(--gold, #e5b80b); border: 2px solid #fff; border-radius: 50%; box-shadow: 0 2px 6px rgba(0,0,0,0.6); pointer-events: none; opacity: 0; transition: opacity 0.15s; }
.progress-track:hover .progress-thumb { opacity: 1; }

.bottom-bar {
  display: flex; align-items: center; justify-content: space-between;
  gap: 0.5rem; padding: 0.5rem 0.9rem;
  background: rgba(0,0,0,0.9); flex: 0 0 auto;
  border-top: 1px solid rgba(255,255,255,0.08);
}
.avatar-btn {
  width: 38px; height: 38px; border-radius: 50%;
  border: 2px solid var(--gold, #e5b80b); background: #333;
  overflow: hidden; cursor: pointer; flex-shrink: 0;
  display: flex; align-items: center; justify-content: center;
  color: #fff; font-weight: 700; font-size: 0.72rem;
}
.avatar-btn img { width: 100%; height: 100%; object-fit: cover; }
.action-btn { background: transparent; border: none; color: #fff; cursor: pointer; display: flex; align-items: center; gap: 0.2rem; padding: 0.3rem 0.45rem; border-radius: 6px; font-size: 1rem; flex-shrink: 0; }
.action-btn:hover { background: rgba(255,255,255,0.08); }
.follow-btn { background: #2ecc71; color: #fff; border: 1px solid #2ecc71; padding: 0.3rem 0.7rem; border-radius: 6px; font-weight: 600; font-size: 0.82rem; }
.follow-btn:hover { background: #27ae60; border-color: #27ae60; }
.follow-btn.following { background: #666; border-color: #666; color: #ddd; }
.icon-action { font-size: 1.1rem; }
.icon-action.active { color: #e5b80b; }
.icon-action.loved { color: #ff5e7e; }
.count { font-size: 0.7rem; color: rgba(255,255,255,0.75); margin-left: 0.1rem; }
.comment-btn {
  flex: 0 0 auto; max-width: 220px;
  background: rgba(255,255,255,0.08);
  border: 1px solid rgba(255,255,255,0.12);
  color: rgba(255,255,255,0.7);
  padding: 0.4rem 0.85rem; border-radius: 20px;
  font-size: 0.83rem; text-align: left; cursor: pointer;
  white-space: nowrap; overflow: hidden; text-overflow: ellipsis;
}
.comment-btn:hover { background: rgba(255,255,255,0.14); color: #fff; }

@media (max-width: 720px) {
  .tab-btn { font-size: 0.85rem; padding: 0.3rem 0.5rem; }
  .top-bar { gap: 0.5rem; padding: 0.4rem 0.7rem; }
  .comment-btn { max-width: 180px; }
  .nav-arrow { width: 36px; height: 36px; }
  .swipe-zone { height: 32px; }
}
@media (max-width: 480px) {
  .tab-label { display: none; }
  .tab-btn { padding: 0.28rem 0.45rem; }
  .tab-icon { font-size: 1rem; }
  .top-bar { padding: 0.28rem 0.5rem; gap: 0.25rem; flex-wrap: nowrap; overflow-x: auto; }
  .top-bar::-webkit-scrollbar { display: none; }
  .icon-btn { width: 28px; height: 28px; font-size: 0.8rem; }
  .right-actions { gap: 0.2rem; flex-shrink: 0; }
  .video-overlay-bottom { padding: 0.7rem 2.4rem 0.4rem 0.5rem; }
  .overlay-caption { font-size: 0.78rem; }
  .overlay-owner { font-size: 0.66rem; }
  .subtitle-overlay { bottom: 3rem; padding: 0.25rem 0.55rem; max-width: 92%; }
  .subtitle-text { font-size: 0.82rem; }
  .nav-arrow { width: 34px; height: 34px; font-size: 0.85rem; }
  .nav-arrow.up { top: 0.5rem; }
  .nav-arrow.down { bottom: 0.5rem; }
  .video-counter { font-size: 0.66rem; padding: 0.1rem 0.45rem; top: 0.4rem; }
  .swipe-zone { height: 30px; }
  .swipe-hint { font-size: 0.62rem; }
  .progress-row { padding: 0.28rem 0.5rem; gap: 0.4rem; }
  .time-text { font-size: 0.68rem; min-width: 34px; }
  .progress-track { height: 5px; }
  .progress-thumb { width: 12px; height: 12px; }
  .bottom-bar { gap: 0.2rem; padding: 0.32rem 0.5rem; flex-wrap: nowrap; overflow-x: auto; }
  .bottom-bar::-webkit-scrollbar { display: none; }
  .avatar-btn { width: 32px; height: 32px; font-size: 0.65rem; }
  .follow-btn { padding: 0.24rem 0.5rem; font-size: 0.7rem; flex-shrink: 0; }
  .action-btn { padding: 0.25rem 0.35rem; font-size: 0.92rem; flex-shrink: 0; }
  .count { display: none; }
  .comment-btn { font-size: 0.7rem; padding: 0.32rem 0.6rem; max-width: 140px; flex-shrink: 0; }
  .external-card { padding: 1.5rem 1rem; }
  .external-icon { font-size: 2.5rem; }
}
@media (max-width: 360px) {
  .follow-btn { font-size: 0.65rem; padding: 0.22rem 0.42rem; }
  .icon-action { font-size: 0.8rem; }
  .comment-btn { max-width: 110px; font-size: 0.66rem; }
}
</style>