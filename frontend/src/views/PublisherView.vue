<script setup lang="ts">
import { computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useVideosStore } from '@/stores/videos'
import { useI18nStore } from '@/stores/i18n'
import VideoFeed from '@/components/video/VideoFeed.vue'

const route = useRoute()
const router = useRouter()
const store = useVideosStore()
const i18n = useI18nStore()

const authorId = computed(() => String(route.params.id || ''))
const authorVideos = computed(() => store.getByAuthor(authorId.value))
const isFollowing = computed(() => store.isFollowing(authorId.value))
const authorHue = computed(() => {
  const len = authorId.value.length
  return (len * 47) % 360
})

function toggleFollow() {
  if (isFollowing.value) store.unfollow(authorId.value)
  else store.follow(authorId.value)
}

function goBack() {
  router.back()
}
</script>

<template>
  <div class="publisher-page">
    <div class="top-bar">
      <button class="back-btn" @click="goBack">←</button>
      <span class="title">{{ i18n.t('publisher_profile') }}</span>
    </div>

    <div class="profile">
      <div
        class="avatar"
        :style="{ background: `hsl(${authorHue},60%,45%)` }"
      >
        {{ authorId.slice(-2) }}
      </div>
      <div class="info">
        <div class="id">@{{ authorId }}</div>
        <div class="stats">
          {{ authorVideos.length }} {{ i18n.t('videos') }}
        </div>
      </div>
      <button
        class="follow-btn"
        :class="{ following: isFollowing }"
        @click="toggleFollow"
      >
        {{ isFollowing ? i18n.t('unfollow') : i18n.t('follow') }}
      </button>
    </div>

    <div class="feed-wrap">
      <VideoFeed :videos="authorVideos" :show-upload-meta="true" />
    </div>
  </div>
</template>

<style scoped>
.publisher-page {
  position: fixed;
  inset: 0;
  display: flex;
  flex-direction: column;
  background: #000;
  z-index: 1000;
}
.top-bar {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  padding: 0.6rem 1rem;
  background: #0d0d0d;
  border-bottom: 1px solid #222;
}
.back-btn {
  background: transparent;
  border: 1px solid #333;
  color: #fff;
  padding: 0.35rem 0.75rem;
  border-radius: 6px;
  cursor: pointer;
}
.title {
  color: var(--gold);
  font-weight: 700;
}
.profile {
  display: flex;
  align-items: center;
  gap: 1rem;
  padding: 1rem 1.25rem;
  background: #111;
  border-bottom: 1px solid #222;
}
.avatar {
  width: 56px;
  height: 56px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #fff;
  font-weight: 700;
  border: 2px solid var(--gold);
}
.info {
  flex: 1;
}
.id {
  color: #fff;
  font-weight: 700;
}
.stats {
  color: var(--text-dim);
  font-size: 0.85rem;
  margin-top: 0.2rem;
}
.follow-btn {
  padding: 0.45rem 1rem;
  border-radius: 6px;
  border: 1px solid var(--gold);
  background: var(--gold);
  color: #111;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.15s;
}
.follow-btn.following {
  background: transparent;
  color: var(--gold);
}
.feed-wrap {
  flex: 1;
  min-height: 0;
  display: flex;
}
</style>