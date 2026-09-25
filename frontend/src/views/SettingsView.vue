<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { api } from '@/api/client'
import { useI18nStore } from '@/stores/i18n'

const router = useRouter()
const i18n = useI18nStore()

interface ChannelProfile {
  user_string_id: string
  display_name: string
  avatar_url: string | null
  follower_count: number
}

const profile = ref<ChannelProfile | null>(null)

async function loadProfile() {
  try {
    const { data } = await api.get('/api/profile/me')
    profile.value = {
      user_string_id: data.user_string_id,
      display_name: data.display_name,
      avatar_url: data.avatar_url,
      follower_count: data.follower_count ?? 0,
    }
  } catch (e) {
    console.warn('[Settings] load profile failed', e)
  }
}

function goBack() {
  router.push('/videos')
}

function goLikes() { router.push('/settings/likes') }
function goFollows() { router.push('/settings/follows') }
function goMessages() { router.push('/settings/messages') }
function goDMs() { router.push('/settings/dms') }

function goChannel() { router.push('/settings/channel') }
function goChannelNotifs() { router.push('/settings/channel/notifications') }
function goChannelDMs() { router.push('/settings/channel/dms') }
function goCreatorCenter() { router.push('/settings/creator-center') }

function goPublishVideo() { router.push('/settings/publish-video') }
// ★ 改动：点击"发起直播"转到跳板页，它会自动创建 session 并跳进 /live/:roomId/host
function goGoLive() { router.push('/settings/go-live') }
function goLaunchActivity() { router.push('/settings/launch-activity') }
function goPublishArticle() { router.push('/settings/publish-article') }

onMounted(loadProfile)
</script>

<template>
  <div class="settings-page">
    <header class="top-bar">
      <button class="back-btn" @click="goBack">‹</button>
      <h1 class="page-title">{{ i18n.t('settings_title') }}</h1>
      <span class="spacer" />
    </header>

    <div class="scroll-body">
      <section class="grid-card">
        <button class="grid-item" @click="goLikes">
          <span class="grid-label">{{ i18n.t('settings_likes') }}</span>
          <span class="grid-arrow">›</span>
        </button>
        <button class="grid-item" @click="goFollows">
          <span class="grid-label">{{ i18n.t('settings_follows') }}</span>
          <span class="grid-arrow">›</span>
        </button>
        <button class="grid-item" @click="goMessages">
          <span class="grid-label">{{ i18n.t('settings_messages') }}</span>
          <span class="grid-arrow">›</span>
        </button>
        <button class="grid-item" @click="goDMs">
          <span class="grid-label">{{ i18n.t('settings_dms') }}</span>
          <span class="grid-arrow">›</span>
        </button>
      </section>

      <p class="section-caption">{{ i18n.t('settings_my_channel') }}</p>

      <section class="card">
        <button class="row-item channel-row" @click="goChannel">
          <div class="avatar">
            <img
              v-if="profile?.avatar_url"
              :src="profile.avatar_url"
              alt="avatar"
            />
            <span v-else class="avatar-fallback">
              {{ profile?.user_string_id?.slice(-2).toUpperCase() || '??' }}
            </span>
          </div>
          <div class="channel-meta">
            <div class="channel-name">
              {{ profile?.display_name || profile?.user_string_id || '—' }}
            </div>
            <div class="channel-followers">
              {{ profile?.follower_count ?? 0 }}
              {{ i18n.t('settings_followers') }}
            </div>
          </div>
          <span class="row-arrow">›</span>
        </button>

        <button class="row-item" @click="goChannelNotifs">
          <span class="row-label">{{ i18n.t('settings_channel_notifications') }}</span>
          <span class="row-arrow">›</span>
        </button>

        <button class="row-item" @click="goChannelDMs">
          <span class="row-label">{{ i18n.t('settings_channel_dms') }}</span>
          <span class="row-arrow">›</span>
        </button>

        <button class="row-item" @click="goCreatorCenter">
          <span class="row-label">{{ i18n.t('settings_creator_center') }}</span>
          <span class="row-arrow">›</span>
        </button>

        <div class="quad-actions">
          <button class="quad-item" @click="goPublishArticle">
            <span class="quad-icon">📄</span>
            <span class="quad-label">{{ i18n.t('settings_publish_article') }}</span>
          </button>
          <div class="quad-divider" />
          <button class="quad-item" @click="goPublishVideo">
            <span class="quad-icon">📷</span>
            <span class="quad-label">{{ i18n.t('settings_publish_video') }}</span>
          </button>
          <div class="quad-divider" />
          <button class="quad-item" @click="goGoLive">
            <span class="quad-icon">🔴</span>
            <span class="quad-label">{{ i18n.t('settings_go_live') }}</span>
          </button>
          <div class="quad-divider" />
          <button class="quad-item" @click="goLaunchActivity">
            <span class="quad-icon">🎉</span>
            <span class="quad-label">{{ i18n.t('settings_launch_activity') }}</span>
          </button>
        </div>
      </section>
    </div>
  </div>
</template>

<style scoped>
.settings-page {
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
  flex-shrink: 0;
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
  display: flex;
  align-items: center;
  justify-content: center;
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
  color: #fff;
}
.spacer { width: 36px; }

.scroll-body {
  flex: 1 1 auto;
  padding: 0 0.75rem 2rem;
  overflow-y: auto;
}

.grid-card {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 0.5rem;
  background: #1a1a1a;
  border-radius: 12px;
  padding: 0.5rem;
  margin-bottom: 1rem;
}
.grid-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  background: transparent;
  border: none;
  color: #fff;
  padding: 1rem 1rem;
  border-radius: 8px;
  font-size: 0.95rem;
  cursor: pointer;
  text-align: left;
  transition: background 0.15s;
}
.grid-item:hover { background: rgba(255, 255, 255, 0.06); }
.grid-label { font-weight: 500; }
.grid-arrow {
  color: rgba(255, 255, 255, 0.4);
  font-size: 1.1rem;
}

.section-caption {
  color: rgba(255, 255, 255, 0.5);
  font-size: 0.8rem;
  margin: 0.5rem 0.75rem 0.5rem;
}

.card {
  background: #1a1a1a;
  border-radius: 12px;
  overflow: hidden;
  margin-bottom: 1rem;
}

.row-item {
  display: flex;
  align-items: center;
  width: 100%;
  background: transparent;
  border: none;
  color: #fff;
  padding: 1rem 1rem;
  font-size: 0.95rem;
  cursor: pointer;
  text-align: left;
  border-bottom: 1px solid rgba(255, 255, 255, 0.05);
  transition: background 0.15s;
}
.row-item:hover { background: rgba(255, 255, 255, 0.05); }
.row-item:last-child { border-bottom: none; }

.row-label { flex: 1; }
.row-arrow {
  color: rgba(255, 255, 255, 0.4);
  font-size: 1.1rem;
  margin-left: 0.5rem;
}

.channel-row { padding: 0.9rem 1rem; }
.avatar {
  width: 52px;
  height: 52px;
  border-radius: 50%;
  background: #333;
  overflow: hidden;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  color: #fff;
  font-weight: 700;
  font-size: 0.85rem;
}
.avatar img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}
.channel-meta {
  flex: 1;
  margin-left: 0.75rem;
  min-width: 0;
}
.channel-name {
  color: #fff;
  font-size: 1rem;
  font-weight: 600;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
.channel-followers {
  color: rgba(255, 255, 255, 0.5);
  font-size: 0.8rem;
  margin-top: 0.15rem;
}

.quad-actions {
  display: flex;
  align-items: stretch;
  border-top: 1px solid rgba(255, 255, 255, 0.05);
}
.quad-item {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 0.3rem;
  background: transparent;
  border: none;
  color: #fff;
  padding: 1rem 0.3rem;
  cursor: pointer;
  transition: background 0.15s;
}
.quad-item:hover { background: rgba(255, 255, 255, 0.05); }
.quad-icon { font-size: 1.4rem; }
.quad-label {
  font-size: 0.72rem;
  font-weight: 500;
  text-align: center;
}
.quad-divider {
  width: 1px;
  background: rgba(255, 255, 255, 0.08);
  margin: 1rem 0;
  flex-shrink: 0;
}
</style>