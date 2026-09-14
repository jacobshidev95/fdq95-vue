<script setup lang="ts">
import { onMounted } from 'vue'
import AppHeader from '@/components/AppHeader.vue'
import AppFooter from '@/components/AppFooter.vue'
import { useI18nStore } from '@/stores/i18n'
import { useAuthStore } from '@/stores/auth'

const i18n = useI18nStore()
const auth = useAuthStore()

onMounted(async () => {
  await i18n.init()
  if (auth.token && !auth.user) {
    await auth.fetchMe()
  }
})
</script>

<template>
  <AppHeader />
  <main class="app-main">
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
  justify-content: flex-start;
  padding: 3rem 1rem;
}
</style>
