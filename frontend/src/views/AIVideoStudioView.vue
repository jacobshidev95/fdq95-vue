<script setup lang="ts">
import { computed, onBeforeUnmount, ref，watch } from 'vue'
import { useRouter } from 'vue-router'
import { api } from '@/api/client'
import { useI18nStore, LANGUAGES } from '@/stores/i18n'
import {
  startGeneration,
  subscribeProgress,
  publishAiVideo,
  type TaskStatus,
} from '@/api/aiVideo'

const router = useRouter()
const i18n = useI18nStore()

type Category =
  | 'medical' | 'health' | 'education' | 'entertainment' | 'travel'
  | 'food' | 'clothing' | 'industry' | 'tech' | 'iot' | 'life' | 'ai'

const CATEGORIES: { value: Category; key: string }[] = [
  { value: 'medical', key: 'Medical' },
  { value: 'health', key: 'Health' },
  { value: 'education', key: 'Education' },
  { value: 'entertainment', key: 'Entertainment' },
  { value: 'travel', key: 'Travel' },
  { value: 'food', key: 'Food' },
  { value: 'clothing', key: 'Clothing' },
  { value: 'industry', key: 'Industry' },
  { value: 'tech', key: 'Technology' },
  { value: 'iot', key: 'IoT' },
  { value: 'life', key: 'Life' },
  { value: 'ai', key: 'AI' },
]

const title = ref('')
const category = ref<Category | null>(null)
const promptLang = ref(i18n.language || 'en')
// ★ 新增：跟随界面语言
watch(() => i18n.language, (newLang) => {
  promptLang.value = newLang
})
const prompt = ref('')
const targetDuration = ref<number>(30)

const generating = ref(false)
const generateProgress = ref(0)
const generateStage = ref('')
const errorMsg = ref('')
const successMsg = ref('')

const generatedVideoUrl = ref('')
const generatedVideoId = ref('')
const showPlayback = ref(false)

const publishing = ref(false)

interface SmartTool {
  id: string
  icon: string
  labelKey: string
  enabled: boolean
}
const smartTools = ref<SmartTool[]>([
  { id: 'auto-caption', icon: '💬', labelKey: 'ai_tool_auto_caption', enabled: true },
  { id: 'bgm',          icon: '🎵', labelKey: 'ai_tool_bgm',          enabled: true },
  { id: 'transition',   icon: '✨', labelKey: 'ai_tool_transition',   enabled: true },
  { id: 'stabilize',    icon: '🎯', labelKey: 'ai_tool_stabilize',    enabled: false },
  { id: 'enhance',      icon: '🌈', labelKey: 'ai_tool_enhance',      enabled: false },
  { id: 'trim-silence', icon: '🔇', labelKey: 'ai_tool_trim_silence', enabled: true },
])

const canGenerate = computed(() =>
  !!prompt.value.trim() && !generating.value,
)

const canPublish = computed(() =>
  !!generatedVideoId.value &&
  !!title.value.trim() &&
  !!category.value &&
  !publishing.value,
)

// ★ SSE 连接句柄
let eventSource: EventSource | null = null
function closeEventSource() {
  eventSource?.close()
  eventSource = null
}

// ──────────────────────────────────────────────
// 生成视频（SSE 实时进度）
// ──────────────────────────────────────────────
async function generateVideo() {
  errorMsg.value = ''
  successMsg.value = ''
  if (!canGenerate.value) {
    errorMsg.value = i18n.t('ai_video_required')
    return
  }

  generating.value = true
  generateProgress.value = 0
  generateStage.value = i18n.t('ai_video_stage_submit')
  generatedVideoUrl.value = ''
  generatedVideoId.value = ''

  try {
    // 1. 触发后端流水线
    const { task_id } = await startGeneration({
      idea: prompt.value.trim(),
      target_duration: targetDuration.value,
      language: promptLang.value,
    })
    generateStage.value = i18n.t('ai_video_stage_processing')

    // 2. 订阅 SSE，等待完成
    await new Promise<void>((resolve, reject) => {
      eventSource = subscribeProgress(
        task_id,
        (data) => {
          // 进度回调
          generateProgress.value = Math.round((data.progress || 0) * 100)
          if (data.step) {
            generateStage.value = mapStage(data.step)
          }
        },
        (data: TaskStatus) => {
          // 完成回调
          if (data.final_video_url) {
            generatedVideoUrl.value = data.final_video_url
            generatedVideoId.value =
              data.final_video_url.split('/').pop() || ''
            generateProgress.value = 100
            resolve()
          } else {
            reject(
              new Error(
                (data.errors || []).join(', ') || i18n.t('ai_video_failed'),
              ),
            )
          }
        },
        (msg) => reject(new Error(msg)),
      )
    })

    successMsg.value = i18n.t('ai_video_success')
  } catch (e: any) {
    errorMsg.value = e?.message || i18n.t('ai_video_failed')
  } finally {
    generating.value = false
    closeEventSource()
  }
}

// 把后端 stage 字符串映射为 i18n 键
function mapStage(step: string): string {
  const map: Record<string, string> = {
    initialized: 'ai_video_step_init',
    scripting_done: 'ai_video_step_script',
    directing_done: 'ai_video_step_direct',
    review_done: 'ai_video_step_review',
    completed: 'ai_video_step_done',
  }
  const key = map[step]
  return key ? i18n.t(key) : step
}

// ──────────────────────────────────────────────
// 发布视频
// ──────────────────────────────────────────────
async function publishVideo() {
  errorMsg.value = ''
  successMsg.value = ''
  if (!canPublish.value) {
    errorMsg.value = i18n.t('ai_video_required')
    return
  }
  publishing.value = true
  try {
    // 1. 把生成的 mp4 转正到 uploads/videos/
    const res = await publishAiVideo(
      generatedVideoId.value,
      title.value.trim(),
    )

    // 2. 走既有的 /api/videos 接口创建视频记录
    await api.post('/api/videos', {
      title: title.value.trim(),
      category: category.value,
      content_type: 'file',
      url: res.public_url,
      duration_sec: 0,
      file_size: res.file_size || 0,
    })

    successMsg.value = i18n.t('ai_video_published')
    setTimeout(() => router.push('/videos'), 1200)
  } catch (e: any) {
    errorMsg.value =
      e?.response?.data?.detail || i18n.t('ai_video_publish_failed')
  } finally {
    publishing.value = false
  }
}

// ──────────────────────────────────────────────
// 回放
// ──────────────────────────────────────────────
function openPlayback() {
  if (!generatedVideoUrl.value) {
    errorMsg.value = i18n.t('ai_video_no_result')
    return
  }
  showPlayback.value = true
}
function closePlayback() {
  showPlayback.value = false
}

function goBack() {
  router.back()
}

onBeforeUnmount(() => {
  closeEventSource()
})
</script>

<template>
  <div class="ai-video-page">
    <header class="top-bar">
      <button type="button" class="back-btn" @click="goBack">‹</button>
      <h1 class="page-title">{{ i18n.t('ai_video_page_title') }}</h1>
      <span class="spacer" />
    </header>

    <div class="scroll-body">
      <div v-if="errorMsg" class="notice notice-error">{{ errorMsg }}</div>
      <div v-if="successMsg" class="notice notice-ok">{{ successMsg }}</div>

      <!-- 标题 -->
      <section class="card">
        <label class="field-label">{{ i18n.t('publish_video_title') }}</label>
        <input
          v-model="title"
          type="text"
          class="title-input"
          :placeholder="i18n.t('publish_video_title_ph')"
          maxlength="200"
        />
      </section>

      <!-- 类别 -->
      <section class="card">
        <label class="field-label">{{ i18n.t('publish_video_category') }}</label>
        <div class="radio-grid">
          <label v-for="cat in CATEGORIES" :key="cat.value" class="radio-item">
            <input
              type="radio"
              name="ai-category"
              :value="cat.value"
              v-model="category"
            />
            <span>{{ cat.key }}</span>
          </label>
        </div>
      </section>

      <!-- 创意 + 时长 + 语言 -->
      <section class="card">
        <div class="prompt-head">
          <label class="field-label">{{ i18n.t('ai_video_prompt') }}</label>
          <div class="prompt-head-actions">
            <select v-model.number="targetDuration" class="lang-inline">
              <option :value="30">
                {{ i18n.t('ai_video_duration_label') }} 30s
              </option>
              <option :value="60">
                {{ i18n.t('ai_video_duration_label') }} 60s
              </option>
              <option :value="120">
                {{ i18n.t('ai_video_duration_label') }} 2min
              </option>
              <option :value="300">
                {{ i18n.t('ai_video_duration_label') }} 5min
              </option>
            </select>
            <select v-model="promptLang" class="lang-inline">
              <option
                v-for="(label, code) in LANGUAGES"
                :key="code"
                :value="code"
              >
                {{ label }}
              </option>
            </select>
          </div>
        </div>
        <textarea
          v-model="prompt"
          rows="5"
          class="prompt-textarea"
          :placeholder="i18n.t('ai_video_prompt_ph')"
          maxlength="2000"
        />
        <div class="prompt-count">{{ prompt.length }} / 2000</div>
      </section>

      <!-- 智能编辑工具 -->
      <section class="card">
        <label class="field-label">{{ i18n.t('ai_video_tools') }}</label>
        <div class="tools-grid">
          <label
            v-for="t in smartTools"
            :key="t.id"
            class="tool-item"
            :class="{ active: t.enabled }"
          >
            <input type="checkbox" v-model="t.enabled" />
            <span class="tool-icon">{{ t.icon }}</span>
            <span class="tool-label">{{ i18n.t(t.labelKey) }}</span>
          </label>
        </div>
      </section>

      <!-- 生成进度 -->
      <section v-if="generating" class="card progress-card">
        <div class="progress-track">
          <div
            class="progress-fill"
            :style="{ width: generateProgress + '%' }"
          />
        </div>
        <div class="progress-text">
          <span>{{ generateStage }}</span>
          <span class="pct">{{ generateProgress }}%</span>
        </div>
      </section>

      <!-- 生成按钮 -->
      <button
        type="button"
        class="action-btn generate"
        :disabled="!canGenerate"
        @click="generateVideo"
      >
        🪄
        {{
          generating
            ? i18n.t('ai_video_generating')
            : i18n.t('ai_video_generate')
        }}
      </button>

      <!-- 生成结果 -->
      <section v-if="generatedVideoUrl" class="card result-card">
        <div class="result-hint">{{ i18n.t('ai_video_ready') }}</div>
        <div class="result-row">
          <button
            type="button"
            class="action-btn playback"
            @click="openPlayback"
          >
            <span>▶</span>
            <span>{{ i18n.t('ai_video_playback') }}</span>
          </button>
          <button
            type="button"
            class="action-btn publish"
            :disabled="!canPublish"
            @click="publishVideo"
          >
            <span>📤</span>
            <span>
              {{ publishing ? '…' : i18n.t('ai_video_publish') }}
            </span>
          </button>
        </div>
      </section>
    </div>

    <!-- 全屏回放 -->
    <div v-if="showPlayback" class="fullscreen-playback">
      <div class="fs-header">
        <h3>{{ title || i18n.t('ai_video_playback') }}</h3>
        <button type="button" class="fs-close" @click="closePlayback">
          ✕
        </button>
      </div>
      <video
        class="fs-video"
        :src="generatedVideoUrl"
        controls
        autoplay
        playsinline
      />
      <div class="fs-toolbar">
        <span class="fs-toolbar-label">
          {{ i18n.t('ai_video_tools') }}:
        </span>
        <span
          v-for="t in smartTools.filter((x) => x.enabled)"
          :key="t.id"
          class="fs-tool-chip"
        >
          {{ t.icon }} {{ i18n.t(t.labelKey) }}
        </span>
      </div>
    </div>
  </div>
</template>

<style scoped>
.ai-video-page {
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
  padding: 0.7rem 1rem;
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
  padding: 0 0.75rem 2rem;
  overflow-y: auto;
}

.card {
  background: #1a1a1a;
  border-radius: 12px;
  padding: 1rem;
  margin-bottom: 1rem;
}

.field-label {
  display: block;
  color: rgba(255, 255, 255, 0.6);
  font-size: 0.85rem;
  margin-bottom: 0.5rem;
}

.title-input {
  width: 100%;
  background: #0d0d0d;
  border: 1px solid rgba(255, 255, 255, 0.12);
  border-radius: 8px;
  color: #fff;
  padding: 0.65rem 1rem;
  font-size: 1.05rem;
  font-weight: 600;
  text-align: center;
  box-sizing: border-box;
}
.title-input:focus { outline: none; border-color: #8b5cf6; }

.radio-grid {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 0.4rem 0.6rem;
}
.radio-item {
  display: inline-flex;
  align-items: center;
  gap: 0.35rem;
  color: var(--text);
  cursor: pointer;
  user-select: none;
  font-size: 0.85rem;
}
.radio-item input {
  width: auto;
  margin: 0;
  accent-color: #8b5cf6;
}

/* 创意卡片头：label + 时长/语言下拉 */
.prompt-head {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 0.5rem;
  flex-wrap: wrap;
}
.prompt-head-actions {
  display: flex;
  gap: 0.4rem;
  align-items: center;
  flex-wrap: wrap;
}
.lang-inline {
  background: transparent;
  color: #fff;
  border: 1px solid rgba(255, 255, 255, 0.15);
  border-radius: 6px;
  padding: 0.2rem 0.5rem;
  font-size: 0.78rem;
}
.lang-inline option { background: #1e1e1e; color: #fff; }

.prompt-textarea {
  width: 100%;
  min-height: 110px;
  margin-top: 0.5rem;
  background: #0d0d0d;
  border: 1px solid rgba(255, 255, 255, 0.12);
  border-radius: 8px;
  color: #fff;
  padding: 0.65rem 0.85rem;
  font-size: 0.95rem;
  line-height: 1.5;
  resize: vertical;
  box-sizing: border-box;
  font-family: inherit;
}
.prompt-textarea:focus { outline: none; border-color: #8b5cf6; }

.prompt-count {
  text-align: right;
  font-size: 0.72rem;
  color: rgba(255, 255, 255, 0.4);
  margin-top: 0.3rem;
}

.tools-grid {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 0.45rem;
}
.tool-item {
  display: flex;
  align-items: center;
  gap: 0.35rem;
  background: rgba(255, 255, 255, 0.04);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 8px;
  padding: 0.5rem 0.55rem;
  cursor: pointer;
  font-size: 0.76rem;
  transition: all 0.15s;
}
.tool-item.active {
  background: rgba(139, 92, 246, 0.15);
  border-color: #8b5cf6;
  color: #c4b5fd;
}
.tool-item input {
  width: auto;
  margin: 0;
  accent-color: #8b5cf6;
}
.tool-icon { font-size: 1rem; }
.tool-label {
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.progress-card { padding: 0.85rem; }
.progress-track {
  width: 100%;
  height: 8px;
  background: rgba(255, 255, 255, 0.1);
  border-radius: 4px;
  overflow: hidden;
  position: relative;
}
.progress-track.small { height: 6px; margin-top: 0.6rem; }
.progress-fill {
  height: 100%;
  background: linear-gradient(90deg, #8b5cf6, #a78bfa);
  border-radius: 4px;
  transition: width 0.2s ease-out;
  position: relative;
}
.progress-fill::after {
  content: '';
  position: absolute;
  inset: 0;
  background-image: linear-gradient(
    45deg,
    rgba(255, 255, 255, 0.2) 25%,
    transparent 25%,
    transparent 50%,
    rgba(255, 255, 255, 0.2) 50%,
    rgba(255, 255, 255, 0.2) 75%,
    transparent 75%,
    transparent
  );
  background-size: 20px 20px;
  animation: progress-stripe 0.8s linear infinite;
}
@keyframes progress-stripe {
  from { background-position: 0 0; }
  to { background-position: 20px 0; }
}
.progress-text {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-top: 0.45rem;
  font-size: 0.8rem;
  color: #c4b5fd;
  font-weight: 600;
}
.progress-text .pct {
  font-family: ui-monospace, monospace;
  color: #e5b80b;
}

.action-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 0.5rem;
  padding: 0.75rem 1rem;
  border: none;
  border-radius: 10px;
  font-weight: 700;
  font-size: 0.95rem;
  cursor: pointer;
  transition: all 0.15s;
}
.action-btn:disabled { opacity: 0.4; cursor: not-allowed; }

.action-btn.generate {
  width: 100%;
  background: #8b5cf6;
  color: #fff;
  box-shadow: 0 4px 14px rgba(139, 92, 246, 0.4);
  margin-bottom: 1rem;
}
.action-btn.generate:hover:not(:disabled) { background: #7c3aed; }

.result-card {
  border: 1px solid rgba(139, 92, 246, 0.3);
  background: linear-gradient(
    135deg,
    rgba(139, 92, 246, 0.06),
    rgba(139, 92, 246, 0.02)
  );
}
.result-hint {
  font-size: 0.85rem;
  color: #c4b5fd;
  text-align: center;
  margin-bottom: 0.6rem;
}
.result-row {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 0.6rem;
}
.action-btn.playback {
  background: rgba(255, 255, 255, 0.1);
  color: #fff;
  border: 1px solid rgba(255, 255, 255, 0.18);
}
.action-btn.publish {
  background: #8b5cf6;
  color: #fff;
  box-shadow: 0 4px 14px rgba(139, 92, 246, 0.4);
}

.fullscreen-playback {
  position: fixed;
  inset: 0;
  background: #000;
  z-index: 9999;
  display: flex;
  flex-direction: column;
  width: 100vw;
  height: 100vh;
  height: 100dvh;
}
.fs-header {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  z-index: 10;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0.7rem 1rem;
  background: linear-gradient(
    to bottom,
    rgba(0, 0, 0, 0.8) 0%,
    rgba(0, 0, 0, 0) 100%
  );
  pointer-events: none;
}
.fs-header h3 {
  margin: 0;
  font-size: 0.95rem;
  font-weight: 500;
  color: #fff;
  max-width: 70%;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  pointer-events: auto;
  text-shadow: 0 1px 4px rgba(0, 0, 0, 0.9);
}
.fs-close {
  background: rgba(0, 0, 0, 0.5);
  border: 1px solid rgba(255, 255, 255, 0.25);
  color: #fff;
  width: 36px;
  height: 36px;
  border-radius: 50%;
  font-size: 1.1rem;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  pointer-events: auto;
}
.fs-close:hover {
  background: rgba(139, 92, 246, 0.6);
  border-color: #8b5cf6;
}
.fs-video {
  width: 100%;
  height: 100%;
  object-fit: contain;
  background: #000;
  display: block;
}
.fs-toolbar {
  position: absolute;
  left: 0;
  right: 0;
  bottom: 0;
  display: flex;
  flex-wrap: wrap;
  gap: 0.4rem;
  padding: 0.5rem 0.75rem;
  background: linear-gradient(
    to top,
    rgba(0, 0, 0, 0.8) 0%,
    rgba(0, 0, 0, 0) 100%
  );
  pointer-events: none;
  align-items: center;
}
.fs-toolbar-label {
  font-size: 0.75rem;
  color: rgba(255, 255, 255, 0.6);
}
.fs-tool-chip {
  background: rgba(139, 92, 246, 0.2);
  border: 1px solid rgba(139, 92, 246, 0.5);
  color: #c4b5fd;
  padding: 0.15rem 0.5rem;
  border-radius: 12px;
  font-size: 0.7rem;
}

.notice {
  padding: 0.7rem 1rem;
  border-radius: 8px;
  margin-bottom: 0.75rem;
  font-size: 0.88rem;
}
.notice-error {
  background: rgba(231, 76, 60, 0.15);
  border: 1px solid #e74c3c;
  color: #ff8a80;
}
.notice-ok {
  background: rgba(46, 204, 113, 0.15);
  border: 1px solid #2ecc71;
  color: #a5f5c6;
}

/* 响应式 */
@media (max-width: 720px) {
  .radio-grid { grid-template-columns: repeat(2, minmax(0, 1fr)); }
  .tools-grid { grid-template-columns: repeat(2, minmax(0, 1fr)); }
}
@media (max-width: 480px) {
  .top-bar { padding: 0.5rem 0.7rem; }
  .page-title { font-size: 0.88rem; }
  .scroll-body { padding: 0 0.5rem 1.5rem; }
  .card { padding: 0.75rem; }
  .tool-item { font-size: 0.7rem; padding: 0.4rem 0.4rem; }
  .action-btn { font-size: 0.85rem; padding: 0.65rem 0.85rem; }
}
</style>