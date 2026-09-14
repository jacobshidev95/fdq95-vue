<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useI18nStore } from '@/stores/i18n'
import { useAuthStore } from '@/stores/auth'
import { AxiosError } from 'axios'

const i18n = useI18nStore()
const auth = useAuthStore()
const router = useRouter()

const email = ref('')
const password = ref('')
const error = ref('')
const loading = ref(false)

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
    router.push('/')
  } catch (e) {
    const ax = e as AxiosError
    error.value =
      ax.response?.status === 400 || ax.response?.status === 401
        ? i18n.t('invalid_credentials')
        : (ax.message || i18n.t('invalid_credentials'))
  } finally {
    loading.value = false
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

    <p class="hint">
      <router-link to="/register">{{ i18n.t('register') }}</router-link>
    </p>
  </div>
</template>

<style scoped>
.login-card {
  position: relative;
  width: 100%;
  max-width: 420px;
}
.card-title {
  text-align: center;
  margin: 0 0 1.25rem;
}
.hint {
  text-align: center;
  margin-top: 1rem;
  font-size: 0.9rem;
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
</style>