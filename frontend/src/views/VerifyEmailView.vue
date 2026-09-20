<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { api } from '@/api/client'
import { useI18nStore } from '@/stores/i18n'

const i18n = useI18nStore()
const route = useRoute()
const router = useRouter()

type Status = 'verifying' | 'success' | 'error'
const status = ref<Status>('verifying')
const message = ref('')

/** 安全地从 query 中取出 token（可能是 string | string[] | null） */
function readToken(): string {
  const raw = route.query.token
  if (Array.isArray(raw)) return raw[0] ?? ''
  if (typeof raw === 'string') return raw
  return ''
}

/** 从错误响应里提取人类可读的 detail */
function extractDetail(e: any): string | null {
  const detail = e?.response?.data?.detail
  if (typeof detail === 'string' && detail) return detail
  if (Array.isArray(detail) && detail.length > 0) {
    const first = detail[0]
    if (typeof first === 'string') return first
    if (first && typeof first === 'object' && typeof first.msg === 'string') {
      return first.msg
    }
  }
  return null
}

onMounted(async () => {
  const token = readToken()

  if (!token) {
    status.value = 'error'
    message.value =
      i18n.t('verify_missing_token') || 'Missing verification token in the URL.'
    return
  }

  try {
    // FastAPI-Users: POST /auth/verify   body {"token": "..."}
    await api.post('/auth/verify', { token })
    status.value = 'success'
    message.value =
      i18n.t('verify_success') || 'Your email has been verified. You can log in now.'
  } catch (e: any) {
    status.value = 'error'
    message.value =
      extractDetail(e) ||
      i18n.t('verify_failed') ||
      'Verification failed or the link has expired. Please register again or contact support.'
  }
})

function goLogin() {
  router.push('/login')
}

function goHome() {
  router.push('/')
}
</script>

<template>
  <div class="verify-wrapper">
    <div class="card verify-card">
      <h2 class="title-gold">
        {{ i18n.t('verify_email') || 'Email Verification' }}
      </h2>

      <div v-if="status === 'verifying'" class="notice">
        {{ i18n.t('verify_in_progress') || 'Verifying your email…' }}
      </div>

      <div v-else-if="status === 'success'" class="notice notice-ok">
        ✓ {{ message }}
      </div>

      <div v-else class="notice notice-error">
        ✗ {{ message }}
      </div>

      <!-- 成功时显示"去登录"，失败时显示"回首页" -->
      <button
        v-if="status === 'success'"
        class="btn btn-primary btn-block"
        @click="goLogin"
      >
        {{ i18n.t('go_to_login') || 'Go to Login' }}
      </button>

      <button
        v-else-if="status === 'error'"
        class="btn btn-outline btn-block"
        @click="goHome"
      >
        {{ i18n.t('go_home') || 'Back to Home' }}
      </button>
    </div>
  </div>
</template>

<style scoped>
.verify-wrapper {
  display: flex;
  justify-content: center;
  align-items: flex-start;
  padding: 3rem 1rem;
  min-height: 60vh;
}
.verify-card {
  width: 100%;
  max-width: 420px;
  text-align: center;
}
.notice {
  padding: 0.9rem 1rem;
  border-radius: 8px;
  margin: 1rem 0;
  font-size: 0.95rem;
  background: rgba(255, 255, 255, 0.04);
  color: var(--text);
  border: 1px solid var(--border);
}
.notice-ok {
  background: rgba(46, 204, 113, 0.12);
  color: #4ade80;
  border-color: rgba(46, 204, 113, 0.4);
}
.notice-error {
  background: rgba(231, 76, 60, 0.12);
  color: #ff8a80;
  border-color: rgba(231, 76, 60, 0.4);
}
.btn-block {
  width: 100%;
  margin-top: 1rem;
}
</style>