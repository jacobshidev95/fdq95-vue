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
const avatarHue = computed(() => {
  const id = store.viewing?.user_string_id || store.me?.user_string_id || ''
  let h = 0
  for (const c of id) h = (h * 31 + c.charCodeAt(0)) % 360
  return h
})

const isAdmin = computed(
  () =>
    auth.user?.provider_level === 'level_0' ||
    auth.user?.provider_level === 'level_1' ||
    auth.user?.provider_level === 'level_2',
)

async function load() {
  if (!store.me) await store.loadMe()
  if (targetUserId.value && !isSelf.value) {
    await store.loadUser(targetUserId.value)
  } else {
    store.resetViewing()
  }
}

onMounted(load)
watch(targetUserId, load)

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

function goActivityReplay() {
  const id = isSelf.value ? store.me?.user_string_id : store.viewing?.user_string_id
  if (id) router.push(`/user/${id}/activity-replay`)
}

function goProducts() {
  const id = isSelf.value ? store.me?.user_string_id : store.viewing?.user_string_id
  if (id) router.push(`/user/${id}/products`)
}

function goLaunchActivity() {
  router.push('/activities/new')
}

function goAdminUsers() {
  router.push('/admin/dashboard')
}

async function addFriend() {
  const id = store.viewing?.user_string_id
  if (!id) return
  try {
    await store.sendFriendRequest(id)
    alert(i18n.t('friend_request_sent'))
  } catch {
    alert(i18n.t('friend_request_failed'))
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
            {{ (isSelf ? store.me : store.viewing)?.display_name }}
          </div>
          <div class="handle">
            @{{ (isSelf ? store.me : store.viewing)?.user_string_id }}
          </div>
        </div>
      </div>

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

    <div class="bio">
      <p class="bio-line">{{ (isSelf ? store.me : store.viewing)?.bio_line_1 }}</p>
      <p class="bio-line">{{ (isSelf ? store.me : store.viewing)?.bio_line_2 }}</p>
    </div>

    <div v-if="!isSelf" class="action-row">
      <button
        class="btn action-btn"
        :class="{ active: store.following }"
        @click="store.toggleFollow()"
      >
        {{ store.following ? i18n.t('following') : i18n.t('follow') }}
      </button>
      <button class="btn action-btn" @click="goMessages">
        {{ i18n.t('message') }}
      </button>
    </div>

    <button
      v-if="!isSelf"
      class="btn btn-primary add-friend-btn"
      @click="addFriend"
    >
      {{ i18n.t('add_as_friend') }}
    </button>

    <nav class="nav-grid">
      <button class="nav-tile" @click="router.push('/profile')">
        🏠 {{ i18n.t('personal_home') }}
      </button>
      <button class="nav-tile" @click="goUserVideos">
        🎬 {{ i18n.t('video_list') }}
      </button>
      <button class="nav-tile" @click="goLaunchActivity">
        📅 {{ i18n.t('launch_activity') }}
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
      <button
        v-if="isAdmin"
        class="nav-tile admin-tile"
        @click="goAdminUsers"
      >
        🛡️ {{ i18n.t('admin_users_title') }}
      </button>
    </nav>
  </div>
</template>

<style scoped>
.profile-page {
  width: 100%;
  max-width: 640px;
  padding: 1rem 1.25rem 3rem;
}

.profile-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 1rem;
}
.avatar-block {
  display: flex;
  align-items: center;
  gap: 0.85rem;
}
.avatar {
  width: 72px;
  height: 72px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #fff;
  font-weight: 800;
  font-size: 1.25rem;
  border: 3px solid var(--gold);
}
.display-name {
  color: #fff;
  font-size: 1.05rem;
  font-weight: 700;
}
.handle {
  color: var(--text-dim);
  font-size: 0.85rem;
}

.menu-wrap {
  position: relative;
}
.menu-btn {
  background: transparent;
  border: 1px solid var(--border);
  color: var(--text);
  border-radius: 6px;
  width: 36px;
  height: 32px;
  font-size: 1.2rem;
  cursor: pointer;
}
.menu-btn:hover {
  border-color: var(--gold);
  color: var(--gold);
}
.menu-panel {
  position: absolute;
  right: 0;
  top: calc(100% + 6px);
  background: #1e1e1e;
  border: 1px solid var(--border);
  border-radius: 8px;
  padding: 0.35rem;
  min-width: 220px;
  display: flex;
  flex-direction: column;
  gap: 0.15rem;
  z-index: 10;
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.5);
}
.menu-panel button {
  background: transparent;
  border: none;
  color: var(--text);
  padding: 0.5rem 0.75rem;
  text-align: left;
  cursor: pointer;
  border-radius: 4px;
  font-size: 0.88rem;
}
.menu-panel button:hover {
  background: rgba(229, 184, 11, 0.15);
  color: var(--gold);
}
.slide-down-enter-active,
.slide-down-leave-active {
  transition: all 0.15s ease;
}
.slide-down-enter-from,
.slide-down-leave-to {
  opacity: 0;
  transform: translateY(-6px);
}

.bio {
  margin-bottom: 1rem;
}
.bio-line {
  color: var(--text-dim);
  font-size: 0.9rem;
  margin: 0.15rem 0;
}

.action-row {
  display: flex;
  gap: 0.6rem;
  margin-bottom: 0.6rem;
}
.action-btn {
  flex: 1 1 0;
  padding: 0.65rem 1rem;
  border: 1px solid var(--gold);
  color: var(--gold);
  background: transparent;
  border-radius: 8px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.15s;
}
.action-btn:hover,
.action-btn.active {
  background: var(--gold);
  color: #111;
}

.add-friend-btn {
  width: 100%;
  margin-bottom: 1.25rem;
  padding: 0.7rem 1rem;
  border-radius: 8px;
}

.nav-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 0.5rem;
  margin-top: 0.5rem;
}
.nav-tile {
  padding: 0.85rem 0.5rem;
  background: var(--bg-soft);
  border: 1px solid var(--border);
  border-radius: 8px;
  color: var(--text);
  font-size: 0.88rem;
  cursor: pointer;
  transition: all 0.15s;
}
.nav-tile:hover {
  border-color: var(--gold);
  color: var(--gold);
}
.nav-tile.admin-tile {
  border-color: rgba(229, 184, 11, 0.5);
  background: rgba(229, 184, 11, 0.06);
  color: var(--gold);
}

@media (max-width: 480px) {
  .nav-grid {
    grid-template-columns: 1fr;
  }
}
</style>