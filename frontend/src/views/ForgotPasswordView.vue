<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useI18nStore } from '@/stores/i18n'
import { api } from '@/api/client'

const i18n = useI18nStore()
const router = useRouter()

const email = ref('')
const loading = ref(false)
const sent = ref(false)
const error = ref('')

async function submit() {
  error.value = ''
  if (!email.value) {
    error.value = i18n.t('please_fill_required')
    return
  }
  loading.value = true
  try {
    await api.post('/api/auth/forgot-password', { email: email.value })
    sent.value = true
  } catch {
    // Always show success to avoid user enumeration
    sent.value = true
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <div class="card forgot-card">
    <button class="close-btn" @click="router.push('/login')">×</button>
    <h2 class="title-gold card-title">{{ i18n.t('forgot_password') }}</h2>

    <div v-if="sent" class="notice notice-ok">
      {{ i18n.t('reset_link_sent') }}
    </div>

    <template v-else>
      <div v-if="error" class="notice notice-error">{{ error }}</div>

      <!-- Description now reads: "Enter your email address below:" -->
      <p class="desc">{{ i18n.t('forgot_password_desc') }}</p>

      <input
        v-model="email"
        type="email"
        autocomplete="email"
        @keyup.enter="submit"
      />

      <button
        class="btn btn-primary btn-block"
        :disabled="loading"
        @click="submit"
      >
        {{ i18n.t('send_reset_link') }}
      </button>
    </template>

    <p class="hint">
      <router-link to="/login">{{ i18n.t('back_to_login') }}</router-link>
    </p>
  </div>
</template>

<style scoped>
.forgot-card {
  position: relative;
  width: 100%;
  max-width: 420px;
}
.card-title {
  text-align: center;
  margin: 0 0 1.25rem;
}
.desc {
  color: var(--text-dim);
  font-size: 0.9rem;
  line-height: 1.6;
  margin: 0 0 0.5rem;
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
  cursor: pointer;
}
.close-btn:hover {
  color: var(--gold);
}
</style>