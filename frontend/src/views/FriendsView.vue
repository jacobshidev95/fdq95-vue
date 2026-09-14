<script setup lang="ts">
import { onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useProfileStore } from '@/stores/profile'
import { useI18nStore } from '@/stores/i18n'

const router = useRouter()
const store = useProfileStore()
const i18n = useI18nStore()

onMounted(async () => {
  if (!store.me) await store.loadMe()
  await store.loadFriends()
})

function hueFor(s: string): number {
  let h = 0
  for (const c of s) h = (h * 31 + c.charCodeAt(0)) % 360
  return h
}

function openFriend(userStringId: string) {
  router.push(`/profile/${userStringId}`)
}
</script>

<template>
  <div class="page">
    <div class="top-bar">
      <button class="back-btn" @click="router.push('/profile')">←</button>
      <span class="title">{{ i18n.t('friend_list') }}</span>
    </div>

    <p v-if="store.friends.length === 0" class="empty">
      {{ i18n.t('no_friends_yet') }}
    </p>

    <ul class="list">
      <li
        v-for="f in store.friends"
        :key="f.user_id"
        class="row"
        @click="openFriend(f.user_string_id)"
      >
        <div
          class="avatar"
          :style="{ background: `hsl(${hueFor(f.user_string_id)},60%,45%)` }"
        >
          {{ f.user_string_id.slice(-2) }}
        </div>
        <div class="meta">
          <div class="name">{{ f.display_name }}</div>
          <div class="handle">@{{ f.user_string_id }}</div>
        </div>
      </li>
    </ul>
  </div>
</template>

<style scoped>
.page {
  width: 100%;
  max-width: 560px;
  padding: 1rem 1.25rem 3rem;
}
.top-bar {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  margin-bottom: 1rem;
}
.back-btn {
  background: transparent;
  border: 1px solid var(--border);
  color: var(--text);
  padding: 0.35rem 0.75rem;
  border-radius: 6px;
  cursor: pointer;
}
.title {
  color: var(--gold);
  font-weight: 700;
}
.empty {
  color: var(--text-dim);
  text-align: center;
  margin-top: 3rem;
}
.list {
  list-style: none;
  padding: 0;
  margin: 0;
}
.row {
  display: flex;
  align-items: center;
  gap: 0.85rem;
  padding: 0.65rem 0.85rem;
  border-radius: 8px;
  cursor: pointer;
}
.row:hover {
  background: var(--bg-soft);
}
.avatar {
  width: 44px;
  height: 44px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #fff;
  font-weight: 700;
  font-size: 0.85rem;
  border: 2px solid var(--gold);
}
.name {
  color: #fff;
  font-weight: 600;
}
.handle {
  color: var(--text-dim);
  font-size: 0.8rem;
}
</style>