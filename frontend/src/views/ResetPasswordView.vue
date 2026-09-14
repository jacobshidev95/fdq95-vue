<script setup lang="ts">
import { ref, computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useI18nStore } from '@/stores/i18n'
import { api } from '@/api/client'

const i18n = useI18nStore()
const route = useRoute()
const router = useRouter()

const token = computed(() => String(route.query.token || ''))
const password = ref('')
const passwordConfirm = ref('')
const loading = ref(false)
const error = ref('')
const success = ref(false)

const match = computed(
  () => !passwordConfirm.value || password.value === passwordConfirm.value,
)

async function submit() {
  error.value = ''
  if (!token.value) {
    error.value = i18n.t('invalid_reset_link')
    return
  }
  if (password.value.length < 8) {
    error.value = i18n.t('password_too_short')
    return
  }
  if (password.value !== passwordConfirm.value) {
    error.value = i18n.t('passwords_do_not_match')
    return
  }
  loading.value = true
  try {
    await api.post('/api/auth/reset-password', {
      token: token.value,
      password: password.value,
    })
    success.value = true
    setTimeout(() => router.push('/login'), 2000)
  } catch (e: any) {
    error.value = e?.response?.data?.detail || i18n.t('reset_failed')
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <div class="card reset-card">
    <h2 class="title-gold card-title">{{ i18n.t('reset_password') }}</h2>

    <div v-if="success" class="notice notice-ok">
      {{ i18n.t('reset_success') }}
    </div>

    <template v-else>
      <div v-if="error" class="notice notice-error">{{ error }}</div>

      <label>{{ i18n.t('new_password') }}</label>
      <input v-model="password" type="password" autocomplete="new-password" />

      <label>{{ i18n.t('password_confirm') }}</label>
      <input
        v-model="passwordConfirm"
        type="password"
        autocomplete="new-password"
      />
      <p
        v-if="passwordConfirm"
        class="field-hint"
        :class="{ ok: match, err: !match }"
      >
        {{ match ? '✓ ' + i18n.t('passwords_match') : '✗ ' + i18n.t('passwords_do_not_match') }}
      </p>

      <button class="btn btn-primary btn-block" :disabled="loading" @click="submit">
        {{ i18n.t('reset_password') }}
      </button>
    </template>
  </div>
</template>

<style scoped>
.reset-card { width: 100%; max-width: 420px; }
.card-title { text-align: center; margin: 0 0 1.25rem; }
.field-hint { font-size: 0.78rem; margin: 0.15rem 0 0; }
.field-hint.ok { color: #2ecc71; }
.field-hint.err { color: #e74c3c; }
</style>