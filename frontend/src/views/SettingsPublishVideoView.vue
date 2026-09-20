<script setup lang="ts">
import { computed, onBeforeUnmount, reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import { api } from '@/api/client'
import { useI18nStore } from '@/stores/i18n'

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
// ★ 只剩两种内容类型：file / record
const contentType = ref<'file' | 'record'>('file')

// A：上传文件
const uploadedUrl = ref('')
const uploadedName = ref('')
const uploadedSize = ref(0)
const uploadingFile = ref(false)
// ★★★ 上传进度 0-100
const uploadProgress = ref(0)
const fileError = ref('')

// B：录制（旧代码保留，防 TS 未用报错；实际由独立页面处理）
const isRecording = ref(false)
const recordDuration = ref(0)
const recordedBlob = ref<Blob | null>(null)
const recordedUrl = ref('')
const recordedServerUrl = ref('')
const uploadingRecord = ref(false)
const recordError = ref('')
const videoPreviewEl = ref<HTMLVideoElement | null>(null)

let mediaRecorder: MediaRecorder | null = null
let mediaStream: MediaStream | null = null
let recordTimer: number | null = null
let chunks: BlobPart[] = []

const submitting = ref(false)
const submitError = ref('')
const submitSuccess = ref('')

const MAX_VIDEO_MB = 50

const canSubmit = computed(() => {
  if (!title.value.trim()) return false
  if (!category.value) return false
  if (contentType.value === 'file') return !!uploadedUrl.value
  return false
})

// ★★★ 通用上传 —— 带进度
async function uploadVideoFile(blobOrFile: Blob, filename: string) {
  const formData = new FormData()
  formData.append('file', blobOrFile, filename)
  uploadProgress.value = 0
  const { data } = await api.post('/api/videos/upload-video', formData, {
    timeout: 300000,
    onUploadProgress: (e) => {
      if (e.total && e.total > 0) {
        uploadProgress.value = Math.min(
          99,
          Math.round((e.loaded / e.total) * 100),
        )
      }
    },
  })
  uploadProgress.value = 100
  return data as { url: string; name: string; size: number }
}

// ── A：选择本地 MP4 ──
function pickVideo() {
  const input = document.createElement('input')
  input.type = 'file'
  input.accept = '.mp4,video/mp4'
  input.onchange = async () => {
    const f = input.files?.[0]
    if (!f) return
    fileError.value = ''
    if (f.size > MAX_VIDEO_MB * 1024 * 1024) {
      fileError.value = i18n.t('publish_video_file_too_large')
      return
    }
    uploadingFile.value = true
    uploadProgress.value = 0
    try {
      const res = await uploadVideoFile(f, f.name)
      uploadedUrl.value = res.url
      uploadedName.value = res.name
      uploadedSize.value = res.size
    } catch (e: any) {
      fileError.value =
        e?.response?.data?.detail ||
        e?.message ||
        i18n.t('publish_video_upload_failed')
    } finally {
      uploadingFile.value = false
    }
  }
  input.click()
}

function clearUploaded() {
  uploadedUrl.value = ''
  uploadedName.value = ''
  uploadedSize.value = 0
  fileError.value = ''
  uploadProgress.value = 0
}

// ── B：录制（保留旧代码，防 TS 未用报错） ──
async function startRecording() {
  recordError.value = ''
  try {
    mediaStream = await navigator.mediaDevices.getUserMedia({
      video: { width: 1280, height: 720 },
      audio: true,
    })
    if (videoPreviewEl.value) {
      videoPreviewEl.value.srcObject = mediaStream
      videoPreviewEl.value.muted = true
      await videoPreviewEl.value.play()
    }
    chunks = []
    const mimeType = MediaRecorder.isTypeSupported('video/mp4')
      ? 'video/mp4'
      : 'video/webm'
    mediaRecorder = new MediaRecorder(mediaStream, { mimeType })
    mediaRecorder.ondataavailable = (e) => {
      if (e.data.size > 0) chunks.push(e.data)
    }
    mediaRecorder.onstop = () => {
      const blob = new Blob(chunks, { type: mimeType })
      recordedBlob.value = blob
      recordedUrl.value = URL.createObjectURL(blob)
    }
    mediaRecorder.start()
    isRecording.value = true
    recordDuration.value = 0
    recordTimer = window.setInterval(() => {
      recordDuration.value += 1
    }, 1000)
  } catch (e: any) {
    recordError.value = i18n.t('publish_video_camera_denied')
  }
}

function stopRecording() {
  if (mediaRecorder && mediaRecorder.state !== 'inactive') {
    mediaRecorder.stop()
  }
  if (mediaStream) {
    mediaStream.getTracks().forEach((t) => t.stop())
    mediaStream = null
  }
  if (recordTimer) {
    clearInterval(recordTimer)
    recordTimer = null
  }
  isRecording.value = false
}

async function uploadRecorded() {
  if (!recordedBlob.value) return
  uploadingRecord.value = true
  uploadProgress.value = 0
  recordError.value = ''
  try {
    const res = await uploadVideoFile(
      recordedBlob.value,
      `record-${Date.now()}.mp4`,
    )
    recordedServerUrl.value = res.url
  } catch (e: any) {
    recordError.value =
      e?.response?.data?.detail ||
      e?.message ||
      i18n.t('publish_video_upload_failed')
  } finally {
    uploadingRecord.value = false
  }
}

function resetRecording() {
  recordedBlob.value = null
  recordedUrl.value = ''
  recordedServerUrl.value = ''
  recordDuration.value = 0
  recordError.value = ''
  uploadProgress.value = 0
}

// ── 提交 ──
async function submit() {
  submitError.value = ''
  submitSuccess.value = ''
  if (!canSubmit.value) {
    submitError.value = i18n.t('publish_video_required')
    return
  }
  submitting.value = true
  try {
    const url = uploadedUrl.value
    const fileSize = uploadedSize.value

    await api.post('/api/videos', {
      title: title.value.trim(),
      category: category.value,
      content_type: 'file',
      url,
      duration_sec: 0,
      file_size: fileSize,
    })
    submitSuccess.value = i18n.t('publish_video_success')
    setTimeout(() => router.push('/videos'), 1500)
  } catch (e: any) {
    submitError.value =
      e?.response?.data?.detail || i18n.t('publish_video_failed')
  } finally {
    submitting.value = false
  }
}

function goBack() {
  router.back()
}

// ★ 跳转到独立录像页
function goRecordVideo() {
  router.push('/record-video')
}

// ★★★ 新增：跳转到智能视频生产页
function goAIVideoStudio() {
  router.push('/ai-video-studio')
}

onBeforeUnmount(() => {
  stopRecording()
})
</script>

<template>
  <div class="publish-page">
    <header class="top-bar">
      <button type="button" class="back-btn" @click="goBack">‹</button>
      <h1 class="page-title">{{ i18n.t('settings_publish_video') }}</h1>
      <span class="spacer" />
    </header>

    <div class="scroll-body">
      <div v-if="submitError" class="notice notice-error">{{ submitError }}</div>
      <div v-if="submitSuccess" class="notice notice-ok">{{ submitSuccess }}</div>

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
              name="category"
              :value="cat.value"
              v-model="category"
            />
            <span>{{ cat.key }}</span>
          </label>
        </div>
      </section>

      <!-- 内容方式：只剩 2 个 tab -->
      <section class="card">
        <label class="field-label">{{ i18n.t('publish_video_content_type') }}</label>
        <div class="type-tabs">
          <button
            type="button"
            class="type-tab"
            :class="{ active: contentType === 'file' }"
            @click="contentType = 'file'"
          >
            📁 {{ i18n.t('publish_video_type_file') }}
          </button>
          <button
            type="button"
            class="type-tab"
            :class="{ active: contentType === 'record' }"
            @click="contentType = 'record'"
          >
            🎥 {{ i18n.t('publish_video_type_record') }}
          </button>
        </div>

        <!-- A: 上传文件（带进度条） -->
        <div v-if="contentType === 'file'" class="type-body">
          <button
            type="button"
            class="upload-btn"
            :disabled="uploadingFile"
            @click="pickVideo"
          >
            {{
              uploadingFile
                ? `${i18n.t('publish_video_uploading')} ${uploadProgress}%`
                : i18n.t('publish_video_choose_file')
            }}
          </button>
          <p class="hint">{{ i18n.t('publish_video_file_hint') }}</p>

          <div v-if="uploadingFile" class="progress-container">
            <div class="progress-bar-track">
              <div
                class="progress-bar-fill"
                :style="{ width: uploadProgress + '%' }"
              ></div>
            </div>
            <div class="progress-text">
              {{ uploadProgress }}%
              <span v-if="uploadProgress < 100" class="progress-status">
                · {{ i18n.t('publish_video_uploading') }}
              </span>
            </div>
          </div>

          <div v-if="fileError" class="notice notice-error">{{ fileError }}</div>
          <div v-if="uploadedUrl" class="file-chip">
            <span class="file-name">🎬 {{ uploadedName }}</span>
            <span class="file-size">
              ({{ (uploadedSize / 1024 / 1024).toFixed(2) }} MB)
            </span>
            <button type="button" class="chip-remove" @click="clearUploaded">✕</button>
          </div>
        </div>

        <!-- B: 录制 —— 跳转到独立录像页 -->
        <div v-else-if="contentType === 'record'" class="type-body">
          <button
            type="button"
            class="record-open-btn"
            @click="goRecordVideo"
          >
            🎥 {{ i18n.t('record_video_open') }}
          </button>
          <p class="hint">{{ i18n.t('record_video_open_hint') }}</p>

          <!-- ★★★ 新增：智能视频按钮（紫色渐变） -->
          <button
            type="button"
            class="ai-video-btn"
            @click="goAIVideoStudio"
          >
            🪄 {{ i18n.t('ai_video_open') }}
          </button>
          <p class="hint">{{ i18n.t('ai_video_open_hint') }}</p>
        </div>
      </section>

      <!-- Publish 按钮 -->
      <button
        v-if="contentType === 'file'"
        type="button"
        class="submit-btn"
        :disabled="!canSubmit || submitting"
        @click="submit"
      >
        {{
          submitting
            ? i18n.t('publish_video_uploading')
            : i18n.t('publish_video_submit')
        }}
      </button>
    </div>
  </div>
</template>

<style scoped>
.publish-page {
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
  padding: 0.8rem 1rem;
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
  padding: 0.75rem 1rem;
  font-size: 1.15rem;
  font-weight: 600;
  text-align: center;
  box-sizing: border-box;
}
.title-input:focus { outline: none; border-color: #e5b80b; }

.radio-grid {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 0.5rem 0.75rem;
}
.radio-item {
  display: inline-flex;
  align-items: center;
  gap: 0.4rem;
  color: var(--text);
  cursor: pointer;
  user-select: none;
}
.radio-item input { width: auto; margin: 0; accent-color: #e5b80b; }
.radio-item span {
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.type-tabs {
  display: flex;
  gap: 0.4rem;
  margin-bottom: 1rem;
  flex-wrap: wrap;
}
.type-tab {
  flex: 1 1 auto;
  background: rgba(255, 255, 255, 0.04);
  border: 1px solid rgba(255, 255, 255, 0.12);
  color: rgba(255, 255, 255, 0.75);
  border-radius: 8px;
  padding: 0.5rem 0.6rem;
  font-size: 0.85rem;
  cursor: pointer;
}
.type-tab.active {
  background: rgba(229, 184, 11, 0.12);
  border-color: #e5b80b;
  color: #e5b80b;
  font-weight: 600;
}

.type-body { margin-top: 0.5rem; }

.upload-btn {
  background: #e5b80b;
  color: #111;
  border: none;
  border-radius: 8px;
  padding: 0.6rem 1rem;
  font-weight: 600;
  cursor: pointer;
}
.upload-btn:disabled { opacity: 0.5; cursor: not-allowed; }

/* 上传进度条 */
.progress-container {
  margin-top: 0.85rem;
  padding: 0.6rem 0.75rem;
  background: rgba(229, 184, 11, 0.06);
  border: 1px solid rgba(229, 184, 11, 0.25);
  border-radius: 8px;
}
.progress-bar-track {
  width: 100%;
  height: 8px;
  background: rgba(255, 255, 255, 0.1);
  border-radius: 4px;
  overflow: hidden;
  position: relative;
}
.progress-bar-fill {
  height: 100%;
  background: linear-gradient(90deg, #e5b80b, #f5c518);
  border-radius: 4px;
  transition: width 0.2s ease-out;
  position: relative;
}
.progress-bar-fill::after {
  content: '';
  position: absolute;
  inset: 0;
  background-image: linear-gradient(
    45deg,
    rgba(255, 255, 255, 0.15) 25%,
    transparent 25%,
    transparent 50%,
    rgba(255, 255, 255, 0.15) 50%,
    rgba(255, 255, 255, 0.15) 75%,
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
  margin-top: 0.4rem;
  font-size: 0.8rem;
  color: #e5b80b;
  font-weight: 600;
  display: flex;
  justify-content: space-between;
  align-items: center;
}
.progress-status {
  color: rgba(255, 255, 255, 0.5);
  font-weight: 400;
}

/* 打开录像页按钮：紫色 */
.record-open-btn {
  width: 100%;
  background: #8b5cf6;
  color: #fff;
  border: none;
  border-radius: 10px;
  padding: 0.85rem 1rem;
  font-weight: 600;
  font-size: 0.95rem;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 0.4rem;
  transition: background 0.2s, box-shadow 0.2s;
  box-shadow: 0 4px 14px rgba(139, 92, 246, 0.35);
}
.record-open-btn:hover { background: #7c3aed; }

/* ★★★ 智能视频按钮：紫色渐变 */
.ai-video-btn {
  width: 100%;
  margin-top: 0.75rem;
  background: linear-gradient(135deg, #8b5cf6, #6366f1);
  color: #fff;
  border: none;
  border-radius: 10px;
  padding: 0.85rem 1rem;
  font-weight: 700;
  font-size: 0.95rem;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 0.4rem;
  box-shadow: 0 4px 14px rgba(139, 92, 246, 0.4);
  transition: all 0.2s;
}
.ai-video-btn:hover {
  background: linear-gradient(135deg, #7c3aed, #4f46e5);
  box-shadow: 0 6px 20px rgba(139, 92, 246, 0.55);
  transform: translateY(-1px);
}

.hint {
  color: rgba(255, 255, 255, 0.45);
  font-size: 0.78rem;
  margin: 0.5rem 0 0;
}

.file-chip {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  background: rgba(229, 184, 11, 0.08);
  border: 1px solid rgba(229, 184, 11, 0.35);
  border-radius: 8px;
  padding: 0.5rem 0.75rem;
  margin-top: 0.75rem;
  font-size: 0.85rem;
}
.file-name { flex: 1; word-break: break-all; }
.file-size { color: rgba(255, 255, 255, 0.55); font-size: 0.78rem; }
.chip-remove {
  background: transparent;
  border: none;
  color: #ff8a80;
  font-size: 1.1rem;
  cursor: pointer;
}

.submit-btn {
  width: 100%;
  background: #e5b80b;
  color: #111;
  border: none;
  border-radius: 10px;
  padding: 0.85rem 1rem;
  font-size: 1rem;
  font-weight: 700;
  cursor: pointer;
  margin-top: 0.5rem;
}
.submit-btn:disabled { opacity: 0.4; cursor: not-allowed; }

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

@media (max-width: 720px) {
  .radio-grid { grid-template-columns: repeat(2, minmax(0, 1fr)); }
}
</style>