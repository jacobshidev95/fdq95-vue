<script setup lang="ts">
import { computed, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useVideosStore } from '@/stores/videos'
import { useI18nStore } from '@/stores/i18n'
import { timeAgo } from '@/data/videos'

const route = useRoute()
const router = useRouter()
const store = useVideosStore()
const i18n = useI18nStore()

const videoId = computed(() => Number(route.params.id))
const video = computed(() => store.getById(videoId.value))
const comments = computed(() => store.commentsFor(videoId.value))

const newComment = ref('')

function post() {
  const text = newComment.value.trim()
  if (!text) return
  store.addComment(videoId.value, text, store.settings.userId)
  newComment.value = ''
}

function goBack() {
  router.back()
}
</script>

<template>
  <div class="comments-page">
    <div class="top-bar">
      <button class="back-btn" @click="goBack">←</button>
      <span class="title">
        {{ i18n.t('comments') }}
        <span v-if="video" class="sub">— {{ video.title }}</span>
      </span>
    </div>

    <div class="list">
      <div v-if="comments.length === 0" class="empty">
        {{ i18n.t('no_comments') }}
      </div>
      <div v-for="c in comments" :key="c.id" class="comment">
        <div
          class="avatar"
          :style="{ background: `hsl(${c.authorHue},60%,45%)` }"
        >
          {{ c.authorId.slice(-2) }}
        </div>
        <div class="body">
          <div class="meta">
            <span class="author">@{{ c.authorId }}</span>
            <span class="time">{{ timeAgo(c.createdAt) }}</span>
          </div>
          <p class="text">{{ c.text }}</p>
        </div>
      </div>
    </div>

    <div class="composer">
      <input
        v-model="newComment"
        :placeholder="i18n.t('comment_placeholder')"
        @keyup.enter="post"
      />
      <button class="btn btn-primary" @click="post">
        {{ i18n.t('post_comment') }}
      </button>
    </div>
  </div>
</template>

<style scoped>
.comments-page {
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
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.sub {
  color: var(--text-dim);
  font-weight: 400;
  font-size: 0.85rem;
}
.list {
  flex: 1;
  overflow-y: auto;
  padding: 0.75rem 1rem;
}
.empty {
  color: var(--text-dim);
  text-align: center;
  margin-top: 2rem;
}
.comment {
  display: flex;
  gap: 0.75rem;
  padding: 0.75rem 0;
  border-bottom: 1px solid #222;
}
.avatar {
  flex: 0 0 36px;
  height: 36px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #fff;
  font-weight: 700;
  font-size: 0.75rem;
}
.body {
  flex: 1;
  min-width: 0;
}
.meta {
  display: flex;
  gap: 0.6rem;
  align-items: baseline;
  margin-bottom: 0.2rem;
}
.author {
  color: var(--gold);
  font-weight: 600;
  font-size: 0.85rem;
}
.time {
  color: var(--text-dim);
  font-size: 0.75rem;
}
.text {
  margin: 0;
  color: #e0e0e0;
  font-size: 0.9rem;
  line-height: 1.5;
  word-break: break-word;
}
.composer {
  display: flex;
  gap: 0.5rem;
  padding: 0.75rem 1rem;
  background: #0d0d0d;
  border-top: 1px solid #222;
}
.composer input {
  flex: 1;
  margin: 0;
}
</style>