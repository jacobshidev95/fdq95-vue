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

      <div class="app-links">
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

/*
 * Outer flex row: description + app-links group.
 * gap: 5px  =>  EXACTLY 5 pixels between the description and the group
 *               (and also 5px if the group wraps below on narrow screens).
 */
.items {
  display: flex;
  flex-direction: row;
  flex-wrap: wrap;
  align-items: center;
  justify-content: center;
  gap: 5px;
}

/* Inner group of the three store links */
.app-links {
  display: flex;
  flex-direction: row;
  flex-wrap: wrap;
  align-items: center;
  justify-content: center;
  gap: 20px;
}

/*
 * Two lines; first line justified; second line left-aligned with
 * single spaces between words.
 */
.desc {
  margin: 0;
  max-width: 430px;
  text-align: justify;
  text-align-last: left;
  word-spacing: normal;
  letter-spacing: normal;
  white-space: pre-line;
  font-size: 0.85rem;
  line-height: 1.5;
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

@media (max-width: 640px) {
  .desc {
    max-width: 100%;
    text-align: center;
    text-align-last: center;
  }
  .app-links {
    gap: 12px;
  }
}
</style>