<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, ref, nextTick } from 'vue'
import { useRouter } from 'vue-router'
import { api } from '@/api/client'
import { useI18nStore } from '@/stores/i18n'
import CategorySelect from '@/components/CategorySelect.vue'

const router = useRouter()
const i18n = useI18nStore()

const title = ref('')
// ★ 分类改为 string | null，配合 CategorySelect
const category = ref<string | null>(null)

// 录制状态
const previewStream = ref<MediaStream | null>(null)
const videoEl = ref<HTMLVideoElement | null>(null)
const mediaRecorder = ref<MediaRecorder | null>(null)
const recordedBlob = ref<Blob | null>(null)
const recordedUrl = ref('')
const isRecording = ref(false)
const recordDuration = ref(0)
let recordTimer: number | null = null

// 设备控制
const cameras = ref<MediaDeviceInfo[]>([])
const currentCameraIndex = ref(0)
const useAudio = ref(true)
const useTorch = ref(false)
const torchSupported = ref(false)
const useBeauty = ref(false)

// 页面状态
const loading = ref(false)
const publishing = ref(false)
const uploadProgress = ref(0)
const errorMsg = ref('')
const successMsg = ref('')
const showPlayback = ref(false)
const cameraError = ref('')

const BEAUTY_LEVEL = 60

const previewFilter = computed(() => {
  if (!useBeauty.value) return 'none'
  const lv = BEAUTY_LEVEL / 100
  return `brightness(${1 + 0.08 * lv}) contrast(${1 + 0.05 * lv}) saturate(${1 + 0.05 * lv})`
})

const hasRecording = computed(() => !!recordedUrl.value)
const canPlayback = computed(() => hasRecording.value && !isRecording.value)
const canPublish = computed(
  () => hasRecording.value && !isRecording.value && !publishing.value,
)

async function loadCameras() {
  try {
    const tmp = await navigator.mediaDevices.getUserMedia({ video: true })
    tmp.getTracks().forEach((t) => t.stop())
    const devices = await navigator.mediaDevices.enumerateDevices()
    cameras.value = devices.filter((d) => d.kind === 'videoinput')
  } catch (e) {
    console.warn('[Recorder] enumerateDevices failed', e)
    cameras.value = []
  }
}

async function startPreview() {
  cameraError.value = ''
  loading.value = true
  try {
    stopStream()
    const videoConstraints: MediaTrackConstraints = {
      width: { ideal: 1280 },
      height: { ideal: 720 },
    }
    if (cameras.value.length > 0 && cameras.value[currentCameraIndex.value]) {
      videoConstraints.deviceId = {
        exact: cameras.value[currentCameraIndex.value].deviceId,
      }
    } else {
      videoConstraints.facingMode =
        currentCameraIndex.value === 0 ? 'user' : 'environment'
    }

    const stream = await navigator.mediaDevices.getUserMedia({
      video: videoConstraints,
      audio: useAudio.value,
    })
    previewStream.value = stream

    if (videoEl.value) {
      videoEl.value.srcObject = stream
      videoEl.value.muted = true
      await videoEl.value.play().catch(() => {})
    }

    const track = stream.getVideoTracks()[0]
    const caps = track.getCapabilities?.() || {}
    torchSupported.value = 'torch' in caps
    if (!torchSupported.value && useTorch.value) {
      useTorch.value = false
    }
  } catch (e: any) {
    cameraError.value =
      e?.name === 'NotAllowedError'
        ? i18n.t('record_video_permission_denied')
        : i18n.t('record_video_no_camera')
    console.error('[Recorder] getUserMedia failed', e)
  } finally {
    loading.value = false
  }
}

function stopStream() {
  if (previewStream.value) {
    previewStream.value.getTracks().forEach((t) => t.stop())
    previewStream.value = null
  }
}

async function switchCamera() {
  if (isRecording.value) return
  currentCameraIndex.value =
    (currentCameraIndex.value + 1) % Math.max(cameras.value.length, 2)
  await startPreview()
}

async function toggleAudio() {
  useAudio.value = !useAudio.value
  if (!isRecording.value) await startPreview()
}

async function toggleTorch() {
  if (!torchSupported.value) {
    errorMsg.value = i18n.t('record_video_torch_unsupported')
    setTimeout(() => (errorMsg.value = ''), 2500)
    return
  }
  useTorch.value = !useTorch.value
  try {
    const track = previewStream.value?.getVideoTracks()[0]
    await track?.applyConstraints({
      advanced: [{ torch: useTorch.value } as any],
    })
  } catch (e) {
    console.warn('[Recorder] torch failed', e)
    useTorch.value = false
  }
}

function toggleBeauty() {
  useBeauty.value = !useBeauty.value
}

function startRecording() {
  if (!previewStream.value) {
    errorMsg.value = i18n.t('record_video_no_camera')
    return
  }
  errorMsg.value = ''
  successMsg.value = ''
  recordedBlob.value = null
  if (recordedUrl.value) {
    URL.revokeObjectURL(recordedUrl.value)
    recordedUrl.value = ''
  }

  try {
    const mimeType = MediaRecorder.isTypeSupported('video/mp4')
      ? 'video/mp4'
      : MediaRecorder.isTypeSupported('video/webm;codecs=vp9')
      ? 'video/webm;codecs=vp9'
      : 'video/webm'

    const chunks: BlobPart[] = []
    const recorder = new MediaRecorder(previewStream.value, { mimeType })

    recorder.ondataavailable = (e) => {
      if (e.data.size > 0) chunks.push(e.data)
    }
    recorder.onstop = () => {
      const blob = new Blob(chunks, { type: mimeType })
      recordedBlob.value = blob
      recordedUrl.value = URL.createObjectURL(blob)
      isRecording.value = false
      if (recordTimer) {
        clearInterval(recordTimer)
        recordTimer = null
      }
    }

    recorder.start()
    mediaRecorder.value = recorder
    isRecording.value = true
    recordDuration.value = 0
    recordTimer = window.setInterval(() => {
      recordDuration.value += 1
    }, 1000)
  } catch (e: any) {
    errorMsg.value = `Recorder error: ${e?.message || e}`
    console.error('[Recorder] MediaRecorder failed', e)
  }
}

function stopRecording() {
  if (mediaRecorder.value && mediaRecorder.value.state !== 'inactive') {
    mediaRecorder.value.stop()
  }
}

function toggleRecording() {
  if (isRecording.value) stopRecording()
  else startRecording()
}

function openPlayback() {
  if (!recordedUrl.value) {
    errorMsg.value = i18n.t('record_video_required')
    return
  }
  showPlayback.value = true
  nextTick(() => {
    const el = document.getElementById('playback-video') as HTMLVideoElement | null
    el?.play().catch(() => {})
  })
}

function closePlayback() {
  const el = document.getElementById('playback-video') as HTMLVideoElement | null
  el?.pause()
  showPlayback.value = false
}

async function publish() {
  errorMsg.value = ''
  successMsg.value = ''

  if (!title.value.trim()) {
    errorMsg.value = i18n.t('record_video_required')
    return
  }
  if (!category.value) {
    errorMsg.value = i18n.t('record_video_required')
    return
  }
  if (!recordedBlob.value) {
    errorMsg.value = i18n.t('record_video_required')
    return
  }

  publishing.value = true
  uploadProgress.value = 0
  try {
    const fd = new FormData()
    const ext = recordedBlob.value.type.includes('mp4') ? 'mp4' : 'webm'
    fd.append('file', recordedBlob.value, `record-${Date.now()}.${ext}`)

    const { data: upload } = await api.post('/api/videos/upload-video', fd, {
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

    await api.post('/api/videos', {
      title: title.value.trim(),
      category: category.value,
      content_type: 'record',
      url: upload.url,
      duration_sec: recordDuration.value,
      file_size: upload.size,
    })

    successMsg.value = i18n.t('record_video_publish_success')
    setTimeout(() => router.push('/videos'), 1200)
  } catch (e: any) {
    errorMsg.value =
      e?.response?.data?.detail ||
      e?.message ||
      i18n.t('record_video_publish_failed')
  } finally {
    publishing.value = false
  }
}

function formatDuration(sec: number): string {
  const m = Math.floor(sec / 60)
  const s = sec % 60
  const pad = (n: number) => n.toString().padStart(2, '0')
  return `${pad(m)}:${pad(s)}`
}

function goBack() {
  router.back()
}

onMounted(async () => {
  await loadCameras()
  await startPreview()
})

onBeforeUnmount(() => {
  stopRecording()
  stopStream()
  if (recordTimer) clearInterval(recordTimer)
  if (recordedUrl.value) URL.revokeObjectURL(recordedUrl.value)
})
</script>

<template>
  <div class="recorder-page">
    <header class="top-bar">
      <button type="button" class="back-btn" @click="goBack">‹</button>
      <h1 class="page-title">{{ i18n.t('record_video_page_title') }}</h1>
      <span class="spacer" />
    </header>

    <div class="main-body">
      <div v-if="errorMsg" class="notice notice-error">{{ errorMsg }}</div>
      <div v-if="successMsg" class="notice notice-ok">{{ successMsg }}</div>

      <section class="card title-card">
        <input
          v-model="title"
          type="text"
          class="title-input"
          :placeholder="i18n.t('publish_video_title_ph')"
          maxlength="200"
        />
      </section>

      <!-- ★ 分类选择：COMBOX -->
      <section class="card category-card">
        <CategorySelect
          v-model="category"
          storage-key="fdq95_record_category"
          :placeholder="i18n.t('publish_video_category') || 'Select category'"
        />
      </section>

      <section class="card video-card">
        <div class="video-frame">
          <video
            ref="videoEl"
            class="preview-video"
            :style="{ filter: previewFilter }"
            autoplay
            playsinline
            muted
          />
          <div v-if="loading" class="video-overlay">
            <span>{{ i18n.t('video_loading') }}</span>
          </div>
          <div v-else-if="cameraError" class="video-overlay err">
            <span>{{ cameraError }}</span>
          </div>

          <div v-if="isRecording" class="rec-indicator">
            <span class="dot"></span>
            <span class="time">{{ formatDuration(recordDuration) }}</span>
          </div>
        </div>
      </section>

      <section class="card controls-card">
        <button
          type="button"
          class="record-btn"
          :class="{ recording: isRecording }"
          :disabled="loading || !!cameraError"
          @click="toggleRecording"
        >
          <span class="record-icon"></span>
          <span class="record-text">
            {{
              isRecording
                ? i18n.t('record_video_stop')
                : i18n.t('record_video_start')
            }}
          </span>
        </button>

        <div class="aux-grid">
          <button
            type="button"
            class="aux-btn"
            :disabled="isRecording || loading || cameras.length < 2"
            @click="switchCamera"
          >
            <span class="aux-icon">🔄</span>
            <span class="aux-label">{{ i18n.t('record_video_switch_camera') }}</span>
          </button>

          <button
            type="button"
            class="aux-btn"
            :class="{ active: useBeauty }"
            :disabled="isRecording"
            @click="toggleBeauty"
          >
            <span class="aux-icon">✨</span>
            <span class="aux-label">{{ i18n.t('record_video_beauty') }}</span>
          </button>

          <button
            type="button"
            class="aux-btn"
            :class="{ active: useAudio }"
            :disabled="isRecording"
            @click="toggleAudio"
          >
            <span class="aux-icon">{{ useAudio ? '🎤' : '🔇' }}</span>
            <span class="aux-label">
              {{
                useAudio
                  ? i18n.t('record_video_audio_on')
                  : i18n.t('record_video_audio_off')
              }}
            </span>
          </button>

          <button
            type="button"
            class="aux-btn"
            :class="{ active: useTorch }"
            :disabled="isRecording || !torchSupported"
            @click="toggleTorch"
          >
            <span class="aux-icon">{{ useTorch ? '🔦' : '💡' }}</span>
            <span class="aux-label">
              {{
                useTorch
                  ? i18n.t('record_video_torch_on')
                  : i18n.t('record_video_torch_off')
              }}
            </span>
          </button>
        </div>
      </section>

      <section class="card action-card">
        <div v-if="publishing" class="upload-progress-wrap">
          <div class="upload-progress-track">
            <div
              class="upload-progress-fill"
              :style="{ width: uploadProgress + '%' }"
            ></div>
          </div>
          <div class="upload-progress-text">
            <span>{{ i18n.t('publish_video_uploading') }}</span>
            <span class="pct">{{ uploadProgress }}%</span>
          </div>
        </div>

        <div class="action-row">
          <button
            type="button"
            class="action-btn playback"
            :disabled="!canPlayback"
            @click="openPlayback"
          >
            <span class="action-icon">▶</span>
            <span>{{ i18n.t('record_video_playback') }}</span>
          </button>
          <button
            type="button"
            class="action-btn publish"
            :disabled="!canPublish"
            @click="publish"
          >
            <span class="action-icon">📤</span>
            <span>{{ publishing ? '…' : i18n.t('record_video_publish') }}</span>
          </button>
        </div>
      </section>
    </div>

    <div v-if="showPlayback" class="fullscreen-playback">
      <div class="fs-header">
        <h3>{{ i18n.t('record_video_playback') }}</h3>
        <button type="button" class="fs-close" @click="closePlayback" aria-label="Close">✕</button>
      </div>
      <video
        id="playback-video"
        class="fs-video"
        :src="recordedUrl"
        controls
        playsinline
        autoplay
      />
    </div>
  </div>
</template>

<style scoped>
.recorder-page {
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
  padding: 0.5rem 1rem;
  background: #000;
  flex: 0 0 auto;
}
.back-btn {
  background: transparent;
  border: none;
  color: #fff;
  font-size: 1.9rem;
  line-height: 1;
  cursor: pointer;
  width: 32px;
  height: 32px;
  border-radius: 6px;
  padding: 0;
}
.back-btn:hover { background: rgba(255, 255, 255, 0.08); }
.page-title {
  flex: 1;
  text-align: right;
  margin: 0;
  font-size: 0.95rem;
  font-weight: 500;
}
.spacer { width: 32px; }

.main-body {
  flex: 1 1 auto;
  min-height: 0;
  display: flex;
  flex-direction: column;
  gap: 0.4rem;
  padding: 0 0.5rem 0.5rem;
  overflow: hidden;
}

.notice {
  padding: 0.5rem 0.75rem;
  border-radius: 6px;
  font-size: 0.8rem;
  flex: 0 0 auto;
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

.card {
  background: #1a1a1a;
  border-radius: 10px;
  padding: 0.5rem;
  flex: 0 0 auto;
}

.title-card { padding: 0.4rem 0.6rem; }
.title-input {
  width: 100%;
  background: #0d0d0d;
  border: 1px solid rgba(255, 255, 255, 0.12);
  border-radius: 6px;
  color: #fff;
  padding: 0.45rem 0.75rem;
  font-size: 0.95rem;
  font-weight: 600;
  text-align: center;
  box-sizing: border-box;
}
.title-input:focus { outline: none; border-color: #8b5cf6; }

/* ★ 分类卡片：COMBOX */
.category-card { padding: 0.5rem 0.6rem; }

.video-card {
  flex: 1 1 auto;
  min-height: 0;
  padding: 0.35rem;
  display: flex;
  flex-direction: column;
}
.video-frame {
  position: relative;
  width: 100%;
  height: 100%;
  min-height: 0;
  background: #000;
  border-radius: 8px;
  overflow: hidden;
  display: flex;
  align-items: center;
  justify-content: center;
}
.preview-video {
  width: 100%;
  height: 100%;
  object-fit: contain;
  background: #000;
  display: block;
}
.video-overlay {
  position: absolute;
  inset: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  background: rgba(0, 0, 0, 0.6);
  color: #fff;
  font-size: 0.85rem;
  padding: 1rem;
  text-align: center;
}
.video-overlay.err { color: #ff8a80; }

.rec-indicator {
  position: absolute;
  top: 0.5rem;
  left: 0.5rem;
  display: flex;
  align-items: center;
  gap: 0.35rem;
  background: rgba(0, 0, 0, 0.6);
  padding: 0.2rem 0.5rem;
  border-radius: 20px;
  font-size: 0.75rem;
  font-family: ui-monospace, monospace;
}
.rec-indicator .dot {
  width: 9px;
  height: 9px;
  border-radius: 50%;
  background: #8b5cf6;
  animation: blink 1s infinite;
}
@keyframes blink {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.3; }
}

.controls-card { padding: 0.55rem 0.5rem 0.5rem; }
.record-btn {
  width: 100%;
  padding: 0.65rem 1rem;
  background: #8b5cf6;
  color: #fff;
  border: none;
  border-radius: 10px;
  font-weight: 700;
  font-size: 0.92rem;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 0.5rem;
  transition: background 0.2s;
  box-shadow: 0 3px 10px rgba(139, 92, 246, 0.35);
}
.record-btn:hover { background: #7c3aed; }
.record-btn.recording {
  background: #6d28d9;
  box-shadow: 0 3px 10px rgba(109, 40, 217, 0.5);
}
.record-btn:disabled { opacity: 0.5; cursor: not-allowed; box-shadow: none; }

.record-icon {
  width: 14px;
  height: 14px;
  border-radius: 50%;
  background: #fff;
}
.record-btn.recording .record-icon {
  border-radius: 3px;
  animation: blink 1s infinite;
}
.record-text { white-space: nowrap; }

.aux-grid {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 0.35rem;
  margin-top: 0.5rem;
}
.aux-btn {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 0.15rem;
  background: rgba(255, 255, 255, 0.06);
  border: 1px solid rgba(255, 255, 255, 0.1);
  color: #fff;
  border-radius: 8px;
  padding: 0.4rem 0.2rem;
  cursor: pointer;
  font-size: 0.6rem;
  transition: all 0.15s;
  text-align: center;
}
.aux-btn:hover:not(:disabled) {
  background: rgba(255, 255, 255, 0.12);
  border-color: rgba(255, 255, 255, 0.2);
}
.aux-btn.active {
  background: rgba(139, 92, 246, 0.18);
  border-color: #8b5cf6;
  color: #c4b5fd;
}
.aux-btn:disabled { opacity: 0.35; cursor: not-allowed; }
.aux-icon { font-size: 1rem; }
.aux-label {
  line-height: 1.1;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  max-width: 100%;
}

.action-card {
  padding: 0.5rem;
  border: 1px solid rgba(139, 92, 246, 0.3);
  background: linear-gradient(
    135deg,
    rgba(139, 92, 246, 0.06),
    rgba(139, 92, 246, 0.02)
  );
}

.upload-progress-wrap {
  margin-bottom: 0.5rem;
  padding: 0.4rem 0.55rem;
  background: rgba(0, 0, 0, 0.35);
  border-radius: 8px;
}
.upload-progress-track {
  width: 100%;
  height: 8px;
  background: rgba(255, 255, 255, 0.12);
  border-radius: 4px;
  overflow: hidden;
  position: relative;
}
.upload-progress-fill {
  height: 100%;
  background: linear-gradient(90deg, #8b5cf6, #a78bfa);
  border-radius: 4px;
  transition: width 0.2s ease-out;
  position: relative;
}
.upload-progress-fill::after {
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
.upload-progress-text {
  margin-top: 0.3rem;
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-size: 0.78rem;
  color: #c4b5fd;
  font-weight: 600;
}
.upload-progress-text .pct {
  font-family: ui-monospace, monospace;
  color: #e5b80b;
}

.action-row {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 0.5rem;
}
.action-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 0.4rem;
  padding: 0.55rem 0.4rem;
  border-radius: 9px;
  font-weight: 700;
  font-size: 0.82rem;
  cursor: pointer;
  border: none;
  transition: all 0.15s;
}
.action-btn.playback {
  background: rgba(255, 255, 255, 0.1);
  color: #fff;
  border: 1px solid rgba(255, 255, 255, 0.18);
}
.action-btn.playback:hover:not(:disabled) {
  background: rgba(255, 255, 255, 0.16);
}
.action-btn.publish {
  background: #8b5cf6;
  color: #fff;
  box-shadow: 0 3px 10px rgba(139, 92, 246, 0.4);
}
.action-btn.publish:hover:not(:disabled) { background: #7c3aed; }
.action-btn:disabled {
  opacity: 0.35;
  cursor: not-allowed;
  box-shadow: none;
}
.action-icon { font-size: 0.95rem; }

/* 全屏回放 */
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
  padding: 0.6rem 1rem;
  background: linear-gradient(
    to bottom,
    rgba(0, 0, 0, 0.75) 0%,
    rgba(0, 0, 0, 0) 100%
  );
  pointer-events: none;
}
.fs-header h3 {
  margin: 0;
  font-size: 0.95rem;
  font-weight: 500;
  color: #fff;
  text-shadow: 0 1px 4px rgba(0, 0, 0, 0.9);
  pointer-events: auto;
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

@media (max-width: 480px) {
  .top-bar { padding: 0.35rem 0.6rem; }
  .page-title { font-size: 0.85rem; }
  .back-btn { font-size: 1.6rem; width: 28px; height: 28px; }
  .spacer { width: 28px; }
  .main-body { gap: 0.3rem; padding: 0 0.4rem 0.4rem; }
  .card { padding: 0.4rem; border-radius: 8px; }
  .title-card { padding: 0.35rem 0.5rem; }
  .title-input { padding: 0.38rem 0.6rem; font-size: 0.88rem; }
  .category-card { padding: 0.4rem 0.5rem; }
  .video-card { padding: 0.25rem; }
  .controls-card { padding: 0.45rem 0.4rem 0.4rem; }
  .record-btn { padding: 0.55rem 0.9rem; font-size: 0.85rem; }
  .record-icon { width: 12px; height: 12px; }
  .aux-grid { gap: 0.3rem; margin-top: 0.4rem; }
  .aux-btn { padding: 0.35rem 0.15rem; font-size: 0.56rem; border-radius: 7px; }
  .aux-icon { font-size: 0.9rem; }
  .action-card { padding: 0.4rem; }
  .action-row { gap: 0.4rem; }
  .action-btn { padding: 0.5rem 0.3rem; font-size: 0.76rem; border-radius: 8px; }
  .action-icon { font-size: 0.88rem; }
  .upload-progress-text { font-size: 0.72rem; }
  .fs-header { padding: 0.5rem 0.7rem; }
  .fs-header h3 { font-size: 0.85rem; }
  .fs-close { width: 32px; height: 32px; font-size: 1rem; }
}

@media (max-height: 640px) {
  .category-card { display: none; }
  .main-body { gap: 0.25rem; }
  .card { padding: 0.35rem; }
}
</style>