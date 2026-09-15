<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useI18nStore } from '@/stores/i18n'
import { useAuthStore } from '@/stores/auth'
import { useProfileStore } from '@/stores/profile'
import { AxiosError } from 'axios'

const i18n = useI18nStore()
const auth = useAuthStore()
const profile = useProfileStore()
const router = useRouter()

const email = ref('')
const password = ref('')
const error = ref('')
const loading = ref(false)

// ---- face prompt dialog ----
const showFacePrompt = ref(false)
const dontShowAgain = ref(false)

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

    const dismissed =
      localStorage.getItem('fdq95_face_prompt_dismissed') === 'true'
    const enrolled = auth.user?.face_enrolled ?? false

    if (!enrolled && !dismissed) {
      showFacePrompt.value = true
    } else {
      router.push('/profile')
    }
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

function goForgotPassword() {
  router.push('/forgot-password')
}

function goRegister() {
  router.push('/register')
}

function goFaceRecognition() {
  const cached = localStorage.getItem('fdq95_face_credential')
  if (cached) {
    router.push('/face/login')
  } else {
    router.push('/face/enroll')
  }
}

function promptAdd() {
  showFacePrompt.value = false
  router.push('/face/enroll')
}

function promptCancel() {
  showFacePrompt.value = false
  router.push('/profile')
}

function onDontShowChange() {
  if (dontShowAgain.value) {
    localStorage.setItem('fdq95_face_prompt_dismissed', 'true')
  } else {
    localStorage.removeItem('fdq95_face_prompt_dismissed')
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

    <button
      class="btn btn-primary btn-block login-btn"
      :disabled="loading"
      @click="submit"
    >
      {{ i18n.t('login') }}
    </button>

    <!-- Three equal-width auxiliary buttons -->
    <div class="aux-actions">
      <button class="btn btn-outline aux-btn" @click="goForgotPassword">
        {{ i18n.t('forgot_password') }}
      </button>
      <button class="btn btn-outline aux-btn" @click="goRegister">
        {{ i18n.t('register') }}
      </button>
      <button class="btn btn-outline aux-btn" @click="goFaceRecognition">
        {{ i18n.t('face_recognition') }}
      </button>
    </div>
  </div>

  <!-- Face recognition prompt dialog -->
  <div v-if="showFacePrompt" class="modal-overlay">
    <div class="modal-card">
      <h3 class="modal-title">{{ i18n.t('face_recognition') }}</h3>
      <p class="modal-message">{{ i18n.t('face_prompt_message') }}</p>

      <div class="modal-actions">
        <button class="btn btn-primary modal-btn" @click="promptAdd">
          {{ i18n.t('add') }}
        </button>
        <button class="btn btn-outline modal-btn" @click="promptCancel">
          {{ i18n.t('cancel') }}
        </button>
      </div>

      <label class="dont-show">
        <input
          type="checkbox"
          v-model="dontShowAgain"
          @change="onDontShowChange"
        />
        <span>{{ i18n.t('dont_show_again') }}</span>
      </label>
    </div>
  </div>
</template>

<style scoped>
/* ▼▼▼ Width increased from 420px to 480px (+60px) ▼▼▼ */
.login-card {
  position: relative;
  width: 100%;
  max-width: 480px;
}
/* ▲▲▲ */

.card-title {
  text-align: center;
  margin: 0 0 1.25rem;
}
.login-btn {
  margin-top: 1.25rem;
}

/* Three equal-width aux buttons.
   flex: 1 1 0 makes each button share the extra 60px equally
   (≈ +20px per button at 480px card width). */
.aux-actions {
  display: flex;
  gap: 0.5rem;
  margin-top: 0.75rem;
}
.aux-btn {
  flex: 1 1 0;
  min-width: 0;
  padding: 0.5rem 0.25rem;
  font-size: 0.78rem;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.close-btn {
  position: absolute;
  top: 0.5rem;
  right: 0.75rem;
  background: transparent;
  border: none;
  color: var(--text-dim);
  font-size: 1.75rem;
  line-height: 1;
  padding: 0.15rem 0.5rem;
  cursor: pointer;
  transition: color 0.15s;
}
.close-btn:hover {
  color: var(--gold);
}

/* ---- modal ---- */
.modal-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.65);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 2000;
  padding: 1rem;
}
.modal-card {
  background: #2a2a2a;
  border: 1px solid var(--border);
  border-radius: 12px;
  padding: 1.5rem 1.5rem 1.25rem;
  max-width: 380px;
  width: 100%;
  text-align: center;
  box-shadow: 0 12px 40px rgba(0, 0, 0, 0.7);
}
.modal-title {
  color: var(--gold);
  margin: 0 0 0.75rem;
  font-size: 1.15rem;
}
.modal-message {
  color: var(--text);
  margin: 0 0 1.25rem;
  font-size: 0.92rem;
  line-height: 1.6;
}
.modal-actions {
  display: flex;
  gap: 0.75rem;
  margin-bottom: 1rem;
}
.modal-btn {
  flex: 1 1 0;
  padding: 0.6rem 1rem;
  font-size: 0.9rem;
}
.dont-show {
  display: inline-flex;
  align-items: center;
  gap: 0.5rem;
  color: var(--text-dim);
  font-size: 0.85rem;
  cursor: pointer;
  margin: 0;
}
.dont-show input {
  width: auto;
  margin: 0;
  accent-color: var(--gold);
}
</style>