<script setup lang="ts">
import { useI18nStore } from '@/stores/i18n'
const i18n = useI18nStore()

const appStoreUrl = 'https://apps.apple.com/app/fdq95'
const googlePlayUrl =
  'https://play.google.com/store/apps/details?id=com.fdq95'
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

/* Row layout — no gap between items; spacing handled per-element
   so we can set an exact 5px between the description and the first
   App Store link. */
.items {
  display: flex;
  flex-direction: row;
  flex-wrap: wrap;
  align-items: center;
  justify-content: center;
  gap: 0.5rem 0; /* row-gap only; column spacing via margins */
}

/* Two lines, first line justified, second line left-aligned with
   single spaces between words. */
.desc {
  margin: 0 5px 0 0; /* exactly 5px to the right (before App Store) */
  width: 100%;
  max-width: 430px;
  text-align: justify;
  text-align-last: left;
  word-spacing: normal;
  letter-spacing: normal;
  white-space: pre-line;
  font-size: 0.85rem;
  line-height: 1.5;
}

/* App Store / Google Play / F-Droid links */
.app-link {
  display: inline-flex;
  align-items: center;
  gap: 0.4rem;
  margin-left: 20px; /* default spacing between app links */
  color: var(--gold);
  font-size: 0.85rem;
  white-space: nowrap;
}
/* The first .app-link (right after the description) gets zero extra
   margin, so the only spacing to the description is the 5px above. */
.app-link:first-of-type {
  margin-left: 0;
}
.app-link:hover {
  color: var(--gold-hover);
}
.icon {
  font-size: 1.05rem;
}

@media (max-width: 640px) {
  .desc {
    max-width: 100%;
    margin-right: 0;
  }
  .app-link {
    margin-left: 12px;
  }
  .app-link:first-of-type {
    margin-left: 12px;
  }
}
</style>