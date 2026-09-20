<script setup lang="ts">
import { computed, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import AppHeader from '@/components/AppHeader.vue'
import AppFooter from '@/components/AppFooter.vue'
import { useI18nStore } from '@/stores/i18n'
import { useAuthStore } from '@/stores/auth'

const i18n = useI18nStore()
const auth = useAuthStore()
const route = useRoute()

// Home uses full-bleed 3-column layout
const isHome = computed(() => route.path === '/')

// ★ 沉浸式全屏页面：/videos、/articles、发布视频、发布文章
const isVideoFullscreen = computed(() => {
  const p = route.path
  return (
    p.startsWith('/videos') ||
    p.startsWith('/articles') ||
    p.startsWith('/record-video') ||                 // ★ 新增
    p.startsWith('/ai-video-studio') ||      // ★ 新增
    p.startsWith('/settings/publish-video') ||
    p.startsWith('/settings/publish-article')
  )
})

onMounted(async () => {
  await i18n.init()
  if (auth.token && !auth.user) {
    await auth.fetchMe()
  }
})
</script>

<template>
  <template v-if="!isVideoFullscreen">
    <AppHeader />
  </template>

  <main
    class="app-main"
    :class="{ 'app-main--full': isHome, 'app-main--bare': isVideoFullscreen }"
  >
    <router-view />
  </main>

  <template v-if="!isVideoFullscreen">
    <AppFooter />
  </template>
</template>

<style scoped>
.app-main {
  flex: 1;
  width: 100%;
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 3rem 1rem;
  min-height: 0;
}
.app-main--full {
  align-items: stretch;
  padding: 0;
  overflow: hidden;
}
.app-main--bare {
  padding: 0;
  align-items: stretch;
  overflow: hidden;
}

@media (max-width: 900px) {
  .app-main--full {
    overflow: visible;
  }
}

/* ★ 移动端主容器 padding 收窄 */
@media (max-width: 480px) {
  .app-main {
    padding: 1rem 0.5rem;
  }
}
</style>