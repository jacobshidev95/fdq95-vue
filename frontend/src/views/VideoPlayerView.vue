<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useVideosStore } from '@/stores/videos'
import { useI18nStore } from '@/stores/i18n'
import VideoFeed from '@/components/video/VideoFeed.vue'

const videosStore = useVideosStore()
const i18n = useI18nStore()
const route = useRoute()
const router = useRouter()

type Tab = 'best' | 'latest' | 'following' | 'recommended' | 'search' | 'settings'

const TABS: { key: Tab; labelKey: string }[] = [
  { key: 'best', labelKey: 'tab_best' },
  { key: 'latest', labelKey: 'tab_latest' },
  { key: 'following', labelKey: 'tab_following' },
  { key: 'recommended', labelKey: 'tab_recommended' },
  { key: 'search', labelKey: 'tab_search' },
  { key: 'settings', labelKey: 'tab_settings' },
]

const active = ref<Tab>('best')

const searchKeyword = ref('')
const searchResults = ref<typeof videosStore.videos>([])

onMounted(() => {
  const q = route.query.video
  if (q) {
    // Future: jump to specific video
  }
})

const currentVideos = computed(() => {
  switch (active.value) {
    case 'best':
      return videosStore.topVideos
    case 'latest':
      return videosStore.latestVideos
    case 'following':
      return videosStore.followingVideos
    case 'recommended':
      return videosStore.recommendedVideos
    default:
      return []
  }
})

function doSearch() {
  searchResults.value = videosStore.searchByKeyword(searchKeyword.value)
}

function goBack() {
  router.push('/')
}
</script>

<template>
  <div class="player">
    <!-- Top tab bar -->
    <div class="top-bar">
      <button class="back-btn" @click="goBack">←</button>
      <button
        v-for="t in TABS"
        :key="t.key"
        class="tab-btn"
        :class="{ active: active === t.key }"
        @click="active = t.key"
      >
        {{ i18n.t(t.labelKey) }}
      </button>
    </div>

    <!-- Best -->
    <VideoFeed
      v-if="active === 'best'"
      :videos="currentVideos"
      :show-rank="true"
    />

    <!-- Latest -->
    <VideoFeed
      v-else-if="active === 'latest'"
      :videos="currentVideos"
      :show-upload-meta="true"
      :show-uploader-id="true"
    />

    <!-- Following -->
    <VideoFeed
      v-else-if="active === 'following'"
      :videos="currentVideos"
      :show-upload-meta="true"
      :show-uploader-id="true"
    />

    <!-- Recommended -->
    <VideoFeed v-else-if="active === 'recommended'" :videos="currentVideos" />

    <!-- Search -->
    <div v-else-if="active === 'search'" class="search-panel">
      <div class="search-row">
        <input
          v-model="searchKeyword"
          type="text"
          :placeholder="i18n.t('search_placeholder')"
          @keyup.enter="doSearch"
        />
        <button class="btn btn-primary" @click="doSearch">
          {{ i18n.t('search') }}
        </button>
      </div>

      <VideoFeed v-if="searchResults.length" :videos="searchResults" />
      <p v-else-if="searchKeyword" class="hint">
        {{ i18n.t('no_results') }}
      </p>
    </div>

    <!-- Settings -->
    <div v-else-if="active === 'settings'" class="settings-panel">
      <h2 class="settings-title">{{ i18n.t('tab_settings') }}</h2>

      <label>{{ i18n.t('display_name') }}</label>
      <input v-model="videosStore.settings.displayName" type="text" />

      <label>{{ i18n.t('user_id_label') }}</label>
      <input v-model="videosStore.settings.userId" type="text" />

      <label>{{ i18n.t('bio') }}</label>
      <textarea v-model="videosStore.settings.bio" rows="3" />

      <label>{{ i18n.t('email') }}</label>
      <input v-model="videosStore.settings.email" type="email" />

      <label>{{ i18n.t('country') }}</label>
      <input v-model="videosStore.settings.country" type="text" />

      <label>{{ i18n.t('language') }}</label>
      <input v-model="videosStore.settings.language" type="text" />

      <label class="checkbox-row">
        <input v-model="videosStore.settings.notifications" type="checkbox" />
        <span>{{ i18n.t('notifications') }}</span>
      </label>

      <label class="checkbox-row">
        <input v-model="videosStore.settings.privateAccount" type="checkbox" />
        <span>{{ i18n.t('private_account') }}</span>
      </label>

      <button class="btn btn-primary btn-block save-btn">
        {{ i18n.t('save') }}
      </button>
    </div>
  </div>
</template>

<style scoped>
.player {
  position: fixed;
  inset: 0;
  display: flex;
  flex-direction: column;
  background: #000;
  z-index: 1000;
}

/* ---------- Top bar ---------- */
.top-bar {
  display: flex;
  align-items: stretch;
  gap: 0.35rem;
  padding: 0.5rem 0.75rem;
  background: #0d0d0d;
  border-bottom: 1px solid #222;
  flex-shrink: 0;
}
.back-btn {
  background: transparent;
  border: 1px solid #333;
  color: #fff;
  padding: 0.4rem 0.75rem;
  border-radius: 6px;
  cursor: pointer;
  font-size: 1rem;
}
.back-btn:hover {
  border-color: var(--gold);
  color: var(--gold);
}
.tab-btn {
  flex: 1 1 0;
  min-width: 0;
  padding: 0.45rem 0.5rem;
  background: transparent;
  color: #aaa;
  border: 1px solid #333;
  border-radius: 6px;
  cursor: pointer;
  font-size: 0.85rem;
  transition: all 0.15s;
}
.tab-btn:hover {
  color: var(--gold);
  border-color: var(--gold);
}
.tab-btn.active {
  background: var(--gold);
  color: #111;
  border-color: var(--gold);
  font-weight: 700;
}

/* ---------- Search ---------- */
.search-panel {
  flex: 1;
  display: flex;
  flex-direction: column;
  min-height: 0;
}
.search-row {
  display: flex;
  gap: 0.5rem;
  padding: 0.75rem 1rem;
  background: #0d0d0d;
  border-bottom: 1px solid #222;
}
.search-row input {
  flex: 1;
  margin: 0;
}
.hint {
  color: var(--text-dim);
  text-align: center;
  margin-top: 2rem;
}

/* ---------- Settings ---------- */
.settings-panel {
  flex: 1;
  overflow-y: auto;
  padding: 1.5rem 1.5rem 3rem;
  max-width: 560px;
  width: 100%;
  margin: 0 auto;
}
.settings-title {
  color: var(--gold);
  margin: 0 0 1rem;
  text-align: center;
}
.checkbox-row {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  margin-top: 0.75rem;
  color: var(--text);
  cursor: pointer;
}
.checkbox-row input {
  width: auto;
  margin: 0;
  accent-color: var(--gold);
}
.save-btn {
  margin-top: 1.5rem;
}

@media (max-width: 720px) {
  .tab-btn {
    font-size: 0.75rem;
    padding: 0.4rem 0.25rem;
  }
}
</style>