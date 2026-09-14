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
  max-width: 860px;
}
.hero-title {
  font-size: 2.25rem;
  margin: 0 0 1rem;
  line-height: 1.25;
  letter-spacing: 0.05em;
}
.hero-desc {
  font-size: 1.1rem;
  line-height: 1.7;
  color: var(--text-dim);
  margin-bottom: 2rem;
}
@media (max-width: 640px) {
  .hero-title {
    font-size: 1.6rem;
  }
}
</style>