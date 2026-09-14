<script setup lang="ts">
import { computed, ref } from 'vue'
import { useRouter } from 'vue-router'
import { useVideosStore } from '@/stores/videos'
import { useI18nStore } from '@/stores/i18n'
import { formatCount, timeAgo, type VideoItem } from '@/data/videos'

const props = defineProps<{
  video: VideoItem
  rank?: number
  showRank?: boolean
  showUploadMeta?: boolean
  showUploaderId?: boolean
}>()

const emit = defineEmits<{
  (e: 'open-comments', id: number): void
}>()

const router = useRouter()
const videos = useVideosStore()
const i18n = useI18nStore()

const isPlaying = ref(false)
const showShareMenu = ref(false)

const liked = computed(() => videos.isLiked(props.video.id))
const hearted = computed(() => videos.isHearted(props.video.id))

function togglePlay() {
  isPlaying.value = !isPlaying.value
}

function toggleLike() {
  videos.like(props.video.id)
}

function toggleHeart() {
  videos.heart(props.video.id)
}

function goPublisher() {
  router.push(`/videos/publisher/${props.video.authorId}`)
}

function openComments() {
  emit('open-comments', props.video.id)
}

async function share() {
  const url = `${window.location.origin}/videos?video=${props.video.id}`
  const payload = {
    title: props.video.title,
    text: `Check out this video by ${props.video.authorId}`,
    url,
  }
  // Try native Web Share (mobile, WeChat in-app browser, etc.)
  if (typeof navigator !== 'undefined' && (navigator as any).share) {
    try {
      await (navigator as any).share(payload)
      showShareMenu.value = false
      return
    } catch {
      /* user cancelled or unsupported */
    }
  }
  showShareMenu.value = !showShareMenu.value
}

async function shareToWeChat() {
  // WeChat deep link scheme — works on mobile browsers
  const url = `${window.location.origin}/videos?video=${props.video.id}`
  const title = encodeURIComponent(props.video.title)
  window.location.href = `weixin://dl/business/?t=${title}&u=${encodeURIComponent(url)}`
  showShareMenu.value = false
  // Fallback: also copy to clipboard
  try {
    await navigator.clipboard.writeText(url)
  } catch { /* ignore */ }
}

async function copyLink() {
  const url = `${window.location.origin}/videos?video=${props.video.id}`
  try {
    await navigator.clipboard.writeText(url)
    alert(i18n.t('link_copied') || 'Link copied')
  } catch {
    /* ignore */
  }
  showShareMenu.value = false
}
</script>

<template>
  <article class="video-card">
    <!-- Video surface (placeholder) -->
    <div
      class="video-surface"
      :style="{
        background: `linear-gradient(150deg, hsl(${video.hue},50%,28%), hsl(${video.hue},60%,12%))`,
      }"
      @click="togglePlay"
    >
      <!-- Play / pause icon -->
      <div class="play-icon" :class="{ hidden: isPlaying }">▶</div>

      <!-- Simulated playing animation -->
      <div v-if="isPlaying" class="playing-bars">
        <span /><span /><span /><span /><span />
      </div>

      <!-- Top-left overlay: rank + views (Best tab) -->
      <div v-if="showRank" class="overlay top-left">
        <div class="rank-badge">#{{ rank }}</div>
        <div class="views-badge">
          {{ formatCount(video.views) }} {{ i18n.t('views') }}
        </div>
      </div>

      <!-- Top-right overlay: upload time + author id (Latest tab) -->
      <div v-if="showUploadMeta" class="overlay top-right">
        <div class="time-badge">{{ timeAgo(video.uploadedAt) }}</div>
        <div v-if="showUploaderId" class="author-badge">
          @{{ video.authorId }}
        </div>
      </div>

      <!-- Bottom overlay: title + duration -->
      <div class="overlay bottom-left">
        <div class="video-title">{{ video.title }}</div>
        <div class="video-desc">{{ video.description }}</div>
      </div>

      <div class="duration">{{ video.durationSec }}s</div>
    </div>

    <!-- Action bar -->
    <div class="action-bar">
      <!-- Publisher button: avatar + ID -->
      <button class="publisher-btn" @click.stop="goPublisher">
        <span
          class="avatar"
          :style="{
            background: `hsl(${video.authorHue},60%,45%)`,
          }"
        >
          {{ video.authorId.slice(-2) }}
        </span>
        <span class="publisher-id">{{ video.authorId }}</span>
      </button>

      <div class="spacer" />

      <!-- Like (thumbs-up) -->
      <button class="action-btn" :class="{ active: liked }" @click.stop="toggleLike">
        <span class="icon">👍</span>
        <span class="count">{{ formatCount(video.likes) }}</span>
      </button>

      <!-- Heart -->
      <button
        class="action-btn"
        :class="{ active: hearted }"
        @click.stop="toggleHeart"
      >
        <span class="icon">❤️</span>
        <span class="count">{{ formatCount(video.hearts) }}</span>
      </button>

      <!-- Share -->
      <div class="share-wrap">
        <button class="action-btn" @click.stop="share">
          <span class="icon">↗️</span>
          <span class="count">{{ i18n.t('share') }}</span>
        </button>

        <div v-if="showShareMenu" class="share-menu" @click.stop>
          <button @click="shareToWeChat">微信</button>
          <button @click="shareToWeChat">朋友圈</button>
          <button @click="copyLink">{{ i18n.t('copy_link') }}</button>
        </div>
      </div>

      <!-- Comments -->
      <button class="action-btn" @click.stop="openComments">
        <span class="icon">💬</span>
        <span class="count">{{ formatCount(video.commentCount) }}</span>
      </button>
    </div>
  </article>
</template>

<style scoped>
.video-card {
  position: relative;
  height: 100%;
  display: flex;
  flex-direction: column;
  scroll-snap-align: start;
  background: #000;
}

/* ---------- Video surface ---------- */
.video-surface {
  position: relative;
  flex: 1;
  cursor: pointer;
  overflow: hidden;
  user-select: none;
}

.play-icon {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  font-size: 3rem;
  color: rgba(255, 255, 255, 0.75);
  text-shadow: 0 2px 12px rgba(0, 0, 0, 0.6);
  transition: opacity 0.2s;
  pointer-events: none;
}
.play-icon.hidden {
  opacity: 0;
}

.playing-bars {
  position: absolute;
  bottom: 1.25rem;
  left: 50%;
  transform: translateX(-50%);
  display: flex;
  align-items: flex-end;
  gap: 3px;
  height: 18px;
}
.playing-bars span {
  width: 3px;
  background: var(--gold);
  border-radius: 2px;
  animation: bar 0.9s ease-in-out infinite;
}
.playing-bars span:nth-child(1) { animation-delay: 0.0s; }
.playing-bars span:nth-child(2) { animation-delay: 0.15s; }
.playing-bars span:nth-child(3) { animation-delay: 0.3s; }
.playing-bars span:nth-child(4) { animation-delay: 0.45s; }
.playing-bars span:nth-child(5) { animation-delay: 0.6s; }

@keyframes bar {
  0%, 100% { height: 4px; }
  50% { height: 16px; }
}

/* ---------- Overlays ---------- */
.overlay {
  position: absolute;
  display: flex;
  flex-direction: column;
  gap: 0.35rem;
  pointer-events: none;
}
.top-left {
  top: 0.85rem;
  left: 0.85rem;
}
.top-right {
  top: 0.85rem;
  right: 0.85rem;
  align-items: flex-end;
}
.bottom-left {
  left: 0.85rem;
  right: 0.85rem;
  bottom: 0.85rem;
}

.rank-badge {
  display: inline-block;
  padding: 0.15rem 0.55rem;
  background: var(--gold);
  color: #111;
  border-radius: 4px;
  font-weight: 800;
  font-size: 0.85rem;
  width: fit-content;
}
.views-badge,
.time-badge,
.author-badge {
  display: inline-block;
  padding: 0.2rem 0.5rem;
  background: rgba(0, 0, 0, 0.55);
  color: #fff;
  border-radius: 4px;
  font-size: 0.78rem;
  width: fit-content;
  backdrop-filter: blur(4px);
}
.author-badge {
  color: var(--gold);
  font-weight: 600;
}

.video-title {
  color: #fff;
  font-size: 1rem;
  font-weight: 700;
  text-shadow: 0 1px 4px rgba(0, 0, 0, 0.8);
  margin-bottom: 0.2rem;
}
.video-desc {
  color: rgba(255, 255, 255, 0.8);
  font-size: 0.82rem;
  text-shadow: 0 1px 4px rgba(0, 0, 0, 0.8);
}
.duration {
  position: absolute;
  bottom: 0.85rem;
  right: 0.85rem;
  padding: 0.15rem 0.45rem;
  background: rgba(0, 0, 0, 0.65);
  color: #fff;
  border-radius: 4px;
  font-size: 0.72rem;
}

/* ---------- Action bar ---------- */
.action-bar {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.6rem 0.85rem;
  background: #0d0d0d;
  border-top: 1px solid #222;
}

.publisher-btn {
  display: inline-flex;
  align-items: center;
  gap: 0.5rem;
  background: transparent;
  border: none;
  color: #fff;
  cursor: pointer;
  padding: 0.15rem 0.35rem;
  border-radius: 20px;
  transition: background 0.15s;
}
.publisher-btn:hover {
  background: rgba(255, 255, 255, 0.08);
}
.avatar {
  width: 32px;
  height: 32px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #fff;
  font-weight: 700;
  font-size: 0.75rem;
  border: 2px solid var(--gold);
}
.publisher-id {
  font-size: 0.85rem;
  color: #fff;
}

.spacer {
  flex: 1;
}

.action-btn {
  display: inline-flex;
  align-items: center;
  gap: 0.3rem;
  background: transparent;
  border: none;
  color: #ccc;
  cursor: pointer;
  padding: 0.35rem 0.55rem;
  border-radius: 6px;
  font-size: 0.8rem;
  transition: background 0.15s, color 0.15s;
}
.action-btn:hover {
  background: rgba(255, 255, 255, 0.08);
  color: #fff;
}
.action-btn.active {
  color: var(--gold);
}
.action-btn .icon {
  font-size: 1.05rem;
}

/* ---------- Share menu ---------- */
.share-wrap {
  position: relative;
}
.share-menu {
  position: absolute;
  bottom: 110%;
  right: 0;
  background: #1e1e1e;
  border: 1px solid var(--border);
  border-radius: 6px;
  padding: 0.35rem;
  display: flex;
  flex-direction: column;
  gap: 0.2rem;
  min-width: 120px;
  z-index: 20;
}
.share-menu button {
  background: transparent;
  border: none;
  color: var(--text);
  padding: 0.4rem 0.75rem;
  text-align: left;
  cursor: pointer;
  border-radius: 4px;
  font-size: 0.82rem;
}
.share-menu button:hover {
  background: rgba(229, 184, 11, 0.15);
  color: var(--gold);
}
</style>