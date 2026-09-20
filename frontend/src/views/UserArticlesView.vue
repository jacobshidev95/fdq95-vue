<script setup lang="ts">
import { useRoute, useRouter } from 'vue-router'
import { useI18nStore } from '@/stores/i18n'

const route = useRoute()
const router = useRouter()
const i18n = useI18nStore()

const userId = (route.params.userId as string) || ''

function goBack() {
  router.back()
}
</script>

<template>
  <div class="articles-page">
    <header class="top-bar">
      <button class="back-btn" @click="goBack">‹</button>
      <h1 class="page-title">
        {{ i18n.t('article_list') === 'article_list' ? '文章列表' : i18n.t('article_list') }}
      </h1>
      <span class="spacer" />
    </header>
    <div class="state">
      <p>@{{ userId }} 的文章列表开发中…</p>
    </div>
  </div>
</template>

<style scoped>
.articles-page {
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
}
.spacer { width: 36px; }
.state {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  color: rgba(255, 255, 255, 0.5);
  font-size: 1rem;
}
</style>