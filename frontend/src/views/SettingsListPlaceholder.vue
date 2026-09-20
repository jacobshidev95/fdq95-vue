<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { api } from '@/api/client'
import { useI18nStore } from '@/stores/i18n'

const route = useRoute()
const router = useRouter()
const i18n = useI18nStore()

const loading = ref(false)
const errorMsg = ref('')
const items = ref<unknown[]>([])

// 从路由 meta 读取标题和 API 端点
const title = (route.meta.title as string) || ''
const apiPath = (route.meta.apiPath as string) || ''

async function load() {
  if (!apiPath) return
  loading.value = true
  errorMsg.value = ''
  try {
    const { data } = await api.get(apiPath)
    items.value = Array.isArray(data) ? data : data?.items ?? []
  } catch (e: any) {
    if (e?.response?.status === 401) {
      errorMsg.value = i18n.t('settings_need_login')
    } else if (e?.response?.status === 404) {
      errorMsg.value = i18n.t('settings_not_ready')
    } else {
      errorMsg.value = e?.response?.data?.detail || i18n.t('settings_load_failed')
    }
  } finally {
    loading.value = false
  }
}

function goBack() {
  router.back()
}

onMounted(load)
</script>

<template>
  <div class="list-page">
    <header class="top-bar">
      <button class="back-btn" @click="goBack">‹</button>
      <h1 class="page-title">{{ title }}</h1>
      <span class="spacer" />
    </header>

    <div class="content">
      <div v-if="loading" class="state">{{ i18n.t('settings_loading') }}</div>
      <div v-else-if="errorMsg" class="state error">{{ errorMsg }}</div>
      <div v-else-if="items.length === 0" class="state">
        {{ i18n.t('settings_empty_list') }}
      </div>
      <ul v-else class="items">
        <li v-for="(it, i) in items" :key="i" class="item">
          <pre>{{ it }}</pre>
        </li>
      </ul>
    </div>
  </div>
</template>

<style scoped>
.list-page {
  display: flex;
  flex-direction: column;
  width: 100%;
  min-height: 100vh;
  background: #000;
  color: #fff;
}
.top-bar {
  display: flex;
  align-items: center;
  padding: 0.8rem 1rem;
  background: #000;
  position: sticky;
  top: 0;
  z-index: 10;
}
.back-btn {
  background: transparent;
  border: none;
  color: #fff;
  font-size: 2rem;
  line-height: 1;
  cursor: pointer;
  width: 36px;
  height: 36px;
  border-radius: 6px;
  padding: 0;
}
.back-btn:hover { background: rgba(255, 255, 255, 0.08); }
.page-title {
  flex: 1;
  text-align: right;
  margin: 0;
  font-size: 1rem;
  font-weight: 500;
}
.spacer { width: 36px; }

.content { padding: 0 0.75rem 2rem; }
.state {
  padding: 3rem 1rem;
  text-align: center;
  color: rgba(255, 255, 255, 0.5);
  font-size: 0.9rem;
}
.state.error { color: #ff8a80; }

.items { list-style: none; padding: 0; margin: 0; }
.item {
  background: #1a1a1a;
  border-radius: 8px;
  padding: 0.75rem 1rem;
  margin-bottom: 0.5rem;
  font-size: 0.85rem;
  color: rgba(255, 255, 255, 0.8);
}
.item pre {
  margin: 0;
  white-space: pre-wrap;
  word-break: break-all;
  font-family: ui-monospace, monospace;
}
</style>