<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useI18nStore } from '@/stores/i18n'
import { useAuthStore } from '@/stores/auth'
import { useProfileStore } from '@/stores/profile'
import { AxiosError } from 'axios'
import { api } from '@/api/client'

const i18n = useI18nStore()
const auth = useAuthStore()
const profile = useProfileStore()
const router = useRouter()

const email = ref('')
const password = ref('')
const error = ref('')
const loading = ref(false)
const showFaceLogin = ref(false)

function close() {
  router.push('/')
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
    await profile.loadMe()
    router.push('/profile')
  } catch (e) {
    const ax = e as AxiosError
    error.value =
      ax.response?.status === 400 || ax.response?.status === 401
        ? i18n.t('invalid_credentials')
        : ax.message || i18n.t('invalid_credentials')
  } finally {
    loading.value = false
  }
}

async function faceLogin() {
  error.value = ''
  try {
    // In production, integrate FaceIO / WebAuthn here.
    const credentialId = prompt(i18n.t('face_login_prompt'))
    if (!credentialId) return
    const { data } = await api.post('/api/auth/face/login', {
      face_credential_id: credentialId,
    })
    auth.token = data.access_token
    localStorage.setItem('fdq95_token', data.access_token)
    await profile.loadMe()
    router.push('/profile')
  } catch {
    error.value = i18n.t('face_login_failed')
  }
}
</script>

<template>
  <div class="card login-card">
    <button class="close-btn" aria-label="Close" @click="close">×</button>
    <h2 class="title-gold card-title">{{ i18n.t('login') }}</h2>

    <div v-if="error" class="notice notice-error">{{ error }}</div>

    <label>{{ i18n.t('email') }}</label>
    <input v-model="email" type="email" autocomplete="email" />

    <label>{{ i18n.t('password') }}</label>
    <input
      v-model="password"
      type="password"
      autocomplete="current-password"
      @keyup.enter="submit"
    />

    <button class="btn btn-primary btn-block" :disabled="loading" @click="submit">
      {{ i18n.t('login') }}
    </button>

    <!-- ---- forgot password ---- -->
    <p class="forgot-row">
      <router-link to="/forgot-password" class="forgot-link">
        {{ i18n.t('forgot_password') }}
      </router-link>
    </p>

    <!-- ---- face recognition login ---- -->
    <div class="face-login">
      <button class="face-toggle" @click="showFaceLogin = !showFaceLogin">
        {{ i18n.t('enable_face_login') }}
      </button>
      <div v-if="showFaceLogin" class="face-panel">
        <p class="face-hint">{{ i18n.t('face_login_hint') }}</p>
        <button class="btn btn-outline btn-block" @click="faceLogin">
          {{ i18n.t('face_login_button') }}
        </button>
      </div>
    </div>

    <p class="hint">
      <router-link to="/register">{{ i18n.t('register') }}</router-link>
    </p>
  </div>
</template>

<style scoped>
.login-card { position: relative; width: 100%; max-width: 420px; }
.card-title { text-align: center; margin: 0 0 1.25rem; }
.hint { text-align: center; margin-top: 1rem; font-size: 0.9rem; }
.forgot-row { text-align: right; margin: 0.5rem 0 0; font-size: 0.85rem; }
.forgot-link { color: var(--gold); }
.face-login { margin-top: 1.25rem; border-top: 1px solid var(--border); padding-top: 1rem; }
.face-toggle { background: transparent; border: none; color: var(--text-dim); font-size: 0.85rem; cursor: pointer; text-decoration: underline; }
.face-panel { margin-top: 0.75rem; }
.face-hint { color: var(--text-dim); font-size: 0.82rem; margin-bottom: 0.5rem; }
.close-btn { position: absolute; top: 0.5rem; right: 0.75rem; background: transparent; border: none; color: var(--text-dim); font-size: 1.75rem; cursor: pointer; }
.close-btn:hover { color: var(--gold); }
</style>