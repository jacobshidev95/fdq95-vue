<script setup lang="ts">
import { useRouter } from 'vue-router'
import VideoCard from './VideoCard.vue'
import type { VideoItem } from '@/data/videos'

defineProps<{
  videos: VideoItem[]
  showRank?: boolean
  showUploadMeta?: boolean
  showUploaderId?: boolean
}>()

const router = useRouter()

function openComments(id: number) {
  router.push(`/videos/comments/${id}`)
}
</script>

<template>
  <div class="feed">
    <VideoCard
      v-for="(v, i) in videos"
      :key="v.id"
      :video="v"
      :rank="i + 1"
      :show-rank="showRank"
      :show-upload-meta="showUploadMeta"
      :show-uploader-id="showUploaderId"
      @open-comments="openComments"
    />

    <div v-if="videos.length === 0" class="empty">
      <p>No videos to show.</p>
    </div>
  </div>
</template>

<style scoped>
.feed {
  flex: 1;
  overflow-y: scroll;
  scroll-snap-type: y mandatory;
  background: #000;
  min-height: 0;
}
.feed > * {
  height: 100%;
}
.empty {
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--text-dim);
  height: 100%;
}
</style>