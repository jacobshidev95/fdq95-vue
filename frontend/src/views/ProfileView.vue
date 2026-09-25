<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useProfileStore } from '@/stores/profile'
import { useAuthStore } from '@/stores/auth'
import { useI18nStore } from '@/stores/i18n'

const route = useRoute()
const router = useRouter()
const store = useProfileStore()
const auth = useAuthStore()
const i18n = useI18nStore()

const targetUserId = computed(() => (route.params.userId as string) || '')
const isSelf = computed(
  () => !targetUserId.value || targetUserId.value === store.me?.user_string_id,
)

const menuOpen = ref(false)
const loading = ref(false)
const loadError = ref('')

const avatarHue = computed(() => {
  const id = store.viewing?.user_string_id || store.me?.user_string_id || ''
  let h = 0
  for (const c of id) h = (h * 31 + c.charCodeAt(0)) % 360
  return h
})

type FriendBtnState = 'idle' | 'pending' | 'friend'
const friendBtnState = computed<FriendBtnState>(() => {
  if (store.isFriend) return 'friend'
  if (store.hasPendingRequest) return 'pending'
  return 'idle'
})

const friendBtnText = computed(() => {
  switch (friendBtnState.value) {
    case 'friend': return i18n.t('friend_status_friend')
    case 'pending': return i18n.t('friend_status_pending')
    default: return i18n.t('add_as_friend')
  }
})

const friendBtnDisabled = computed(() => friendBtnState.value !== 'idle')

async function load() {
  loadError.value = ''
  loading.value = true
  try {
    try {
      await store.loadMe()
    } catch (e: any) {
      console.warn('[ProfileView] loadMe failed:', e?.response?.status)
    }
    try {
      await store.loadFriends()
    } catch { /* ignore */ }

    if (targetUserId.value && !isSelf.value) {
      try {
        await store.loadUser(targetUserId.value)
      } catch (e: any) {
        const status = e?.response?.status
        const detail = e?.response?.data?.detail
        if (status === 401) {
          loadError.value = i18n.t('profile_login_required')
        } else if (status === 404) {
          loadError.value = `用户 @${targetUserId.value} 不存在`
        } else {
          loadError.value = detail || i18n.t('profile_load_failed')
        }
      }
      try {
        await store.loadFriendStatus(targetUserId.value)
      } catch { /* ignore */ }
    } else {
      store.resetViewing()
    }
  } finally {
    loading.value = false
  }
}

onMounted(load)
watch(targetUserId, load)

function goLogin() {
  router.push({ path: '/login', query: { redirect: route.fullPath } })
}

function goMessages() {
  const id = isSelf.value ? store.me?.user_string_id : store.viewing?.user_string_id
  if (id) router.push(`/messages/${id}`)
}

function goFriendList() {
  router.push('/friends')
}

function goUserVideos() {
  const id = isSelf.value ? store.me?.user_string_id : store.viewing?.user_string_id
  if (id) router.push(`/user/${id}/videos`)
}

function goUserArticles() {
  const id = isSelf.value ? store.me?.user_string_id : store.viewing?.user_string_id
  if (id) router.push(`/user/${id}/articles`)
}

// ★ 新增：跳转到该用户的 Live 回放列表
function goLiveReplay() {
  const id = isSelf.value ? store.me?.user_string_id : store.viewing?.user_string_id
  if (id) router.push(`/user/${id}/live-replays`)
}

function goActivityReplay() {
  const id = isSelf.value ? store.me?.user_string_id : store.viewing?.user_string_id
  if (id) router.push(`/user/${id}/activity-replay`)
}

function goProducts() {
  const id = isSelf.value ? store.me?.user_string_id : store.viewing?.user_string_id
  if (id) router.push(`/user/${id}/products`)
}

function goVideoPlay() {
  router.push('/videos')
}

function goArticleBrowse() {
  router.push('/articles')
}

async function addFriend() {
  if (friendBtnDisabled.value) {
    if (friendBtnState.value === 'pending') {
      alert(i18n.t('friend_request_already_sent'))
    } else if (friendBtnState.value === 'friend') {
      alert(i18n.t('friend_already'))
    }
    return
  }
  const id = store.viewing?.user_string_id
  if (!id) return
  if (!auth.token) {
    alert(i18n.t('profile_login_required'))
    goLogin()
    return
  }
  try {
    const res: any = await store.sendFriendRequest(id)
    if (res?.status === 'already_friends') {
      alert(i18n.t('friend_already'))
    } else if (res?.status === 'pending') {
      alert(i18n.t('friend_request_already_sent'))
    } else {
      alert(i18n.t('friend_request_sent'))
    }
  } catch (e: any) {
    alert(e?.response?.data?.detail || i18n.t('friend_request_failed'))
  }
}

async function onToggleFollow() {
  if (!store.viewing?.user_string_id) return
  if (!auth.token) {
    alert(i18n.t('profile_login_required'))
    goLogin()
    return
  }
  try {
    await store.toggleFollow()
  } catch {
    alert(i18n.t('action_failed_retry'))
  }
}

function shareToWeChat() {
  const url = window.location.href
  window.location.href = `weixin://dl/business/?u=${encodeURIComponent(url)}`
  navigator.clipboard.writeText(url).catch(() => {})
  menuOpen.value = false
}

function shareToWhatsApp() {
  const url = encodeURIComponent(window.location.href)
  const text = encodeURIComponent(i18n.t('recommend_whatsapp_text'))
  window.open(`https://wa.me/?text=${text}%20${url}`, '_blank')
  menuOpen.value = false
}

function complaint() {
  if (!store.me?.real_verified && !auth.user?.real_name) {
    alert(i18n.t('complaint_requires_real_name'))
    return
  }
  const subject = encodeURIComponent('Complaint from FDQ95 user')
  const body = encodeURIComponent(
    `Reporting user: ${store.viewing?.user_string_id}\n\nReason:\n`,
  )
  window.location.href = `mailto:complaint@fdq95.com?subject=${subject}&body=${body}`
  menuOpen.value = false
}
</script>

<template>
  <div class="profile-page">
    <div v-if="loading" class="state-banner">{{ i18n.t('video_loading') }}</div>

    <div v-else-if="loadError" class="state-banner error">
      <p>{{ loadError }}</p>
      <button v-if="!auth.token" class="btn btn-primary" @click="goLogin">
        {{ i18n.t('login') }}
      </button>
      <button v-else class="btn btn-outline" @click="load">
        {{ i18n.t('video_retry') }}
      </button>
    </div>

    <template v-else>
      <!-- Header -->
      <div class="profile-header">
        <div class="avatar-block">
          <div
            class="avatar"
            :style="{ background: `hsl(${avatarHue},60%,45%)` }"
          >
            {{
              (isSelf ? store.me : store.viewing)?.user_string_id?.slice(-2) || '??'
            }}
          </div>
          <div class="id-block">
            <div class="display-name">
              {{ (isSelf ? store.me : store.viewing)?.display_name || '—' }}
            </div>
            <div class="handle">
              @{{ (isSelf ? store.me : store.viewing)?.user_string_id || '—' }}
              <span v-if="!isSelf && store.isFriend" class="friend-badge">
                {{ i18n.t('friend_status_friend') }}
              </span>
            </div>
          </div>
        </div>

        <div class="header-actions">
          <button class="article-browse-btn" @click="goArticleBrowse">
            📄 {{ i18n.t('article_browse') }}
          </button>
          <button class="video-play-btn" @click="goVideoPlay">
            ▶ {{ i18n.t('play_video') }}
          </button>
          <div class="menu-wrap">
            <button class="menu-btn" @click="menuOpen = !menuOpen">⋯</button>
            <transition name="slide-down">
              <div v-if="menuOpen" class="menu-panel">
                <button @click="shareToWeChat">🤝 {{ i18n.t('recommend_to_wechat') }}</button>
                <button @click="shareToWhatsApp">🤝 {{ i18n.t('recommend_to_whatsapp') }}</button>
                <button @click="complaint">⚠️ {{ i18n.t('complaint') }}</button>
                <button @click="menuOpen = false">✕ {{ i18n.t('cancel') }}</button>
              </div>
            </transition>
          </div>
        </div>
      </div>

      <!-- bio -->
      <div class="bio">
        <p class="bio-line">{{ (isSelf ? store.me : store.viewing)?.bio_line_1 || '' }}</p>
        <p class="bio-line">{{ (isSelf ? store.me : store.viewing)?.bio_line_2 || '' }}</p>
      </div>

      <!-- 3 action buttons -->
      <div v-if="!isSelf" class="action-row">
        <button
          class="action-btn follow-btn"
          :class="{ following: store.following }"
          @click="onToggleFollow"
        >
          {{ store.following ? i18n.t('unfollow') : i18n.t('follow') }}
        </button>
        <button class="action-btn message-btn" @click="goMessages">
          {{ i18n.t('message') }}
        </button>
        <button
          class="action-btn"
          :class="{
            'friend-btn': friendBtnState === 'idle',
            'friend-btn-pending': friendBtnState === 'pending',
            'friend-btn-friend': friendBtnState === 'friend',
          }"
          :disabled="friendBtnDisabled"
          @click="addFriend"
        >
          {{ friendBtnText }}
        </button>
      </div>

      <!-- ★ 导航按钮：Live Replay 在 Activity Replay 之前 -->
      <nav class="nav-grid">
        <button class="nav-tile" @click="router.push('/profile')">
          🏠 {{ i18n.t('personal_home') }}
        </button>
        <button class="nav-tile" @click="goUserArticles">
          📄 {{ i18n.t('article_list') }}
        </button>
        <button class="nav-tile" @click="goUserVideos">
          🎬 {{ i18n.t('video_list') }}
        </button>
        <button class="nav-tile" @click="goLiveReplay">
          📺 {{ i18n.t('live_replay') }}
        </button>
        <button class="nav-tile" @click="goActivityReplay">
          🔁 {{ i18n.t('activity_replay') }}
        </button>
        <button class="nav-tile" @click="goProducts">
          🛒 {{ i18n.t('product_list') }}
        </button>
        <button class="nav-tile" @click="goFriendList">
          👥 {{ i18n.t('friend_list') }}
        </button>
      </nav>
    </template>
  </div>
</template>

<style scoped>
.profile-page {
  width: 100%;
  max-width: 640px;
  padding: 1rem 1.25rem 3rem;
  box-sizing: border-box;
}

.state-banner {
  padding: 2rem 1rem;
  text-align: center;
  color: var(--text-dim);
  font-size: 0.95rem;
}
.state-banner.error { color: #ff8a80; }
.state-banner button { margin-top: 1rem; }

.profile-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 0.5rem;
  margin-bottom: 1rem;
  flex-wrap: wrap;
}
.avatar-block { display: flex; align-items: center; gap: 0.85rem; min-width: 0; }
.avatar {
  width: 72px; height: 72px;
  border-radius: 50%;
  display: flex; align-items: center; justify-content: center;
  color: #fff; font-weight: 800; font-size: 1.25rem;
  border: 3px solid var(--gold);
  flex-shrink: 0;
}
.display-name { color: #fff; font-size: 1.05rem; font-weight: 700; }
.handle {
  color: var(--text-dim);
  font-size: 0.85rem;
  display: flex; align-items: center; gap: 0.4rem;
}

.friend-badge {
  display: inline-block;
  background: #2ecc71; color: #fff;
  font-size: 0.68rem; font-weight: 700;
  padding: 0.1rem 0.4rem; border-radius: 4px;
  line-height: 1.2;
}

.header-actions {
  display: flex; align-items: center;
  gap: 0.4rem;
  flex-wrap: wrap;
}
.article-browse-btn,
.video-play-btn {
  background: transparent;
  border: 1px solid var(--gold);
  color: var(--gold);
  border-radius: 6px;
  padding: 0.35rem 0.7rem;
  font-size: 0.82rem;
  cursor: pointer;
  white-space: nowrap;
}
.article-browse-btn:hover,
.video-play-btn:hover { background: var(--gold); color: #111; }

.menu-wrap { position: relative; }
.menu-btn {
  background: transparent;
  border: 1px solid var(--border);
  color: var(--text);
  border-radius: 6px;
  width: 36px; height: 32px;
  font-size: 1.2rem; cursor: pointer;
}
.menu-btn:hover { border-color: var(--gold); color: var(--gold); }
.menu-panel {
  position: absolute; right: 0; top: calc(100% + 6px);
  background: #1e1e1e;
  border: 1px solid var(--border);
  border-radius: 8px; padding: 0.35rem;
  min-width: 220px;
  display: flex; flex-direction: column; gap: 0.15rem;
  z-index: 10;
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.5);
}
.menu-panel button {
  background: transparent; border: none; color: var(--text);
  padding: 0.5rem 0.75rem; text-align: left;
  cursor: pointer; border-radius: 4px; font-size: 0.88rem;
}
.menu-panel button:hover {
  background: rgba(229, 184, 11, 0.15); color: var(--gold);
}
.slide-down-enter-active,
.slide-down-leave-active { transition: all 0.15s ease; }
.slide-down-enter-from,
.slide-down-leave-to { opacity: 0; transform: translateY(-6px); }

.bio { margin-bottom: 1rem; }
.bio-line {
  color: #fff;
  font-size: 0.9rem;
  margin: 0.15rem 0;
  white-space: pre-line;
  word-break: break-word;
}

.action-row {
  display: flex;
  gap: 0.5rem;
  margin-bottom: 1rem;
  flex-wrap: wrap;
}
.action-btn {
  flex: 1 1 30%;
  min-width: 90px;
  padding: 0.65rem 0.4rem;
  border: 1px solid transparent;
  border-radius: 8px;
  font-weight: 600;
  font-size: 0.88rem;
  cursor: pointer;
  white-space: nowrap;
}
.action-btn:disabled { cursor: not-allowed; }

.follow-btn { background: #2ecc71; border-color: #2ecc71; color: #fff; }
.follow-btn:hover { background: #27ae60; border-color: #27ae60; }
.follow-btn.following { background: #666; border-color: #666; color: #ddd; }
.follow-btn.following:hover { background: #555; border-color: #555; }

.message-btn { background: #666; border-color: #666; color: #fff; }
.message-btn:hover { background: #555; border-color: #555; }

.friend-btn { background: #2ecc71; border-color: #2ecc71; color: #fff; }
.friend-btn:hover { background: #27ae60; border-color: #27ae60; }
.friend-btn-pending {
  background: #888; border-color: #888;
  color: #ddd; opacity: 0.75;
}
.friend-btn-friend {
  background: #444; border-color: #555;
  color: #aaa; opacity: 0.7;
}

/* ★ 导航网格：7 个按钮 → 4 列两行，不换行 */
.nav-grid {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 0.4rem;
  margin-top: 0.5rem;
}
.nav-tile {
  padding: 0.6rem 0.3rem;
  background: var(--bg-soft);
  border: 1px solid var(--border);
  border-radius: 8px;
  color: var(--text);
  font-size: 0.7rem;
  line-height: 1.25;
  cursor: pointer;
  text-align: center;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
.nav-tile:hover { border-color: var(--gold); color: var(--gold); }

/* ★ 中屏（平板）：3 列 */
@media (max-width: 720px) {
  .nav-grid { grid-template-columns: repeat(3, minmax(0, 1fr)); }
  .nav-tile { font-size: 0.7rem; padding: 0.65rem 0.3rem; }
}

/* ★ 小屏（手机）：2 列 */
@media (max-width: 480px) {
  .profile-page { padding: 1rem 0.75rem 2rem; }
  .avatar { width: 60px; height: 60px; font-size: 1rem; }
  .display-name { font-size: 0.98rem; }
  .handle { font-size: 0.78rem; }
  .action-btn { font-size: 0.78rem; padding: 0.55rem 0.3rem; min-width: 80px; }
  .nav-grid { grid-template-columns: repeat(2, minmax(0, 1fr)); }
  .nav-tile { font-size: 0.68rem; padding: 0.55rem 0.25rem; }
  .article-browse-btn,
  .video-play-btn { font-size: 0.72rem; padding: 0.3rem 0.5rem; }
}
</style>