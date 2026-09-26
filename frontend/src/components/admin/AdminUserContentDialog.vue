<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import { api } from '@/api/client'
import { useI18nStore } from '@/stores/i18n'

const i18n = useI18nStore()

const props = defineProps<{
  visible: boolean
  userId: string        // UUID 字符串
  userLabel: string     // 显示用（@abc95med 或 email）
}>()

const emit = defineEmits<{
  'update:visible': [v: boolean]
  changed: []
}>()

interface ArticleItem {
  id: string
  title: string
  category: string | null
  content_type: string
  file_url: string | null
  link_url: string | null
  created_at: string | null
}

interface VideoItem {
  id: string
  title: string
  url: string
  thumbnail_url: string | null
  category: string | null
  duration_sec: number
  file_size: number
  views: number
  likes: number
  created_at: string | null
}

interface ContentResp {
  user: { id: string; user_id: string; email: string }
  articles: ArticleItem[]
  videos: VideoItem[]
  live_videos: VideoItem[]
  activity_videos: VideoItem[]
}

type TabKey = 'articles' | 'videos' | 'live' | 'activity'

const activeTab = ref<TabKey>('articles')
const loading = ref(false)
const loadError = ref('')
const data = ref<ContentResp | null>(null)

const TABS: { key: TabKey; label: string; icon: string }[] = [
  { key: 'articles', label: 'Text / Articles', icon: '📄' },
  { key: 'videos',   label: 'Videos',          icon: '🎬' },
  { key: 'live',     label: 'Live Videos',     icon: '📺' },
  { key: 'activity', label: 'Activity Videos', icon: '🎉' },
]

const currentList = computed(() => {
  if (!data.value) return []
  switch (activeTab.value) {
    case 'articles': return data.value.articles
    case 'videos':   return data.value.videos
    case 'live':     return data.value.live_videos
    case 'activity': return data.value.activity_videos
  }
})

async function load() {
  if (!props.userId) return
  loading.value = true
  loadError.value = ''
  try {
    const { data: resp } = await api.get(
      `/api/admin/users/${props.userId}/content`
    )
    data.value = resp
  } catch (e: any) {
    loadError.value = e?.response?.data?.detail || 'Load failed'
  } finally {
    loading.value = false
  }
}

watch(
  () => [props.visible, props.userId],
  ([v]) => { if (v) load() }
)

function close() {
  emit('update:visible', false)
}

function fmtSize(bytes: number): string {
  if (!bytes) return '—'
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`
  return `${(bytes / 1024 / 1024).toFixed(1)} MB`
}

function fmtDate(iso: string | null): string {
  if (!iso) return '—'
  try { return new Date(iso).toLocaleString() } catch { return iso }
}

// ★ 删除单条内容
async function deleteItem(kind: TabKey, id: string, title: string) {
  const what = kind === 'articles' ? 'article' : 'video'
  if (!confirm(`Delete this ${what}?\n\n"${title}"\n\nThis cannot be undone.`)) return
  try {
    if (kind === 'articles') {
      await api.delete(`/api/admin/articles/${id}`)
    } else {
      await api.delete(`/api/admin/videos/${id}`)
    }
    await load()
    emit('changed')
  } catch (e: any) {
    alert(e?.response?.data?.detail || 'Delete failed')
  }
}
</script>

<template>
  <div v-if="visible" class="modal-backdrop" @click.self="close">
    <div class="modal">
      <div class="modal-header">
        <h3>
          Content of <span class="user-label">{{ userLabel }}</span>
        </h3>
        <button @click="close">✕</button>
      </div>

      <!-- Tab 栏 -->
      <div class="tab-bar">
        <button
          v-for="t in TABS"
          :key="t.key"
          class="tab-btn"
          :class="{ active: activeTab === t.key }"
          @click="activeTab = t.key"
        >
          {{ t.icon }} {{ t.label }}
          <span class="tab-count">
            {{
              t.key === 'articles' ? (data?.articles.length ?? 0)
              : t.key === 'videos' ? (data?.videos.length ?? 0)
              : t.key === 'live' ? (data?.live_videos.length ?? 0)
              : (data?.activity_videos.length ?? 0)
            }}
          </span>
        </button>
      </div>

      <!-- 内容区 -->
      <div class="modal-body">
        <div v-if="loading" class="state">Loading…</div>
        <div v-else-if="loadError" class="state error">{{ loadError }}</div>
        <div v-else-if="currentList.length === 0" class="state">
          Nothing here yet.
        </div>

        <ul v-else class="item-list">
          <li v-for="item in currentList" :key="item.id" class="item-row">
            <div class="item-main">
              <div class="item-title">
                {{ (item as any).title || '(untitled)' }}
              </div>
              <div class="item-meta">
                <span v-if="(item as any).category" class="badge">
                  {{ (item as any).category }}
                </span>
                <span v-if="(item as any).duration_sec">
                  ⏱ {{ Math.round((item as any).duration_sec) }}s
                </span>
                <span v-if="(item as any).file_size">
                  💾 {{ fmtSize((item as any).file_size) }}
                </span>
                <span>{{ fmtDate((item as any).created_at) }}</span>
              </div>
            </div>
            <div class="item-actions">
              <a
                v-if="(item as any).url || (item as any).file_url"
                :href="(item as any).url || (item as any).file_url || '#'"
                target="_blank"
                rel="noopener"
                class="btn-link"
              >Open</a>
              <button
                class="btn-del"
                @click="deleteItem(activeTab, item.id, (item as any).title || '')"
              >Delete</button>
            </div>
          </li>
        </ul>
      </div>

      <div class="modal-footer">
        <button class="btn-close" @click="close">Close</button>
      </div>
    </div>
  </div>
</template>

<style scoped>
.modal-backdrop {
  position: fixed; inset: 0;
  background: rgba(0, 0, 0, 0.75);
  display: flex; align-items: center; justify-content: center;
  z-index: 3000;
  padding: 1rem;
}
.modal {
  width: 92%; max-width: 820px;
  max-height: 88vh;
  background: #111;
  border: 1px solid var(--border, #333);
  border-radius: 12px;
  color: #fff;
  display: flex; flex-direction: column;
  overflow: hidden;
}
.modal-header {
  display: flex; align-items: center; justify-content: space-between;
  padding: 0.9rem 1rem;
  border-bottom: 1px solid #222;
}
.modal-header h3 { margin: 0; font-size: 1rem; }
.user-label { color: var(--gold, #e5b80b); }
.modal-header button {
  background: transparent; border: none;
  color: #fff; font-size: 1.2rem; cursor: pointer;
}

.tab-bar {
  display: flex; gap: 0.3rem;
  padding: 0.5rem 1rem;
  border-bottom: 1px solid #222;
  flex-wrap: wrap;
}
.tab-btn {
  flex: 1 1 auto;
  padding: 0.45rem 0.6rem;
  background: rgba(32, 32, 32, 1);
  border: 1px solid var(--border, #333);
  border-radius: 6px;
  color: rgba(255, 255, 255, 0.7);
  font-size: 0.8rem;
  cursor: pointer;
  white-space: nowrap;
}
.tab-btn:hover { color: #fff; }
.tab-btn.active {
  background: rgba(229, 184, 11, 0.15);
  border-color: var(--gold, #e5b80b);
  color: var(--gold, #e5b80b);
  font-weight: 600;
}
.tab-count {
  display: inline-block;
  margin-left: 0.35rem;
  padding: 0 0.35rem;
  background: rgba(255, 255, 255, 0.12);
  border-radius: 8px;
  font-size: 0.7rem;
}

.modal-body {
  flex: 1 1 auto;
  min-height: 0;
  overflow-y: auto;
  padding: 0.75rem 1rem;
}
.state {
  padding: 2rem;
  text-align: center;
  color: rgba(255, 255, 255, 0.5);
}
.state.error { color: #ff8a80; }

.item-list { list-style: none; padding: 0; margin: 0; }
.item-row {
  display: flex; align-items: center; justify-content: space-between;
  gap: 0.75rem;
  padding: 0.6rem 0.5rem;
  border-bottom: 1px solid #222;
}
.item-row:last-child { border-bottom: none; }
.item-main { flex: 1; min-width: 0; }
.item-title {
  font-size: 0.9rem;
  color: #fff;
  white-space: nowrap; overflow: hidden; text-overflow: ellipsis;
}
.item-meta {
  display: flex; gap: 0.6rem; flex-wrap: wrap;
  margin-top: 0.2rem;
  font-size: 0.72rem;
  color: rgba(255, 255, 255, 0.5);
}
.badge {
  padding: 0 0.4rem;
  background: rgba(139, 92, 246, 0.2);
  color: #c4b5fd;
  border-radius: 4px;
}
.item-actions {
  display: flex; gap: 0.4rem; flex-shrink: 0;
}
.btn-link, .btn-del {
  padding: 0.3rem 0.7rem;
  border-radius: 6px;
  font-size: 0.75rem;
  cursor: pointer;
  text-decoration: none;
  border: 1px solid transparent;
  white-space: nowrap;
}
.btn-link {
  background: rgba(255, 255, 255, 0.08);
  color: #ddd;
  border-color: rgba(255, 255, 255, 0.15);
}
.btn-link:hover { color: #fff; }
.btn-del {
  background: rgba(231, 76, 60, 0.15);
  color: #ff8a80;
  border-color: rgba(231, 76, 60, 0.4);
}
.btn-del:hover { background: rgba(231, 76, 60, 0.3); }

.modal-footer {
  display: flex; justify-content: flex-end;
  padding: 0.75rem 1rem;
  border-top: 1px solid #222;
}
.btn-close {
  padding: 0.5rem 1.2rem;
  background: rgba(32, 32, 32, 1);
  color: #fff;
  border: 1px solid var(--border, #333);
  border-radius: 8px;
  font-size: 0.85rem;
  cursor: pointer;
}
.btn-close:hover { border-color: var(--gold, #e5b80b); color: var(--gold, #e5b80b); }
</style>