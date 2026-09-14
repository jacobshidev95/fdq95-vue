<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useI18nStore } from '@/stores/i18n'
import { useAuthStore } from '@/stores/auth'
import { useProfileStore } from '@/stores/profile'
import { api } from '@/api/client'

const router = useRouter()
const auth = useAuthStore()
const profile = useProfileStore()
const i18n = useI18nStore()

const scanning = ref(false)
const error = ref('')
const progress = ref(0)

async function startLogin() {
  error.value = ''
  scanning.value = true
  progress.value = 0

  const cached = localStorage.getItem('fdq95_face_credential')
  if (!cached) {
    error.value = i18n.t('no_face_credential')
    scanning.value = false
    return
  }

  const timer = window.setInterval(() => {
    progress.value = Math.min(progress.value + 12, 100)
  }, 120)

  try {
    // Simulate scanning delay
    await new Promise((resolve) => setTimeout(resolve, 1400))

    const { data } = await api.post('/api/auth/face/login', {
      face_credential_id: cached,
    })
    auth.token = data.access_token
    localStorage.setItem('fdq95_token', data.access_token)
    await auth.fetchMe()
    await profile.loadMe()
    router.push('/profile')
  } catch {
    error.value = i18n.t('face_login_failed')
  } finally {
    window.clearInterval(timer)
    scanning.value = false
  }
}
</script>

<template>
  <div class="face-page">
    <div class="top-bar">
      <button class="back-btn" @click="router.push('/login')">←</button>
      <span class="title">{{ i18n.t('face_login_title') }}</span>
    </div>

    <div class="camera-area">
      <div class="camera-frame" :class="{ scanning }">
        <span class="face-icon" aria-hidden="true">😊</span>
        <div v-if="scanning" class="scan-line" />
      </div>
      <p class="hint">{{ i18n.t('face_login_hint') }}</p>
    </div>

    <div v-if="scanning" class="progress-bar">
      <div class="progress-fill" :style="{ width: progress + '%' }" />
    </div>

    <div v-if="error" class="notice notice-error">{{ error }}</div>

    <button
      class="btn btn-primary btn-block"
      :disabled="scanning"
      @click="startLogin"
    >
      {{ scanning ? i18n.t('face_scanning') : i18n.t('face_login_button') }}
    </button>

    <p class="hint">
      <router-link to="/face/enroll">
        {{ i18n.t('face_setup_link') }}
      </router-link>
    </p>
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