<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { api } from '@/api/client'
import { useI18nStore } from '@/stores/i18n'
import { useProfileStore } from '@/stores/profile'

const router = useRouter()
const i18n = useI18nStore()
const store = useProfileStore()

const bio = ref('')
const saving = ref(false)
const msg = ref('')
const err = ref('')

async function load() {
  try {
    const { data } = await api.get('/api/profile/me')
    bio.value = data.bio_line_1 || ''
  } catch (e) {
    console.warn('[ChannelProfile] load failed', e)
  }
}

async function saveBio() {
  saving.value = true
  msg.value = ''
  err.value = ''
  try {
    await api.patch('/api/profile/me', { bio_line_1: bio.value })
    msg.value = i18n.t('settings_saved')

    // ★ 主动刷新 store.me，让 ProfileView 显示最新 bio
    try {
      await store.loadMe()
    } catch {
      /* ignore */
    }
  } catch (e: any) {
    err.value = e?.response?.data?.detail || i18n.t('settings_save_failed')
  } finally {
    saving.value = false
  }
}

function goPublishVideo() { router.push('/settings/publish-video') }
function goGoLive() { router.push('/settings/go-live') }
function goLaunchActivity() { router.push('/settings/launch-activity') }

function goBack() { router.back() }

onMounted(load)
</script>

<template>
  <div class="channel-page">
    <header class="top-bar">
      <button class="back-btn" @click="goBack">‹</button>
      <h1 class="page-title">{{ i18n.t('settings_my_channel') }}</h1>
      <span class="spacer" />
    </header>

    <div class="content">
      <!-- 简介 -->
      <section class="card bio-card">
        <label class="field-label">{{ i18n.t('settings_bio') }}</label>
        <textarea
          v-model="bio"
          rows="3"
          :placeholder="i18n.t('settings_bio_placeholder')"
        />
        <div v-if="msg" class="notice ok">{{ msg }}</div>
        <div v-if="err" class="notice err">{{ err }}</div>
        <button class="save-btn" :disabled="saving" @click="saveBio">
          {{ saving ? '…' : i18n.t('save') }}
        </button>
      </section>

      <!-- 三个快捷操作按钮 -->
      <section class="card">
        <div class="triple-actions">
          <button class="triple-item" @click="goPublishVideo">
            <span class="triple-icon">📷</span>
            <span class="triple-label">{{ i18n.t('settings_publish_video') }}</span>
          </button>
          <div class="triple-divider" />
          <button class="triple-item" @click="goGoLive">
            <span class="triple-icon">🔴</span>
            <span class="triple-label">{{ i18n.t('settings_go_live') }}</span>
          </button>
          <div class="triple-divider" />
          <button class="triple-item" @click="goLaunchActivity">
            <span class="triple-icon">🎉</span>
            <span class="triple-label">{{ i18n.t('settings_launch_activity') }}</span>
          </button>
        </div>
      </section>
    </div>
  </div>
</template>

<style scoped>
.channel-page {
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

.card {
  background: #1a1a1a;
  border-radius: 12px;
  overflow: hidden;
  margin-bottom: 1rem;
}

.bio-card { padding: 1rem; }

.field-label {
  display: block;
  color: rgba(255, 255, 255, 0.6);
  font-size: 0.85rem;
  margin-bottom: 0.4rem;
}
textarea {
  width: 100%;
  background: #0d0d0d;
  border: 1px solid rgba(255, 255, 255, 0.12);
  border-radius: 8px;
  color: #fff;
  padding: 0.6rem 0.75rem;
  font-size: 0.9rem;
  font-family: inherit;
  resize: vertical;
  box-sizing: border-box;
}
textarea:focus { outline: none; border-color: #e5b80b; }

.save-btn {
  margin-top: 0.75rem;
  width: 100%;
  background: #e5b80b;
  color: #111;
  border: none;
  border-radius: 8px;
  padding: 0.65rem 1rem;
  font-weight: 600;
  font-size: 0.9rem;
  cursor: pointer;
}
.save-btn:disabled { opacity: 0.5; cursor: not-allowed; }

.triple-actions {
  display: flex;
  align-items: stretch;
}
.triple-item {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 0.4rem;
  background: transparent;
  border: none;
  color: #fff;
  padding: 1.25rem 0.5rem;
  cursor: pointer;
  transition: background 0.15s;
}
.triple-item:hover { background: rgba(255, 255, 255, 0.05); }
.triple-icon { font-size: 1.6rem; }
.triple-label {
  font-size: 0.85rem;
  font-weight: 500;
  text-align: center;
  white-space: nowrap;
}
.triple-divider {
  width: 1px;
  background: rgba(255, 255, 255, 0.08);
  margin: 1rem 0;
  flex-shrink: 0;
}

.notice {
  padding: 0.5rem 0.75rem;
  border-radius: 6px;
  margin-top: 0.5rem;
  font-size: 0.85rem;
}
.notice.ok { background: rgba(46, 204, 113, 0.15); color: #a5f5c6; }
.notice.err { background: rgba(231, 76, 60, 0.15); color: #ff8a80; }
</style>