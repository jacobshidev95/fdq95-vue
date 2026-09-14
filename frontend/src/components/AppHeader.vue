<script setup lang="ts">
import { computed } from 'vue'
import { useRouter } from 'vue-router'
import { useI18nStore, LANGUAGES } from '@/stores/i18n'
import { useAuthStore } from '@/stores/auth'

const i18n = useI18nStore()
const auth = useAuthStore()
const router = useRouter()

const today = new Date().toISOString().slice(0, 10)

const currentLang = computed({
  get: () => i18n.language,
  set: (v: string) => i18n.setLanguage(v),
})

function goLogin() {
  router.push('/login')
}

function logout() {
  auth.logout()
  router.push('/')
}
</script>

<template>
  <header class="header">
    <div class="left">
      <span class="logo" aria-hidden="true">🌐</span>
      <span class="brand">Logo</span>
    </div>

    <div class="center">
      <span class="title-gold">FDQ95</span>
    </div>

    <div class="right">
      <select v-model="currentLang" class="lang-select">
        <option v-for="(label, code) in LANGUAGES" :key="code" :value="code">
          {{ label }}
        </option>
      </select>

      <button v-if="!auth.isAuthenticated" class="btn btn-outline" @click="goLogin">
        {{ i18n.t('login') }}
      </button>
      <template v-else>
        <span class="user">{{ auth.user?.user_id || auth.user?.email }}</span>
        <button class="btn btn-outline" @click="logout">Logout</button>
      </template>

      <span class="date">{{ today }}</span>
    </div>
  </header>
</template>

<style scoped>
.header {
  display: grid;
  grid-template-columns: 1fr auto 1fr;
  align-items: center;
  gap: 1rem;
  padding: 0.75rem 1.25rem;
  background: var(--bg-header);
  border-bottom: 1px solid var(--border);
}

.left {
  display: flex;
  align-items: center;
  gap: 0.5rem;
}
.logo {
  font-size: 1.5rem;
}
.brand {
  color: #fff;
  font-weight: 700;
}

.center {
  text-align: center;
}
.title-gold {
  font-size: 1.5rem;
  letter-spacing: 0.2em;
}

.right {
  display: flex;
  align-items: center;
  justify-content: flex-end;
  gap: 0.75rem;
  flex-wrap: wrap;
}
.lang-select {
  width: auto;
  margin: 0;
  padding: 0.35rem 0.5rem;
}
.date {
  color: var(--text-dim);
  font-size: 0.85rem;
}
.user {
  color: var(--text-dim);
  font-size: 0.9rem;
}

@media (max-width: 640px) {
  .header {
    grid-template-columns: 1fr;
    text-align: center;
  }
  .left, .right {
    justify-content: center;
  }
}
</style>
