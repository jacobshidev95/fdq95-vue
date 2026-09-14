<script setup lang="ts">
import { useI18nStore } from '@/stores/i18n'
const i18n = useI18nStore()

const appStoreUrl = 'https://apps.apple.com/app/fdq95'
const googlePlayUrl = 'https://play.google.com/store/apps/details?id=com.fdq95'
const fdroidUrl = 'https://f-droid.org/packages/com.fdq95'
</script>

<template>
  <footer class="footer">
    <div class="items">
      <p class="desc">{{ i18n.t('footer_text') }}</p>

      <a class="app-link" :href="appStoreUrl" target="_blank" rel="noopener">
        <span class="icon" aria-hidden="true">🍎</span>
        {{ i18n.t('app_store') }}
      </a>

      <a class="app-link" :href="googlePlayUrl" target="_blank" rel="noopener">
        <span class="icon" aria-hidden="true">▶</span>
        {{ i18n.t('google_play') }}
      </a>

      <a class="app-link" :href="fdroidUrl" target="_blank" rel="noopener">
        <span class="icon" aria-hidden="true">🤖</span>
        {{ i18n.t('fdroid') }}
      </a>
    </div>
  </footer>
</template>

<style scoped>
.footer {
  background: var(--bg-header);
  border-top: 1px solid var(--border);
  padding: 1rem 1.25rem;
  color: var(--text-dim);
}
.items {
  display: flex;
  flex-direction: row;
  flex-wrap: wrap;
  align-items: center;
  justify-content: center;
  gap: 1.5rem;
}
.desc {
  margin: 0;
  text-align: center;
  font-size: 0.85rem;
  line-height: 1.35;
  white-space: pre-line;
}
.app-link {
  display: inline-flex;
  align-items: center;
  gap: 0.4rem;
  color: var(--gold);
  font-size: 0.85rem;
  white-space: nowrap;
}
.app-link:hover {
  color: var(--gold-hover);
}
.icon {
  font-size: 1.05rem;
}
</style>
