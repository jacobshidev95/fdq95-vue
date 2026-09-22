<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useI18nStore } from '@/stores/i18n'

const route = useRoute()
const router = useRouter()
const i18n = useI18nStore()

// ──────────────────────────────────────────────
// 状态
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

// 角色
const isModerator = computed(() => route.query.role === 'moderator')

// ──────────────────────────────────────────────
// 嵌入式 URL
// ──────────────────────────────────────────────
// ★ 视频会议：直接指向 /remote/ 登录页
const VIDEO_CALL_BASE = import.meta.env.VITE_VIDEO_CALL_URL
  || 'https://video-call.fdq95.com'
const videoCallUrl = computed(() => `${VIDEO_CALL_BASE}/remote/`)

// ★ 场地相机
const FIELD_CAMERA_URL = import.meta.env.VITE_FIELD_CAMERA_URL
  || 'https://webcam.fdq95.com'

// ──────────────────────────────────────────────
// 观众文字
// ──────────────────────────────────────────────
const chatMessage = ref('')
const chatMessages = ref<Array<{ from: string; text: string; time: string }>>([])

function sendChatMessage() {
  const text = chatMessage.value.trim()
  if (!text) return
  chatMessages.value.push({
    from: i18n.t('live_you') || 'You',
    text,
    time: new Date().toLocaleTimeString(),
  })
  chatMessage.value = ''
  // TODO: WebSocket / SSE 发送
}

// ──────────────────────────────────────────────
// 5 个按钮
// ──────────────────────────────────────────────
function onGift()  { console.log('[Live] Gift') }
function onEmoji() { console.log('[Live] Emoji') }
function onCall()  { console.log('[Live] Call') }
function onShare() {
  if (navigator.clipboard) navigator.clipboard.writeText(window.location.href)
}
function onLike()  { console.log('[Live] Like') }

// ──────────────────────────────────────────────
// 导航
// ──────────────────────────────────────────────
function goBack() { router.back() }

onMounted(() => {
  // 保持页面占满视口，无滚动
  document.documentElement.style.overflow = 'hidden'
  document.body.style.overflow = 'hidden'
})
</script>

<template>
  <div class="live-page">
    <!-- ── 顶部：返回 + 标题（单独一排） ── -->
    <div class="title-row">
      <button type="button" class="back-btn" @click="goBack">‹</button>
      <input
        v-model="liveTitle"
        type="text"
        class="live-title-input"
        :placeholder="i18n.t('live_title_ph') || 'Enter live title'"
        maxlength="120"
      />
      <div class="role-badge" :class="{ moderator: isModerator }">
        {{ isModerator
          ? (i18n.t('live_moderator') || 'Host')
          : (i18n.t('live_viewer') || 'Viewer') }}
      </div>
    </div>

    <!-- ── 类别（单独一排） ── -->
    <div class="category-row">
      <select v-model="liveCategory" class="live-category-select">
        <option :value="null" disabled>
          {{ i18n.t('live_category') || 'Category' }}
        </option>
        <option v-for="c in CATEGORIES" :key="c.value" :value="c.value">
          {{ c.key }}
        </option>
      </select>
    </div>

    <!-- ── 主体：左视频会议 + 右场地相机/观众输入 ── -->
    <main class="live-body">
      <!-- 左列 -->
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

      <!-- 右列 -->
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
/* ──────────────────────────────────────────────
   整页布局：满屏、无滚动
   ────────────────────────────────────────────── */
.live-page {
  display: flex;
  flex-direction: column;
  width: 100vw;
  height: 100vh;
  background: #000;
  color: #fff;
  overflow: hidden;
  box-sizing: border-box;
}

/* ── 第一排：返回 + 标题 ── */
.title-row {
  display: flex;
  align-items: center;
  gap: 0.6rem;
  padding: 0.5rem 0.8rem;
  background: #0d0d0d;
  border-bottom: 1px solid #222;
  flex-shrink: 0;
}
.back-btn {
  background: transparent;
  border: none;
  color: #fff;
  font-size: 1.8rem;
  line-height: 1;
  cursor: pointer;
  padding: 0 0.2rem;
  flex-shrink: 0;
}
.live-title-input {
  flex: 1;
  min-width: 0;
  background: #1a1a1a;
  border: 1px solid #333;
  border-radius: 8px;
  color: #fff;
  padding: 0.4rem 0.7rem;
  font-size: 0.95rem;
  font-weight: 600;
}
.live-title-input:focus { outline: none; border-color: #8b5cf6; }
.role-badge {
  padding: 0.2rem 0.6rem;
  border-radius: 12px;
  font-size: 0.72rem;
  font-weight: 600;
  background: rgba(255, 255, 255, 0.1);
  color: rgba(255, 255, 255, 0.7);
  flex-shrink: 0;
}
.role-badge.moderator {
  background: rgba(229, 184, 11, 0.2);
  color: #e5b80b;
  border: 1px solid #e5b80b;
}

/* ── 第二排：类别 ── */
.category-row {
  padding: 0.4rem 0.8rem;
  background: #0d0d0d;
  border-bottom: 1px solid #222;
  flex-shrink: 0;
}
.live-category-select {
  background: #1a1a1a;
  border: 1px solid #333;
  border-radius: 8px;
  color: #fff;
  padding: 0.35rem 0.6rem;
  font-size: 0.85rem;
  width: 100%;
  max-width: 220px;
}

/* ── 主体：左右两列 ── */
.live-body {
  display: grid;
  grid-template-columns: 3fr 2fr;
  gap: 0.5rem;
  padding: 0.5rem;
  flex: 1 1 auto;
  min-height: 0;
  overflow: hidden;
}

/* 左列 */
.left-col {
  display: flex;
  flex-direction: column;
  gap: 0.4rem;
  min-height: 0;
}
.video-frame {
  flex: 1 1 auto;
  min-height: 0;
  background: #000;
  border-radius: 10px;
  overflow: hidden;
  border: 1px solid #222;
}
.video-call-iframe {
  width: 100%;
  height: 100%;
  display: block;
  border: 0;
}

.action-bar {
  display: flex;
  gap: 0.35rem;
  padding: 0.3rem;
  background: #111;
  border-radius: 8px;
  flex-shrink: 0;
}
.action-btn {
  flex: 1 1 auto;
  min-width: 0;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 0.1rem;
  padding: 0.35rem 0.2rem;
  background: rgba(255, 255, 255, 0.05);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 6px;
  color: #fff;
  cursor: pointer;
  transition: all 0.15s;
}
.action-btn:hover {
  background: rgba(139, 92, 246, 0.15);
  border-color: #8b5cf6;
}
.action-btn .icon { font-size: 1.1rem; }
.action-btn .label {
  font-size: 0.68rem;
  color: rgba(255, 255, 255, 0.75);
}
.action-btn.like:hover {
  background: rgba(231, 76, 60, 0.15);
  border-color: #e74c3c;
}

/* 右列 */
.right-col {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
  min-height: 0;
}
.field-camera-frame {
  flex: 0 0 auto;
  aspect-ratio: 16 / 9;
  background: #000;
  border-radius: 10px;
  overflow: hidden;
  border: 1px solid #222;
}
.field-camera-iframe {
  width: 100%;
  height: 100%;
  display: block;
  border: 0;
}

.audience-panel {
  flex: 1 1 auto;
  min-height: 0;
  display: flex;
  flex-direction: column;
  background: #111;
  border-radius: 10px;
  border: 1px solid #222;
  overflow: hidden;
}
.audience-messages {
  flex: 1 1 auto;
  min-height: 0;
  overflow-y: auto;
  padding: 0.5rem 0.7rem;
  display: flex;
  flex-direction: column;
  gap: 0.3rem;
}
.empty-hint {
  color: rgba(255, 255, 255, 0.35);
  font-size: 0.8rem;
  text-align: center;
  padding: 0.8rem 0;
}
.audience-msg {
  font-size: 0.82rem;
  line-height: 1.35;
  word-break: break-word;
}
.msg-from { color: #c4b5fd; font-weight: 600; margin-right: 0.25rem; }
.msg-text { color: #fff; }
.msg-time {
  color: rgba(255, 255, 255, 0.35);
  font-size: 0.68rem;
  margin-left: 0.35rem;
}
.audience-input-row {
  display: flex;
  gap: 0.35rem;
  padding: 0.4rem 0.5rem;
  background: #0d0d0d;
  border-top: 1px solid #222;
  flex-shrink: 0;
}
.audience-input {
  flex: 1;
  min-width: 0;
  background: #1a1a1a;
  border: 1px solid #333;
  border-radius: 6px;
  color: #fff;
  padding: 0.4rem 0.6rem;
  font-size: 0.85rem;
}
.audience-input:focus { outline: none; border-color: #8b5cf6; }
.send-btn {
  background: #8b5cf6;
  color: #fff;
  border: none;
  border-radius: 6px;
  padding: 0 0.85rem;
  font-weight: 600;
  font-size: 0.82rem;
  cursor: pointer;
}
.send-btn:disabled { opacity: 0.4; cursor: not-allowed; }

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
    max-height: 260px;
  }
}

@media (max-width: 600px) {
  .live-body {
    grid-template-columns: 1fr;
    gap: 0.4rem;
    padding: 0.4rem;
  }
  .right-col { flex-direction: column; }
  .action-btn .label { font-size: 0.6rem; }
  .action-btn .icon { font-size: 0.95rem; }
  .category-row { padding: 0.35rem 0.5rem; }
  .title-row { padding: 0.4rem 0.5rem; }
}
</style>