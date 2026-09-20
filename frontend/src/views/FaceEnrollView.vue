<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { useI18nStore } from '@/stores/i18n'

const router = useRouter()
const auth = useAuthStore()
const i18n = useI18nStore()

const scanning = ref(false)
const progress = ref(0)
const error = ref('')
const success = ref(false)

function generateCredential(): string {
  // In production, integrate FaceIO / WebAuthn here.
  const random = crypto.getRandomValues(new Uint8Array(16))
  return Array.from(random)
    .map((b) => b.toString(16).padStart(2, '0'))
    .join('')
}

async function startEnroll() {
  error.value = ''
  success.value = false
  scanning.value = true
  progress.value = 0

  const timer = window.setInterval(() => {
    progress.value = Math.min(progress.value + 10, 100)
  }, 150)

  try {
    // Simulate sampling delay
    await new Promise((resolve) => setTimeout(resolve, 1600))

    const credentialId = generateCredential()
    await auth.enrollFace(credentialId)

    // Cache credential for future face login
    localStorage.setItem('fdq95_face_credential', credentialId)
    localStorage.setItem('fdq95_face_prompt_dismissed', 'true')

    success.value = true
  } catch {
    error.value = i18n.t('face_enroll_failed')
  } finally {
    window.clearInterval(timer)
    progress.value = 100
    scanning.value = false
  }
}

onMounted(() => {
  // Enrollment requires an authenticated session
  if (!auth.isAuthenticated) {
    router.push('/login')
  }
})
</script>

<template>
  <div class="face-page">
    <div class="top-bar">
      <button class="back-btn" @click="router.back()">←</button>
      <span class="title">{{ i18n.t('face_enroll_title') }}</span>
    </div>

    <div class="camera-area">
      <div class="camera-frame" :class="{ scanning }">
        <span class="face-icon" aria-hidden="true">😊</span>
        <div v-if="scanning" class="scan-line" />
      </div>
      <p class="hint">{{ i18n.t('face_enroll_hint') }}</p>
    </div>

    <div v-if="scanning" class="progress-bar">
      <div class="progress-fill" :style="{ width: progress + '%' }" />
    </div>

    <div v-if="error" class="notice notice-error">{{ error }}</div>
    <div v-if="success" class="notice notice-ok">
      {{ i18n.t('face_enroll_success') }}
    </div>

    <button
      v-if="!success"
      class="btn btn-primary btn-block"
      :disabled="scanning"
      @click="startEnroll"
    >
      {{ scanning ? i18n.t('face_scanning') : i18n.t('face_capture') }}
    </button>
    <button
      v-else
      class="btn btn-primary btn-block"
      @click="router.push('/profile')"
    >
      {{ i18n.t('continue_to_profile') }}
    </button>
  </div>
</template>

<style scoped>
.face-page {
  width: 100%;
  max-width: 520px;
  padding: 1rem 1.25rem 3rem;
  display: flex;
  flex-direction: column;
  align-items: center;
}
.top-bar {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  width: 100%;
  margin-bottom: 1.5rem;
}
.back-btn {
  background: transparent;
  border: 1px solid var(--border);
  color: var(--text);
  padding: 0.35rem 0.75rem;
  border-radius: 6px;
  cursor: pointer;
}
.title {
  color: var(--gold);
  font-weight: 700;
}
.camera-area {
  display: flex;
  flex-direction: column;
  align-items: center;
  margin-bottom: 1.25rem;
}
.camera-frame {
  width: 220px;
  height: 220px;
  border-radius: 50%;
  border: 3px solid var(--border);
  background: #1a1a1a;
  display: flex;
  align-items: center;
  justify-content: center;
  position: relative;
  overflow: hidden;
  transition: border-color 0.2s;
}
.camera-frame.scanning {
  border-color: var(--gold);
  box-shadow: 0 0 0 6px rgba(229, 184, 11, 0.15);
}
.face-icon {
  font-size: 6rem;
  opacity: 0.5;
}
.scan-line {
  position: absolute;
  left: 0;
  right: 0;
  height: 3px;
  background: linear-gradient(
    90deg,
    transparent,
    var(--gold),
    transparent
  );
  animation: scan 1.4s ease-in-out infinite;
}
@keyframes scan {
  0% { top: 10%; }
  50% { top: 90%; }
  100% { top: 10%; }
}
.hint {
  color: var(--text-dim);
  font-size: 0.88rem;
  margin-top: 1rem;
  text-align: center;
  max-width: 320px;
  line-height: 1.6;
}
.progress-bar {
  width: 100%;
  max-width: 320px;
  height: 6px;
  background: #333;
  border-radius: 3px;
  overflow: hidden;
  margin-bottom: 1rem;
}
.progress-fill {
  height: 100%;
  background: var(--gold);
  transition: width 0.15s linear;
}
.notice {
  width: 100%;
  max-width: 380px;
}
.btn {
  max-width: 320px;
}
</style>