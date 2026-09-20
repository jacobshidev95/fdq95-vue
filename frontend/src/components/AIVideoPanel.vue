<template>
  <div class="ai-video-panel" :class="{ 'is-mobile': isMobile }">
    <!-- 输入区域 -->
    <div v-if="stage === 'input'" class="input-stage">
      <div class="panel-header">
        <h2>{{ t('ai_video_page_title') }}</h2>
        <p class="subtitle">{{ t('ai_video_subtitle') }}</p>
      </div>

      <div class="form-group">
        <label>{{ t('ai_video_idea_label') }}</label>
        <textarea
          v-model="form.idea"
          class="idea-input"
          :placeholder="t('ai_video_idea_placeholder')"
          rows="5"
        />
      </div>

      <div class="form-row">
        <div class="form-group">
          <label>{{ t('ai_video_duration_label') }}</label>
          <select v-model.number="form.target_duration" class="duration-select">
            <option :value="30">30s</option>
            <option :value="60">60s</option>
            <option :value="120">120s</option>
            <option :value="300">5min</option>
          </select>
        </div>
        <div class="form-group">
          <label>{{ t('ai_video_language_label') }}</label>
          <select v-model="form.language" class="lang-select">
            <option value="zh">中文</option>
            <option value="en">English</option>
            <option value="ja">日本語</option>
          </select>
        </div>
      </div>

      <button
        class="generate-btn"
        :disabled="form.idea.length < 10"
        @click="handleGenerate"
      >
        {{ t('ai_video_generate_btn') }}
      </button>
    </div>

    <!-- 生成中 -->
    <div v-else-if="stage === 'generating'" class="generating-stage">
      <div class="progress-container">
        <div class="spinner" />
        <h3>{{ t('ai_video_generating') }}</h3>
        <p class="current-step">{{ stepLabel(progressStep) }}</p>
        <div class="progress-bar">
          <div class="progress-fill" :style="{ width: `${progress * 100}%` }" />
        </div>
        <span class="progress-text">{{ Math.round(progress * 100) }}%</span>
      </div>
    </div>

    <!-- 完成 -->
    <div v-else-if="stage === 'done'" class="result-stage">
      <h3>{{ t('ai_video_done') }}</h3>
      <video
        v-if="videoUrl"
        :src="videoUrl"
        controls
        class="result-video"
      />
      <div class="action-row">
        <a :href="videoUrl" download class="download-btn">
          {{ t('ai_video_download') }}
        </a>
        <button class="new-btn" @click="reset">
          {{ t('ai_video_new') }}
        </button>
      </div>
    </div>

    <!-- 错误 -->
    <div v-else-if="stage === 'error'" class="error-stage">
      <p class="error-msg">{{ errorMessage }}</p>
      <button class="retry-btn" @click="reset">{{ t('ai_video_retry') }}</button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted, onUnmounted } from 'vue'
import { useI18nStore } from '@/stores/i18n'
import {
  startGeneration,
  subscribeProgress,
  type TaskStatus,
} from '@/api/aiVideo'

const emit = defineEmits<{
  (e: 'generated', payload: { videoId: string; videoUrl: string }): void
  (e: 'close'): void
}>()

const i18n = useI18nStore()
const t = (key: string): string => i18n.t(key)

const stage = ref<'input' | 'generating' | 'done' | 'error'>('input')
const progress = ref(0)
const progressStep = ref('')
const videoUrl = ref('')
const errorMessage = ref('')
const isMobile = ref(false)

let eventSource: EventSource | null = null

const form = reactive({
  idea: '',
  target_duration: 60,
  language: 'zh',
})

// 进度阶段 → i18n 键映射
const stepKeyMap: Record<string, string> = {
  initialized: 'ai_video_step_init',
  scripting_done: 'ai_video_step_script',
  directing_done: 'ai_video_step_direct',
  review_done: 'ai_video_step_review',
  completed: 'ai_video_step_done',
}

function stepLabel(step: string): string {
  return t(stepKeyMap[step] ?? 'ai_video_step_init')
}

function handleResize() {
  isMobile.value = window.innerWidth < 768
}

onMounted(() => {
  handleResize()
  window.addEventListener('resize', handleResize)
})

onUnmounted(() => {
  window.removeEventListener('resize', handleResize)
  eventSource?.close()
})

async function handleGenerate() {
  try {
    stage.value = 'generating'
    progress.value = 0
    progressStep.value = 'initialized'

    const { task_id } = await startGeneration({
      idea: form.idea,
      target_duration: form.target_duration,
      language: form.language,
    })

    eventSource = subscribeProgress(
      task_id,
      (data) => {
        progress.value = data.progress
        progressStep.value = data.step
      },
      (data: TaskStatus) => {
        if (data.final_video_url) {
          videoUrl.value = data.final_video_url
          stage.value = 'done'
          // ★ 把 videoId 一并 emit，供父组件发布使用
          const vid = data.final_video_url.split('/').pop() || ''
          emit('generated', { videoId: vid, videoUrl: data.final_video_url })
        } else {
          errorMessage.value = data.errors?.join(', ') || t('ai_video_failed')
          stage.value = 'error'
        }
      },
      (msg) => {
        errorMessage.value = msg
        stage.value = 'error'
      },
    )
  } catch (e: any) {
    errorMessage.value = e?.message || t('ai_video_failed')
    stage.value = 'error'
  }
}

function reset() {
  stage.value = 'input'
  progress.value = 0
  videoUrl.value = ''
  errorMessage.value = ''
  eventSource?.close()
}
</script>

<style scoped>
.ai-video-panel {
  max-width: 720px;
  margin: 0 auto;
  padding: 24px;
  background: #1a1a2e;
  border-radius: 16px;
  color: #e0e0e0;
}

.panel-header h2 {
  margin: 0 0 8px;
  font-size: 1.5rem;
}

.subtitle {
  color: #888;
  margin-bottom: 24px;
}

.form-group {
  margin-bottom: 16px;
}

.form-group label {
  display: block;
  margin-bottom: 6px;
  font-size: 0.9rem;
  color: #aaa;
}

.idea-input {
  width: 100%;
  padding: 12px;
  background: #0f0f1a;
  border: 1px solid #333;
  border-radius: 8px;
  color: #e0e0e0;
  font-size: 0.95rem;
  resize: vertical;
  box-sizing: border-box;
}

.idea-input:focus {
  outline: none;
  border-color: #6c5ce7;
}

.form-row {
  display: flex;
  gap: 16px;
}

.form-row .form-group {
  flex: 1;
}

.duration-select,
.lang-select {
  width: 100%;
  padding: 10px;
  background: #0f0f1a;
  border: 1px solid #333;
  border-radius: 8px;
  color: #e0e0e0;
}

.generate-btn {
  width: 100%;
  padding: 14px;
  margin-top: 16px;
  background: linear-gradient(135deg, #6c5ce7, #a29bfe);
  border: none;
  border-radius: 10px;
  color: #fff;
  font-size: 1rem;
  font-weight: 600;
  cursor: pointer;
  transition: opacity 0.2s;
}

.generate-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.progress-container {
  text-align: center;
  padding: 40px 0;
}

.spinner {
  width: 48px;
  height: 48px;
  border: 4px solid #333;
  border-top-color: #6c5ce7;
  border-radius: 50%;
  margin: 0 auto 20px;
  animation: spin 1s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

.progress-bar {
  width: 100%;
  height: 8px;
  background: #0f0f1a;
  border-radius: 4px;
  margin: 20px 0 8px;
  overflow: hidden;
}

.progress-fill {
  height: 100%;
  background: linear-gradient(90deg, #6c5ce7, #a29bfe);
  border-radius: 4px;
  transition: width 0.5s ease;
}

.result-video {
  width: 100%;
  border-radius: 12px;
  margin: 16px 0;
}

.action-row {
  display: flex;
  gap: 12px;
}

.download-btn,
.new-btn,
.retry-btn {
  flex: 1;
  padding: 12px;
  border-radius: 10px;
  text-align: center;
  font-weight: 600;
  cursor: pointer;
  text-decoration: none;
}

.download-btn {
  background: #6c5ce7;
  color: #fff;
  border: none;
}

.new-btn {
  background: transparent;
  color: #6c5ce7;
  border: 1px solid #6c5ce7;
}

.error-msg {
  color: #ff6b6b;
  text-align: center;
  padding: 20px;
}

/* 响应式 */
.is-mobile {
  padding: 16px;
  border-radius: 12px;
}

.is-mobile .form-row {
  flex-direction: column;
  gap: 8px;
}

.is-mobile .panel-header h2 {
  font-size: 1.2rem;
}
</style>