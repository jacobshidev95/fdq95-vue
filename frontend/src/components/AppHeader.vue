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
// ★ Careers → Recruitment
const jobsButtonLabel = computed(() =>
  isJobsPage.value ? i18n.t('home') : i18n.t('recruitment'),
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
        class="btn nav-btn"
        @click="goLogin"
      >
        {{ i18n.t('login') }}
      </button>
      <template v-else>
        <button class="btn nav-btn" @click="logout">
          {{ i18n.t('logout') || 'Logout' }}
        </button>
      </template>

      <button class="btn nav-btn" @click="toggleJobsHome">
        {{ jobsButtonLabel }}
      </button>

      <select v-model="currentLang" class="lang-select nav-btn">
        <option v-for="(label, code) in LANGUAGES" :key="code" :value="code">
          {{ label }}
        </option>
      </select>

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

/* ★ 所有右侧控件：统一背景色 rgba(32,32,32,1.0) + 白字 + 不换行 */
.nav-btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-width: 130px;                 /* ★ 从 100px 加宽到 130px，容得下 Recruitment */
  padding: 0.4rem 0.75rem;
  background: rgba(32, 32, 32, 1.0); /* ★ 统一深色背景 */
  color: #ffffff;                    /* ★ 白色文字 */
  border: 1px solid var(--gold);
  border-radius: 6px;
  font-weight: 600;
  font-size: 0.85rem;
  text-align: center;
  white-space: nowrap;               /* ★ 禁止换行 */
  cursor: pointer;
  box-sizing: border-box;
  transition: background 0.15s, border-color 0.15s, color 0.15s;
}
.nav-btn:hover {
  background: rgba(50, 50, 50, 1.0);
  border-color: #ffffff;
  color: #ffffff;
}

/* Language 下拉框：与 Login/Recruitment 按钮完全同宽 */
.lang-select.nav-btn {
  flex: 0 0 130px;            /* ★ 关键：禁止 flex 拉伸 */
  width: 130px;
  min-width: 0;               /* ★ 打断 <select> 默认 min-width: auto */
  max-width: 130px;
  box-sizing: border-box;

  padding: 0.35rem 1.4rem 0.35rem 0.5rem;
  margin: 0;
  background-color: rgba(32, 32, 32, 1.0);
  color: #ffffff;
  border: 1px solid var(--gold);
  border-radius: 6px;
  font-weight: 600;
  font-size: 0.85rem;
  cursor: pointer;

  text-align: center;
  text-align-last: center;

  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;

  appearance: none;
  -webkit-appearance: none;
  -moz-appearance: none;

  /* 自定义右侧下拉箭头 */
  background-image:
    linear-gradient(45deg, transparent 50%, #fff 50%),
    linear-gradient(135deg, #fff 50%, transparent 50%);
  background-position: calc(100% - 14px) 50%, calc(100% - 9px) 50%;
  background-size: 5px 5px, 5px 5px;
  background-repeat: no-repeat;
}

/* 日期：纯白 + 深色描边，同宽 */
.date.nav-btn {
  color: #ffffff;
  font-weight: 700;
  letter-spacing: 0.03em;
  background: rgba(32, 32, 32, 1.0);
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
    display: inline-flex;
    align-items: center;
    justify-content: center;
    flex: 0 0 130px;              /* ★ 固定宽度，禁止拉伸 */
    width: 130px;
    min-width: 0;
    max-width: 130px;
    box-sizing: border-box;
    padding: 0.4rem 0.75rem;
    background: rgba(32, 32, 32, 1.0);
    color: #ffffff;
    border: 1px solid var(--gold);
    border-radius: 6px;
    font-weight: 600;
    font-size: 0.85rem;
    text-align: center;
    white-space: nowrap;
    cursor: pointer;
    transition: background 0.15s, border-color 0.15s;
  }
}
</style>