<script setup lang="ts">
import { computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useI18nStore, LANGUAGES } from '@/stores/i18n'
import { useAuthStore } from '@/stores/auth'

const i18n = useI18nStore()
const auth = useAuthStore()
const route = useRoute()
const router = useRouter()

const today = new Date().toISOString().slice(0, 10)

const currentLang = computed({
  get: () => i18n.language,
  set: (v: string) => i18n.setLanguage(v),
})

const isJobsPage = computed(() => route.path === '/jobs')
const jobsButtonLabel = computed(() =>
  isJobsPage.value ? i18n.t('home') : i18n.t('careers'),
)

function goLogin() {
  router.push('/login')
}
function toggleJobsHome() {
  router.push(isJobsPage.value ? '/' : '/jobs')
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
      <span class="title-gold">{{ i18n.t('welcome_title') }}</span>
    </div>

    <div class="right">
      <button
        v-if="!auth.isAuthenticated"
        class="btn btn-outline nav-btn"
        @click="goLogin"
      >
        {{ i18n.t('login') }}
      </button>
      <template v-else>
        <span class="user">{{ auth.user?.user_id || auth.user?.email }}</span>
        <button class="btn btn-outline nav-btn" @click="logout">Logout</button>
      </template>

      <button class="btn btn-outline nav-btn" @click="toggleJobsHome">
        {{ jobsButtonLabel }}
      </button>

      <!-- Language select: after nav-btn, same width as nav-btn -->
      <select v-model="currentLang" class="lang-select nav-btn">
        <option v-for="(label, code) in LANGUAGES" :key="code" :value="code">
          {{ label }}
        </option>
      </select>

      <!-- Date: pure white with edge; width matches nav-btn -->
      <span class="date nav-btn">{{ today }}</span>
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
  font-size: 1.1rem;
  letter-spacing: 0.05em;
  white-space: nowrap;
}

.right {
  display: flex;
  align-items: center;
  justify-content: flex-end;
  gap: 0.75rem;
  flex-wrap: wrap;
}

/* Every control in the right cluster shares the same width */
.nav-btn {
  min-width: 100px;
  width: 100px;
  text-align: center;
  justify-content: center;
}

/* Language dropdown — styled as a button of the same width */
.lang-select.nav-btn {
  padding: 0.35rem 0.5rem;
  margin: 0;
  background: #1e1e1e;
  color: var(--text);
  border: 1px solid var(--gold);
  border-radius: 6px;
  font-weight: 600;
  font-size: 0.85rem;
  cursor: pointer;
}

/* Date — pure white, edge via text-shadow, same width */
.date.nav-btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  color: #ffffff;
  font-weight: 700;
  font-size: 0.85rem;
  letter-spacing: 0.03em;
  text-shadow:
    1px 1px 0 #000,
    -1px 1px 0 #000,
    1px -1px 0 #000,
    -1px -1px 0 #000,
    0 1px 0 #000,
    0 -1px 0 #000,
    1px 0 0 #000,
    -1px 0 0 #000;
}

.user {
  color: var(--text-dim);
  font-size: 0.9rem;
}

@media (max-width: 900px) {
  .header {
    grid-template-columns: 1fr;
    text-align: center;
  }
  .left, .right {
    justify-content: center;
  }
  .title-gold {
    font-size: 1rem;
    white-space: normal;
  }
  .nav-btn {
    min-width: 90px;
    width: 90px;
  }
}
</style>