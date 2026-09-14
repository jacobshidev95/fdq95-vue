<script setup lang="ts">
import { useI18nStore } from '@/stores/i18n'

const i18n = useI18nStore()
</script>

<template>
  <section class="home">
    <h1 class="title-gold hero-title">{{ i18n.t('welcome_title') }}</h1>
    <p class="hero-desc">{{ i18n.t('welcome_desc') }}</p>
  </section>
</template>

<style scoped>
.home {
  text-align: center;
  max-width: 720px;
}
.hero-title {
  font-size: 3rem;
  margin: 0 0 1rem;
}
.hero-desc {
  font-size: 1.1rem;
  line-height: 1.7;
  color: var(--text-dim);
  margin-bottom: 2rem;
}
</style>