<script setup lang="ts">
import { onBeforeUnmount, ref, watch } from 'vue'
import { useI18nStore } from '@/stores/i18n'

const i18n = useI18nStore()

const props = defineProps<{
  visible: boolean
  videoUrl: string
  durationSec: number
  sizeMB: number
}>()

const emit = defineEmits<{
  'update:visible': [v: boolean]
  confirm: []
  discard: []
}>()

const videoEl = ref<HTMLVideoElement | null>(null)
const isPlaying = ref(false)
const currentTime = ref(0)

function fmt(sec: number): string {
  const s = Math.max(0, Math.floor(sec || 0))
  const m = Math.floor(s / 60)
  const r = s % 60
  return `${m.toString().padStart(2, '0')}:${r.toString().padStart(2, '0')}`
}

function close(action: 'confirm' | 'discard') {
  const el = videoEl.value
  if (el) { el.pause() }
  emit('update:visible', false)
  if (action === 'confirm') emit('confirm')
  else emit('discard')
}

function onTimeUpdate() {
  const el = videoEl.value
  if (el) currentTime.value = el.currentTime
}

function onPlayPause() {
  const el = videoEl.value
  if (!el) return
  if (el.paused) { el.play(); isPlaying.value = true }
  else { el.pause(); isPlaying.value = false }
}

watch(
  () => props.visible,
  (v) => {
    if (!v && videoEl.value) videoEl.value.pause()
  }
)

onBeforeUnmount(() => {
  if (videoEl.value) videoEl.value.pause()
})
</script>

<template>
  <div v-if="visible" class="preview-backdrop">
    <div class="preview-modal">
      <div class="preview-header">
        <h3>{{ i18n.t('recording_preview_title') }}</h3>
        <button class="close-btn" @click="close('discard')">✕</button>
      </div>

      <div class="preview-body">
        <video
          ref="videoEl"
          :src="videoUrl"
          class="preview-video"
          controls
          playsinline
          @timeupdate="onTimeUpdate"
        />
      </div>

      <div class="preview-meta">
        <span>⏱ {{ fmt(durationSec) }}</span>
        <span>💾 {{ sizeMB.toFixed(1) }} MB</span>
      </div>

      <div class="preview-footer">
        <button class="btn ghost" @click="close('discard')">
          {{ i18n.t('recording_discard') }}
        </button>
        <button class="btn primary" @click="close('confirm')">
          {{ i18n.t('recording_publish') }}
        </button>
      </div>
    </div>
  </div>
</template>

<style scoped>
.preview-backdrop {
  position: fixed; inset: 0;
  background: rgba(0, 0, 0, 0.8);
  display: flex; align-items: center; justify-content: center;
  z-index: 300;
}
.preview-modal {
  width: 92%; max-width: 720px;
  max-height: 88vh;
  background: #111;
  border: 1px solid #333;
  border-radius: 12px;
  color: #fff;
  display: flex; flex-direction: column;
  overflow: hidden;
}
.preview-header {
  display: flex; align-items: center; justify-content: space-between;
  padding: 0.8rem 1rem;
  border-bottom: 1px solid #222;
}
.preview-header h3 { margin: 0; font-size: 1rem; }
.close-btn {
  background: transparent; border: none;
  color: #fff; font-size: 1.1rem; cursor: pointer;
}
.preview-body {
  flex: 1 1 auto;
  background: #000;
  display: flex; align-items: center; justify-content: center;
  min-height: 220px;
}
.preview-video {
  width: 100%;
  max-height: 60vh;
  display: block;
  background: #000;
}
.preview-meta {
  display: flex; gap: 1rem;
  padding: 0.5rem 1rem;
  font-size: 0.8rem;
  color: rgba(255, 255, 255, 0.7);
  border-bottom: 1px solid #222;
}
.preview-footer {
  display: flex; justify-content: flex-end; gap: 0.5rem;
  padding: 0.75rem 1rem;
}
.btn {
  padding: 0.5rem 1rem;
  border-radius: 8px;
  font-size: 0.85rem;
  font-weight: 600;
  cursor: pointer;
  border: 1px solid transparent;
}
.btn.ghost {
  background: transparent;
  border-color: rgba(255, 255, 255, 0.25);
  color: #ddd;
}
.btn.ghost:hover { border-color: #e74c3c; color: #ff8a80; }
.btn.primary {
  background: #8b5cf6;
  color: #fff;
}
.btn.primary:hover { background: #7c3aed; }
</style>