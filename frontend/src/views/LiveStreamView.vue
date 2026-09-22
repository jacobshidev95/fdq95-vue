<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useI18nStore } from '@/stores/i18n'
import { api } from '@/api/client'

const route = useRoute()
const router = useRouter()
const i18n = useI18nStore()

// ──────────────────────────────────────────────
// 页面状态
// ──────────────────────────────────────────────
type LiveCategory =
  | 'medical' | 'health' | 'education' | 'entertainment' | 'travel'
  | 'food' | 'clothing' | 'industry' | 'tech' | 'iot' | 'life' | 'ai'

const CATEGORIES: { value: LiveCategory; key: string }[] = [
  { value: 'medical',       key: 'Medical' },
  { value: 'health',        key: 'Health' },
  { value: 'education',     key: 'Education' },
  { value: 'entertainment', key: 'Entertainment' },
  { value: 'travel',        key: 'Travel' },
  { value: 'food',          key: 'Food' },
  { value: 'clothing',      key: 'Clothing' },
  { value: 'industry',      key: 'Industry' },
  { value: 'tech',          key: 'Technology' },
  { value: 'iot',           key: 'IoT' },
  { value: 'life',          key: 'Life' },
  { value: 'ai',            key: 'AI' },
]

const liveTitle = ref('')
const liveCategory = ref<LiveCategory | null>(null)

// ★ 从 URL 参数读取：role / user / pass / room
//   主持人：/live?role=moderator&user=admin&pass=xxx&room=xxx
//   观众：  /live?room=xxx
const isModerator = computed(() => route.query.role === 'moderator')
const moderatorUser = computed(() => String(route.query.user || ''))
const moderatorPass = computed(() => String(route.query.pass || ''))
const roomName = ref(
  String(route.query.room || `fdq95-live-${Math.random().toString(36).slice(2, 10)}`),
)

// ──────────────────────────────────────────────
// 嵌入配置
// ──────────────────────────────────────────────
// ★ 视频会议 iframe（你的 Jitsi 部署）
const VIDEO_CALL_BASE = import.meta.env.VITE_VIDEO_CALL_URL
  || 'https://video-call.fdq95.com'

// ★ 场地相机 iframe（第二个相机）
const FIELD_CAMERA_URL = import.meta.env.VITE_FIELD_CAMERA_URL
  || 'https://webcam.fdq95.com'

// 拼接 video-call 的 URL（带房间名和角色参数）
const videoCallUrl = computed(() => {
  const params = new URLSearchParams()
  params.set('room', roomName.value)
  if (isModerator.value) {
    params.set('role', 'moderator')
    if (moderatorUser.value) params.set('user', moderatorUser.value)
    if (moderatorPass.value) params.set('pass', moderatorPass.value)
  }
  // Jitsi 原生的 URL 参数（供 video-call 页面转发给 Jitsi）
  params.set('jitsiRoom', roomName.value)
  return `${VIDEO_CALL_BASE}/?${params.toString()}`
})

// ──────────────────────────────────────────────
// 观众文字输入
// ──────────────────────────────────────────────
const chatMessage = ref('')
const chatMessages = ref<Array<{ from: string; text: string; time: string }>>([])

async function sendChatMessage() {
  const text = chatMessage.value.trim()
  if (!text) return

  chatMessages.value.push({
    from: i18n.t('live_you') || 'You',
    text,
    time: new Date().toLocaleTimeString(),
  })
  chatMessage.value = ''

  // TODO: 通过 WebSocket / SSE 发送到直播室
  // await api.post('/api/live/chat', { room: roomName.value, text })
}

// ──────────────────────────────────────────────
// 5 个操作按钮（占位，功能页后续开发）
// ──────────────────────────────────────────────
function onGift() {
  console.log('[LiveStream] Gift clicked')
  // TODO: 打开礼物面板
}
function onEmoji() {
  console.log('[LiveStream] Emoji clicked')
  // TODO: 打开表情面板
}
function onCall() {
  console.log('[LiveStream] Call clicked')
  // TODO: 打开通话
}
function onShare() {
  console.log('[LiveStream] Share clicked')
  if (navigator.clipboard) {
    navigator.clipboard.writeText(window.location.href)
  }
}
function onLike() {
  console.log('[LiveStream] Like clicked')
  // TODO: 发送点赞到后端
}

// ──────────────────────────────────────────────
// 导航
// ──────────────────────────────────────────────
function goBack() {
  router.back()
}
</script>

<template>
  <div class="live-page">
    <!-- 顶部栏 -->
    <header class="top-bar">
      <button type="button" class="back-btn" @click="goBack">‹</button>
      <div class="top-fields">
        <input
          v-model="liveTitle"
          type="text"
          class="live-title-input"
          :placeholder="i18n.t('live_title_ph') || 'Enter live title'"
          maxlength="120"
        />
        <select v-model="liveCategory" class="live-category-select">
          <option :value="null" disabled>
            {{ i18n.t('live_category') || 'Category' }}
          </option>
          <option v-for="c in CATEGORIES" :key="c.value" :value="c.value">
            {{ c.key }}
          </option>
        </select>
      </div>
      <div class="role-badge" :class="{ moderator: isModerator }">
        {{ isModerator
          ? (i18n.t('live_moderator') || 'Host')
          : (i18n.t('live_viewer') || 'Viewer') }}
      </div>
    </header>

    <!-- 主体 -->
    <main class="live-body">
      <!-- 左列：视频会议 + 操作按钮 -->
      <section class="left-col">
        <div class="video-frame">
          <iframe
            :src="videoCallUrl"
            class="video-call-iframe"
            frameborder="0"
            allow="camera; microphone; fullscreen; display-capture; autoplay; clipboard-write"
            sandbox="allow-same-origin allow-scripts allow-forms allow-popups allow-modals"
          />
        </div>

        <!-- 5 个操作按钮 -->
        <div class="action-bar">
          <button type="button" class="action-btn" @click="onGift">
            <span class="icon">🎁</span>
            <span class="label">{{ i18n.t('live_btn_gift') || 'Gift' }}</span>
          </button>
          <button type="button" class="action-btn" @click="onEmoji">
            <span class="icon">😊</span>
            <span class="label">{{ i18n.t('live_btn_emoji') || 'Emoji' }}</span>
          </button>
          <button type="button" class="action-btn" @click="onCall">
            <span class="icon">📞</span>
            <span class="label">{{ i18n.t('live_btn_call') || 'Call' }}</span>
          </button>
          <button type="button" class="action-btn" @click="onShare">
            <span class="icon">📤</span>
            <span class="label">{{ i18n.t('live_btn_share') || 'Share' }}</span>
          </button>
          <button type="button" class="action-btn like" @click="onLike">
            <span class="icon">❤️</span>
            <span class="label">{{ i18n.t('live_btn_like') || 'Like' }}</span>
          </button>
        </div>
      </section>

      <!-- 右列：场地相机 + 观众输入 -->
      <aside class="right-col">
        <div class="field-camera-frame">
          <iframe
            :src="FIELD_CAMERA_URL"
            class="field-camera-iframe"
            frameborder="0"
            allow="camera; microphone; fullscreen; autoplay"
            sandbox="allow-same-origin allow-scripts allow-forms allow-popups"
          />
        </div>

        <div class="audience-panel">
          <div class="audience-messages">
            <div v-if="chatMessages.length === 0" class="empty-hint">
              {{ i18n.t('live_no_messages') || 'No messages yet' }}
            </div>
            <div
              v-for="(msg, idx) in chatMessages"
              :key="idx"
              class="audience-msg"
            >
              <span class="msg-from">{{ msg.from }}:</span>
              <span class="msg-text">{{ msg.text }}</span>
              <span class="msg-time">{{ msg.time }}</span>
            </div>
          </div>
          <div class="audience-input-row">
            <input
              v-model="chatMessage"
              type="text"
              class="audience-input"
              :placeholder="i18n.t('live_input_ph') || 'Say something…'"
              @keyup.enter="sendChatMessage"
            />
            <button
              type="button"
              class="send-btn"
              :disabled="!chatMessage.trim()"
              @click="sendChatMessage"
            >
              {{ i18n.t('live_send') || 'Send' }}
            </button>
          </div>
        </div>
      </aside>
    </main>
  </div>
</template>

<style scoped>
.live-page {
  display: flex;
  flex-direction: column;
  width: 100%;
  min-height: 100vh;
  background: #000;
  color: #fff;
}

/* ── 顶部栏 ── */
.top-bar {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  padding: 0.6rem 1rem;
  background: #0d0d0d;
  border-bottom: 1px solid #222;
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
  padding: 0 0.25rem;
}
.top-fields {
  display: flex;
  gap: 0.6rem;
  flex: 1;
  min-width: 0;
}
.live-title-input {
  flex: 1;
  min-width: 0;
  background: #1a1a1a;
  border: 1px solid #333;
  border-radius: 8px;
  color: #fff;
  padding: 0.45rem 0.8rem;
  font-size: 0.95rem;
  font-weight: 600;
}
.live-category-select {
  background: #1a1a1a;
  border: 1px solid #333;
  border-radius: 8px;
  color: #fff;
  padding: 0.45rem 0.6rem;
  font-size: 0.85rem;
  min-width: 130px;
}
.role-badge {
  padding: 0.25rem 0.7rem;
  border-radius: 12px;
  font-size: 0.75rem;
  font-weight: 600;
  background: rgba(255, 255, 255, 0.1);
  color: rgba(255, 255, 255, 0.7);
}
.role-badge.moderator {
  background: rgba(229, 184, 11, 0.2);
  color: #e5b80b;
  border: 1px solid #e5b80b;
}

/* ── 主体 ── */
.live-body {
  display: grid;
  grid-template-columns: 3fr 2fr;
  gap: 0.75rem;
  padding: 0.75rem;
  flex: 1;
  min-height: 0;
}

/* ── 左列 ── */
.left-col {
  display: flex;
  flex-direction: column;
  gap: 0.6rem;
  min-height: 0;
}
.video-frame {
  flex: 1;
  min-height: 60vh;
  background: #000;
  border-radius: 12px;
  overflow: hidden;
  border: 1px solid #222;
}
.video-call-iframe {
  width: 100%;
  height: 100%;
  min-height: 60vh;
  display: block;
}

.action-bar {
  display: flex;
  gap: 0.4rem;
  padding: 0.4rem;
  background: #111;
  border-radius: 10px;
  flex-wrap: wrap;
}
.action-btn {
  flex: 1 1 auto;
  min-width: 70px;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 0.15rem;
  padding: 0.45rem 0.3rem;
  background: rgba(255, 255, 255, 0.05);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 8px;
  color: #fff;
  cursor: pointer;
  transition: all 0.15s;
}
.action-btn:hover {
  background: rgba(139, 92, 246, 0.15);
  border-color: #8b5cf6;
}
.action-btn .icon {
  font-size: 1.2rem;
}
.action-btn .label {
  font-size: 0.7rem;
  color: rgba(255, 255, 255, 0.75);
}
.action-btn.like:hover {
  background: rgba(231, 76, 60, 0.15);
  border-color: #e74c3c;
}

/* ── 右列 ── */
.right-col {
  display: flex;
  flex-direction: column;
  gap: 0.6rem;
  min-height: 0;
}
.field-camera-frame {
  aspect-ratio: 16 / 9;
  background: #000;
  border-radius: 12px;
  overflow: hidden;
  border: 1px solid #222;
}
.field-camera-iframe {
  width: 100%;
  height: 100%;
  display: block;
}

/* ── 观众文字区 ── */
.audience-panel {
  flex: 1;
  min-height: 0;
  display: flex;
  flex-direction: column;
  background: #111;
  border-radius: 12px;
  border: 1px solid #222;
  overflow: hidden;
}
.audience-messages {
  flex: 1;
  min-height: 0;
  overflow-y: auto;
  padding: 0.7rem 0.85rem;
  display: flex;
  flex-direction: column;
  gap: 0.4rem;
}
.empty-hint {
  color: rgba(255, 255, 255, 0.35);
  font-size: 0.85rem;
  text-align: center;
  padding: 1rem 0;
}
.audience-msg {
  font-size: 0.85rem;
  line-height: 1.4;
  word-break: break-word;
}
.msg-from {
  color: #c4b5fd;
  font-weight: 600;
  margin-right: 0.3rem;
}
.msg-text {
  color: #fff;
}
.msg-time {
  color: rgba(255, 255, 255, 0.35);
  font-size: 0.7rem;
  margin-left: 0.4rem;
}
.audience-input-row {
  display: flex;
  gap: 0.4rem;
  padding: 0.55rem;
  background: #0d0d0d;
  border-top: 1px solid #222;
}
.audience-input {
  flex: 1;
  min-width: 0;
  background: #1a1a1a;
  border: 1px solid #333;
  border-radius: 8px;
  color: #fff;
  padding: 0.5rem 0.75rem;
  font-size: 0.9rem;
}
.audience-input:focus {
  outline: none;
  border-color: #8b5cf6;
}
.send-btn {
  background: #8b5cf6;
  color: #fff;
  border: none;
  border-radius: 8px;
  padding: 0 1rem;
  font-weight: 600;
  cursor: pointer;
}
.send-btn:disabled {
  opacity: 0.4;
  cursor: not-allowed;
}

/* ──────────────────────────────────────────────
   响应式
   ────────────────────────────────────────────── */
@media (max-width: 900px) {
  .live-body {
    grid-template-columns: 1fr;
  }
  .right-col {
    flex-direction: row;
    align-items: flex-start;
  }
  .field-camera-frame {
    flex: 1;
  }
  .audience-panel {
    flex: 1;
    max-height: 320px;
  }
}

@media (max-width: 600px) {
  .live-body {
    grid-template-columns: 1fr;
    gap: 0.5rem;
    padding: 0.5rem;
  }
  .right-col {
    flex-direction: column;
  }
  .video-frame {
    min-height: 45vh;
  }
  .video-call-iframe {
    min-height: 45vh;
  }
  .top-fields {
    flex-direction: column;
    gap: 0.3rem;
  }
  .action-bar {
    gap: 0.3rem;
  }
  .action-btn {
    min-width: 56px;
    padding: 0.35rem 0.2rem;
  }
  .action-btn .label {
    font-size: 0.62rem;
  }
}
</style>