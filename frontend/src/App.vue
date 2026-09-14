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

// Home page uses a full-bleed 3-column layout (no padding).
const isHome = computed(() => route.path === '/')

onMounted(async () => {
  await i18n.init()
  if (auth.token && !auth.user) {
    await auth.fetchMe()
  }
})
</script>

<template>
  <AppHeader />
  <main class="app-main" :class="{ 'app-main--full': isHome }">
    <router-view />
  </main>
  <AppFooter />
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

/* Full-bleed variant used by the home page */
.app-main--full {
  align-items: stretch;
  padding: 0;
  overflow: hidden;
}

@media (max-width: 900px) {
  .app-main--full {
    overflow: visible;
  }
}
</style>