<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useI18nStore } from '@/stores/i18n'
import { useAuthStore } from '@/stores/auth'
import { api } from '@/api/client'

const i18n = useI18nStore()
const auth = useAuthStore()
const router = useRouter()

type Mode = 'password' | 'face'
const mode = ref<Mode>('password')

const email = ref('')
const password = ref('')
const error = ref('')
const loading = ref(false)

// ---- face ----
const faceScanning = ref(false)
const faceProgress = ref(0)
const faceError = ref('')

const ADMIN_LEVELS = ['level_0', 'level_1', 'level_2']

async function goDashboard() {
  // verify the logged-in user is actually an admin
  await auth.fetchMe()
  if (!auth.user || !ADMIN_LEVELS.includes(auth.user.provider_level || '')) {
    error.value = i18n.t('admin_no_access')
    auth.logout()
    return
  }
  router.push('/admin/dashboard')
}

async function submit() {
  error.value = ''
  if (!email.value || !password.value) {
    error.value = i18n.t('please_fill_required')
    return
  }
  loading.value = true
  try {
    await auth.login(email.value, password.value)
    await goDashboard()
  } catch (e) {
    error.value = i18n.t('invalid_credentials')
  } finally {
    loading.value = false
  }
}

async function faceLogin() {
  faceError.value = ''
  faceScanning.value = true
  faceProgress.value = 0

  const credential = localStorage.getItem('fdq95_face_credential')
  if (!credential) {
    faceError.value = i18n.t('no_face_credential')
    faceScanning.value = false
    return
  }

  const timer = window.setInterval(() => {
    faceProgress.value = Math.min(faceProgress.value + 12, 100)
  }, 120)

  try {
    await new Promise((r) => setTimeout(r, 1400))
    const { data } = await api.post('/api/auth/face/login', {
      face_credential_id: credential,
    })
    auth.token = data.access_token
    localStorage.setItem('fdq95_token', data.access_token)
    await goDashboard()
  } catch {
    faceError.value = i18n.t('face_login_failed')
  } finally {
    window.clearInterval(timer)
    faceScanning.value = false
  }
}

onMounted(() => {
  // nothing
})
</script>

<template>
  <div class="admin-login-wrap">
    <div class="card admin-login-card">
      <h1 class="title-gold admin-title">🛡️ {{ i18n.t('admin_portal') }}</h1>
      <p class="admin-subtitle">{{ i18n.t('admin_login_subtitle') }}</p>

      <div class="mode-switch">
        <button
          class="mode-btn"
          :class="{ active: mode === 'password' }"
          @click="mode = 'password'"
        >
          {{ i18n.t('password_login') }}
        </button>
        <button
          class="mode-btn"
          :class="{ active: mode === 'face' }"
          @click="mode = 'face'"
        >
          {{ i18n.t('face_login_title') }}
        </button>
      </div>

      <!-- ---------- password mode ---------- -->
      <template v-if="mode === 'password'">
        <div v-if="error" class="notice notice-error">{{ error }}</div>

        <label>{{ i18n.t('email') }}</label>
        <input
          v-model="email"
          type="email"
          autocomplete="email"
          @keyup.enter="submit"
        />

        <label>{{ i18n.t('password') }}</label>
        <input
          v-model="password"
          type="password"
          autocomplete="current-password"
          @keyup.enter="submit"
        />

        <button
          class="btn btn-primary btn-block submit-btn"
          :disabled="loading"
          @click="submit"
        >
          {{ loading ? i18n.t('login') + '…' : i18n.t('login') }}
        </button>
      </template>

      <!-- ---------- face mode ---------- -->
      <template v-else>
        <div v-if="faceError" class="notice notice-error">{{ faceError }}</div>

        <div class="face-area">
          <div class="face-frame" :class="{ scanning: faceScanning }">
            <span class="face-icon">😊</span>
            <div v-if="faceScanning" class="scan-line" />
          </div>
          <p class="face-hint">{{ i18n.t('face_login_hint') }}</p>
        </div>

        <div v-if="faceScanning" class="progress-bar">
          <div class="progress-fill" :style="{ width: faceProgress + '%' }" />
        </div>

        <button
          class="btn btn-primary btn-block submit-btn"
          :disabled="faceScanning"
          @click="faceLogin"
        >
          {{ faceScanning ? i18n.t('face_scanning') : i18n.t('face_login_button') }}
        </button>
      </template>

      <p class="hint">
        <router-link to="/login">{{ i18n.t('back_to_login') }}</router-link>
      </p>
    </div>
  </div>
</template>

<style scoped>
.admin-login-wrap {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 3rem 1rem;
}
.admin-login-card {
  width: 100%;
  max-width: 440px;
}
.admin-title {
  text-align: center;
  margin: 0 0 0.35rem;
  font-size: 1.5rem;
}
.admin-subtitle {
  text-align: center;
  color: var(--text-dim);
  font-size: 0.85rem;
  margin: 0 0 1.25rem;
}

/* mode switch */
.mode-switch {
  display: flex;
  gap: 0.35rem;
  margin-bottom: 1rem;
  padding: 0.25rem;
  background: #1a1a1a;
  border: 1px solid var(--border);
  border-radius: 8px;
}
.mode-btn {
  flex: 1 1 0;
  padding: 0.5rem 0.5rem;
  background: transparent;
  border: none;
  border-radius: 6px;
  color: var(--text-dim);
  cursor: pointer;
  font-size: 0.85rem;
  transition: all 0.15s;
}
.mode-btn.active {
  background: var(--gold);
  color: #111;
  font-weight: 600;
}

.submit-btn {
  margin-top: 1.25rem;
}

.hint {
  text-align: center;
  margin-top: 1rem;
  font-size: 0.9rem;
}

/* face area */
.face-area {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 1rem 0;
}
.face-frame {
  width: 180px;
  height: 180px;
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
.face-frame.scanning {
  border-color: var(--gold);
  box-shadow: 0 0 0 6px rgba(229, 184, 11, 0.15);
}
.face-icon {
  font-size: 5rem;
  opacity: 0.5;
}
.scan-line {
  position: absolute;
  left: 0;
  right: 0;
  height: 3px;
  background: linear-gradient(90deg, transparent, var(--gold), transparent);
  animation: scan 1.4s ease-in-out infinite;
}
@keyframes scan {
  0% { top: 10%; }
  50% { top: 90%; }
  100% { top: 10%; }
}
.face-hint {
  color: var(--text-dim);
  font-size: 0.85rem;
  margin-top: 0.75rem;
  text-align: center;
  max-width: 320px;
}
.progress-bar {
  width: 100%;
  height: 5px;
  background: #333;
  border-radius: 3px;
  overflow: hidden;
  margin-top: 0.5rem;
}
.progress-fill {
  height: 100%;
  background: var(--gold);
  transition: width 0.15s linear;
}

.notice {
  padding: 0.7rem 1rem;
  border-radius: 6px;
  margin: 0.75rem 0;
  font-size: 0.88rem;
}
.notice-error {
  background: rgba(231, 76, 60, 0.15);
  border: 1px solid #e74c3c;
  color: #ff8a80;
}
</style>