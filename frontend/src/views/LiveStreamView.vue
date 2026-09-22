<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useI18nStore } from '@/stores/i18n'

const route = useRoute()
const router = useRouter()
const i18n = useI18nStore()

// ──────────────────────────────────────────────
// 类别
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

// ──────────────────────────────────────────────
// 标题 / 类别：localStorage 记忆
// ──────────────────────────────────────────────
const TITLE_STORAGE_KEY = 'fdq95_live_title'
const CATEGORY_STORAGE_KEY = 'fdq95_live_category'

const liveTitle = ref(localStorage.getItem(TITLE_STORAGE_KEY) || '')
const liveCategory = ref<LiveCategory | null>(
  (localStorage.getItem(CATEGORY_STORAGE_KEY) as LiveCategory) || null
)
watch(liveTitle, (v) => localStorage.setItem(TITLE_STORAGE_KEY, v))
watch(liveCategory, (v) => { if (v) localStorage.setItem(CATEGORY_STORAGE_KEY, v) })

// ──────────────────────────────────────────────
// 角色
// ──────────────────────────────────────────────
const isModerator = computed(() => route.query.role === 'moderator')

// ──────────────────────────────────────────────
// 嵌入式 URL
// ──────────────────────────────────────────────
const VIDEO_CALL_BASE = import.meta.env.VITE_VIDEO_CALL_URL
  || 'https://video-call.fdq95.com'
const videoCallUrl = computed(() => `${VIDEO_CALL_BASE}/remote`)

const FIELD_CAMERA_BASE = import.meta.env.VITE_FIELD_CAMERA_URL
  || 'https://webcam.fdq95.com'

// ★ 主持人 → 完整控制面板；观众 → 只读视图
//   如果 webcam 不支持参数，改成 `${FIELD_CAMERA_BASE}` 并靠 CSS 隐藏控制
const fieldCameraUrl = computed(() => {
  if (isModerator.value) return FIELD_CAMERA_BASE
  return `${FIELD_CAMERA_BASE}?readonly=1`
})

// 观众视角下用 CSS 遮住底部控制区（后备方案）
const fieldCameraWrapClass = computed(() => ({
  'field-camera-frame': true,
  'viewer-mode': !isModerator.value,
}))

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
// 导航 / 生命周期
// ──────────────────────────────────────────────
function goBack() { router.back() }

onMounted(() => {
  document.documentElement.style.overflow = 'hidden'
  document.body.style.overflow = 'hidden'
})
onBeforeUnmount(() => {
  document.documentElement.style.overflow = ''
  document.body.style.overflow = ''
})
</script>

<template>
  <div class="live-page">
    <!-- 顶部：标题 + 类别（紧凑两排） -->
    <div class="live-top">
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
    </div>

    <!-- 主体（可滚动区域） -->
    <main class="live-body">
      <section class="left-col">
        <div class="video-frame">
          <iframe
            :key="videoCallUrl"
            :src="videoCallUrl"
            class="video-call-iframe"
            frameborder="0"
            allow="camera; microphone; fullscreen; display-capture; autoplay; clipboard-write"
            sandbox="allow-same-origin allow-scripts allow-forms allow-popups allow-modals"
          />
        </div>
      </section>

      <aside class="right-col">
        <div :class="fieldCameraWrapClass">
          <iframe
            :src="fieldCameraUrl"
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
        </div>
      </aside>
    </main>

    <!-- ★ 底部固定操作栏：5 个按钮 + 文字输入（不再被挤掉） -->
    <footer class="live-footer">
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
    </footer>
  </div>
</template>

<style scoped>
/* ──────────────────────────────────────────────
   整页布局：满屏 + 上下固定 + 中间滚动
   ────────────────────────────────────────────── */
.live-page {
  display: flex;
  flex-direction: column;
  width: 100vw;
  height: 100vh;
  height: 100dvh;               /* ★ 手机端动态高度 */
  background: #000;
  color: #fff;
  overflow: hidden;
  box-sizing: border-box;
}

/* ── 顶部（标题 + 类别，固定不滚动） ── */
.live-top {
  flex-shrink: 0;
  background: #0d0d0d;
  border-bottom: 1px solid #222;
}
.title-row {
  display: flex;
  align-items: center;
  gap: 0.6rem;
  padding: 0.4rem 0.7rem;
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
  font-size: 0.9rem;
  font-weight: 600;
}
.live-title-input:focus { outline: none; border-color: #8b5cf6; }
.role-badge {
  padding: 0.2rem 0.6rem;
  border-radius: 12px;
  font-size: 0.7rem;
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
.category-row {
  padding: 0.35rem 0.7rem 0.5rem;
}
.live-category-select {
  background: #1a1a1a;
  border: 1px solid #333;
  border-radius: 8px;
  color: #fff;
  padding: 0.35rem 0.6rem;
  font-size: 0.85rem;
  width: 100%;
  box-sizing: border-box;
}

/* ── 中间主体（左右两列，可滚动） ── */
.live-body {
  display: grid;
  grid-template-columns: 3fr 2fr;
  gap: 0.5rem;
  padding: 0.5rem;
  flex: 1 1 auto;
  min-height: 0;
  overflow: hidden;
}
.left-col {
  display: flex;
  flex-direction: column;
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
  position: relative;
}
.field-camera-iframe {
  width: 100%;
  height: 100%;
  display: block;
  border: 0;
}

/* ★ 观众模式：遮住 iframe 底部控制面板区域 */
.field-camera-frame.viewer-mode {
  /* 若有控制条，用伪元素遮住底部 15% */
  position: relative;
}
.field-camera-frame.viewer-mode::after {
  content: '';
  position: absolute;
  left: 0;
  right: 0;
  bottom: 0;
  height: 0;              /* 先设为 0；如果观众能看到控制条，改成 20% 左右 */
  background: #000;
  pointer-events: none;
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

/* ── ★ 底部固定栏（永远显示） ── */
.live-footer {
  flex-shrink: 0;
  background: #0d0d0d;
  border-top: 1px solid #222;
  padding: 0.4rem 0.5rem 0.5rem;
  box-sizing: border-box;
}

.action-bar {
  display: flex;
  gap: 0.3rem;
  padding: 0.25rem;
  background: #111;
  border-radius: 8px;
  margin-bottom: 0.4rem;
}
.action-btn {
  flex: 1 1 auto;
  min-width: 0;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 0.1rem;
  padding: 0.3rem 0.15rem;
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
.action-btn .icon { font-size: 1.05rem; }
.action-btn .label {
  font-size: 0.65rem;
  color: rgba(255, 255, 255, 0.75);
}
.action-btn.like:hover {
  background: rgba(231, 76, 60, 0.15);
  border-color: #e74c3c;
}

.audience-input-row {
  display: flex;
  gap: 0.35rem;
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
   移动端（<900px）：改为纵向布局
   ────────────────────────────────────────────── */
@media (max-width: 900px) {
  .live-body {
    grid-template-columns: 1fr;
    gap: 0.4rem;
    padding: 0.4rem;
    overflow-y: auto;         /* 中间区域可滚动 */
  }
  .right-col {
    flex-direction: row;
    align-items: flex-start;
  }
  .field-camera-frame { flex: 1; }
  .audience-panel { flex: 1; max-height: 260px; }
}

@media (max-width: 600px) {
  .live-body {
    padding: 0.35rem;
    gap: 0.35rem;
  }
  .right-col {
    flex-direction: column;
  }
  .field-camera-frame {
    aspect-ratio: 16 / 9;
  }
  .audience-panel {
    max-height: 180px;
  }
  .action-btn .label { font-size: 0.58rem; }
  .action-btn .icon { font-size: 0.95rem; }
  .title-row { padding: 0.35rem 0.5rem; }
  .category-row { padding: 0.3rem 0.5rem 0.45rem; }
  .live-title-input { font-size: 0.85rem; }
  .live-category-select { font-size: 0.8rem; }
  .live-footer { padding: 0.35rem 0.4rem 0.45rem; }
}
</style>