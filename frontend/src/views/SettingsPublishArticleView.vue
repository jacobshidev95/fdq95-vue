<script setup lang="ts">
import { computed, reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import { api } from '@/api/client'
import { useI18nStore } from '@/stores/i18n'

const router = useRouter()
const i18n = useI18nStore()

type Category =
  | 'medical' | 'health' | 'education' | 'entertainment' | 'travel'
  | 'food' | 'clothing' | 'industry' | 'tech' | 'iot' | 'life' | 'ai'

const CATEGORIES: { value: Category; key: string }[] = [
  { value: 'medical', key: 'Medical' },
  { value: 'health', key: 'Health' },
  { value: 'education', key: 'Education' },
  { value: 'entertainment', key: 'Entertainment' },
  { value: 'travel', key: 'Travel' },
  { value: 'food', key: 'Food' },
  { value: 'clothing', key: 'Clothing' },
  { value: 'industry', key: 'Industry' },
  { value: 'tech', key: 'Technology' },
  { value: 'iot', key: 'IoT' },
  { value: 'life', key: 'Life' },
  { value: 'ai', key: 'AI' },
]

const title = ref('')
const category = ref<Category | null>(null)
const contentType = ref<'file' | 'rich' | 'link'>('rich')

const fileUrl = ref('')
const fileName = ref('')
const fileSize = ref(0)
const uploadingFile = ref(false)
const fileError = ref('')

interface Block {
  type: 'text' | 'image' | 'video'
  content: string
  uploading: boolean
}
// ★ 数组里每个元素都是 reactive
const richBlocks = ref<Block[]>([reactive<Block>({ type: 'text', content: '', uploading: false })])

const linkUrl = ref('')

const submitting = ref(false)
const submitError = ref('')
const submitSuccess = ref('')

const MAX_DOC_MB = 10
const MAX_IMAGE_MB = 5
const MAX_VIDEO_MB = 50

const canSubmit = computed(() => {
  if (!title.value.trim()) return false
  if (!category.value) return false
  if (contentType.value === 'file') return !!fileUrl.value
  if (contentType.value === 'link') return !!linkUrl.value.trim()
  if (contentType.value === 'rich') {
    return richBlocks.value.some(
      (b) => !b.uploading && (b.content || '').trim(),
    )
  }
  return false
})

async function upload(kind: 'document' | 'image' | 'video', f: File) {
  const formData = new FormData()
  formData.append('kind', kind)
  formData.append('file', f)
  const { data } = await api.post('/api/articles/upload', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  })
  return data as { url: string; name: string; size: number }
}

function pickDocument() {
  const input = document.createElement('input')
  input.type = 'file'
  input.accept = '.pdf,.doc,.docx,.txt'
  input.onchange = async () => {
    const f = input.files?.[0]
    if (!f) return
    fileError.value = ''
    if (f.size > MAX_DOC_MB * 1024 * 1024) {
      fileError.value = i18n.t('publish_article_file_too_large')
      return
    }
    uploadingFile.value = true
    try {
      const res = await upload('document', f)
      fileUrl.value = res.url
      fileName.value = res.name
      fileSize.value = res.size
    } catch (e: any) {
      fileError.value = e?.response?.data?.detail || i18n.t('publish_article_upload_failed')
    } finally {
      uploadingFile.value = false
    }
  }
  input.click()
}

function clearFile() {
  fileUrl.value = ''
  fileName.value = ''
  fileSize.value = 0
  fileError.value = ''
}

function addTextBlock() {
  richBlocks.value.push(
    reactive<Block>({ type: 'text', content: '', uploading: false }),
  )
}

function addImageBlock() {
  pickMedia('image', '.jpg,.jpeg,.png,.gif,.webp', MAX_IMAGE_MB)
}
function addVideoBlock() {
  pickMedia('video', '.mp4,.webm,.mov', MAX_VIDEO_MB)
}

function pickMedia(
  type: 'image' | 'video',
  accept: string,
  maxMB: number,
) {
  const input = document.createElement('input')
  input.type = 'file'
  input.accept = accept
  input.onchange = async () => {
    const f = input.files?.[0]
    if (!f) return
    if (f.size > maxMB * 1024 * 1024) {
      alert(i18n.t('publish_article_file_too_large'))
      return
    }

    // ★ 关键：用 reactive 包装，让 Vue 能追踪 uploading / content 变化
    const block = reactive<Block>({ type, content: '', uploading: true })
    richBlocks.value.push(block)

    try {
      const res = await upload(type, f)
      block.content = res.url
      block.uploading = false
    } catch (e: any) {
      alert(e?.response?.data?.detail || i18n.t('publish_article_upload_failed'))
      const idx = richBlocks.value.indexOf(block)
      if (idx >= 0) richBlocks.value.splice(idx, 1)
    }
  }
  input.click()
}

function removeBlock(i: number) {
  richBlocks.value.splice(i, 1)
}

async function submit() {
  submitError.value = ''
  submitSuccess.value = ''
  if (!canSubmit.value) {
    submitError.value = i18n.t('publish_article_required')
    return
  }
  submitting.value = true
  try {
    const payload: Record<string, unknown> = {
      title: title.value.trim(),
      category: category.value,
      content_type: contentType.value,
    }
    if (contentType.value === 'file') {
      payload.file_url = fileUrl.value
      payload.file_name = fileName.value
      payload.file_size = fileSize.value
    } else if (contentType.value === 'link') {
      payload.link_url = linkUrl.value.trim()
    } else {
      payload.rich_blocks = richBlocks.value
        .filter((b) => !b.uploading && (b.content || '').trim())
        .map((b) => ({ type: b.type, content: b.content }))
    }
    await api.post('/api/articles', payload)
    submitSuccess.value = i18n.t('publish_article_success')
    setTimeout(() => router.push('/articles'), 1500)
  } catch (e: any) {
    submitError.value =
      e?.response?.data?.detail || i18n.t('publish_article_failed')
  } finally {
    submitting.value = false
  }
}

function goBack() {
  router.back()
}
</script>

<template>
  <div class="publish-page">
    <header class="top-bar">
      <button class="back-btn" @click="goBack">‹</button>
      <h1 class="page-title">{{ i18n.t('settings_publish_article') }}</h1>
      <span class="spacer" />
    </header>

    <div class="scroll-body">
      <div v-if="submitError" class="notice notice-error">{{ submitError }}</div>
      <div v-if="submitSuccess" class="notice notice-ok">{{ submitSuccess }}</div>

      <section class="card">
        <label class="field-label">{{ i18n.t('publish_article_title') }}</label>
        <input
          v-model="title"
          type="text"
          class="title-input"
          :placeholder="i18n.t('publish_article_title_ph')"
          maxlength="200"
        />
      </section>

      <section class="card">
        <label class="field-label">{{ i18n.t('publish_article_category') }}</label>
        <div class="radio-grid">
          <label v-for="cat in CATEGORIES" :key="cat.value" class="radio-item">
            <input
              type="radio"
              name="category"
              :value="cat.value"
              v-model="category"
            />
            <span>{{ cat.key }}</span>
          </label>
        </div>
      </section>

      <section class="card">
        <label class="field-label">{{ i18n.t('publish_article_content_type') }}</label>
        <div class="type-tabs">
          <button
            class="type-tab"
            :class="{ active: contentType === 'file' }"
            @click="contentType = 'file'"
          >
            📎 {{ i18n.t('publish_article_type_file') }}
          </button>
          <button
            class="type-tab"
            :class="{ active: contentType === 'rich' }"
            @click="contentType = 'rich'"
          >
            ✏️ {{ i18n.t('publish_article_type_rich') }}
          </button>
          <button
            class="type-tab"
            :class="{ active: contentType === 'link' }"
            @click="contentType = 'link'"
          >
            🔗 {{ i18n.t('publish_article_type_link') }}
          </button>
        </div>

        <div v-if="contentType === 'file'" class="type-body">
          <button class="upload-btn" :disabled="uploadingFile" @click="pickDocument">
            {{ uploadingFile ? i18n.t('publish_article_uploading') : i18n.t('publish_article_choose_file') }}
          </button>
          <p class="hint">
            {{ i18n.t('publish_article_file_hint').replace('{n}', String(MAX_DOC_MB)) }}
          </p>
          <div v-if="fileError" class="notice notice-error">{{ fileError }}</div>
          <div v-if="fileUrl" class="file-chip">
            <span class="file-name">📄 {{ fileName }}</span>
            <span class="file-size">
              ({{ (fileSize / 1024 / 1024).toFixed(2) }} MB)
            </span>
            <button class="chip-remove" @click="clearFile">✕</button>
          </div>
        </div>

        <div v-else-if="contentType === 'rich'" class="type-body">
          <div class="block-list">
            <div
              v-for="(b, i) in richBlocks"
              :key="i"
              class="block-item"
              :class="`block-${b.type}`"
            >
              <div class="block-head">
                <span class="block-label">
                  {{
                    b.type === 'text'
                      ? i18n.t('publish_article_block_text')
                      : b.type === 'image'
                      ? i18n.t('publish_article_block_image')
                      : i18n.t('publish_article_block_video')
                  }}
                </span>
                <button class="block-remove" @click="removeBlock(i)">✕</button>
              </div>

              <textarea
                v-if="b.type === 'text'"
                v-model="b.content"
                rows="3"
                :placeholder="i18n.t('publish_article_text_ph')"
              />

              <div v-else-if="b.uploading" class="uploading-hint">
                {{ i18n.t('publish_article_uploading') }}
              </div>

              <div v-else-if="b.type === 'image'" class="media-preview">
                <img :src="b.content" alt="image" />
              </div>

              <div v-else-if="b.type === 'video'" class="media-preview">
                <video :src="b.content" controls playsinline />
              </div>
            </div>
          </div>

          <div class="add-block-row">
            <button class="add-btn" @click="addTextBlock">
              + {{ i18n.t('publish_article_block_text') }}
            </button>
            <button class="add-btn" @click="addImageBlock">
              + {{ i18n.t('publish_article_block_image') }}
            </button>
            <button class="add-btn" @click="addVideoBlock">
              + {{ i18n.t('publish_article_block_video') }}
            </button>
          </div>
          <p class="hint">
            {{
              i18n.t('publish_article_media_hint')
                .replace('{img}', String(MAX_IMAGE_MB))
                .replace('{vid}', String(MAX_VIDEO_MB))
            }}
          </p>
        </div>

        <div v-else-if="contentType === 'link'" class="type-body">
          <label class="field-label">{{ i18n.t('publish_article_link_url') }}</label>
          <input v-model="linkUrl" type="url" placeholder="https://..." />
        </div>
      </section>

      <button
        class="submit-btn"
        :disabled="!canSubmit || submitting"
        @click="submit"
      >
        {{ submitting ? i18n.t('publish_article_uploading') : i18n.t('publish_article_submit') }}
      </button>
    </div>
  </div>
</template>

<style scoped>
.publish-page {
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
  position: sticky;
  top: 0;
  z-index: 10;
  flex-shrink: 0;
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

.scroll-body {
  flex: 1 1 auto;
  padding: 0 0.75rem 2rem;
  overflow-y: auto;
}

.card {
  background: #1a1a1a;
  border-radius: 12px;
  padding: 1rem;
  margin-bottom: 1rem;
}

.field-label {
  display: block;
  color: rgba(255, 255, 255, 0.6);
  font-size: 0.85rem;
  margin-bottom: 0.5rem;
}

.title-input {
  width: 100%;
  background: #0d0d0d;
  border: 1px solid rgba(255, 255, 255, 0.12);
  border-radius: 8px;
  color: #fff;
  padding: 0.75rem 1rem;
  font-size: 1.15rem;
  font-weight: 600;
  text-align: center;
  box-sizing: border-box;
}
.title-input:focus { outline: none; border-color: #e5b80b; }

.radio-grid {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 0.5rem 0.75rem;
}
.radio-item {
  display: inline-flex;
  align-items: center;
  gap: 0.4rem;
  color: var(--text);
  cursor: pointer;
  user-select: none;
}
.radio-item input {
  width: auto;
  margin: 0;
  accent-color: #e5b80b;
}
.radio-item span {
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.type-tabs {
  display: flex;
  gap: 0.4rem;
  margin-bottom: 1rem;
  flex-wrap: wrap;
}
.type-tab {
  flex: 1 1 auto;
  background: rgba(255, 255, 255, 0.04);
  border: 1px solid rgba(255, 255, 255, 0.12);
  color: rgba(255, 255, 255, 0.75);
  border-radius: 8px;
  padding: 0.5rem 0.6rem;
  font-size: 0.85rem;
  cursor: pointer;
}
.type-tab.active {
  background: rgba(229, 184, 11, 0.12);
  border-color: #e5b80b;
  color: #e5b80b;
  font-weight: 600;
}

.type-body { margin-top: 0.5rem; }

.upload-btn {
  background: #e5b80b;
  color: #111;
  border: none;
  border-radius: 8px;
  padding: 0.6rem 1rem;
  font-weight: 600;
  cursor: pointer;
}
.upload-btn:disabled { opacity: 0.5; cursor: not-allowed; }

.hint {
  color: rgba(255, 255, 255, 0.45);
  font-size: 0.78rem;
  margin: 0.5rem 0 0;
}

.file-chip {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  background: rgba(229, 184, 11, 0.08);
  border: 1px solid rgba(229, 184, 11, 0.35);
  border-radius: 8px;
  padding: 0.5rem 0.75rem;
  margin-top: 0.75rem;
  font-size: 0.85rem;
}
.file-name { flex: 1; word-break: break-all; }
.file-size { color: rgba(255, 255, 255, 0.55); font-size: 0.78rem; }
.chip-remove {
  background: transparent;
  border: none;
  color: #ff8a80;
  font-size: 1.1rem;
  cursor: pointer;
}

.block-list {
  display: flex;
  flex-direction: column;
  gap: 0.6rem;
}
.block-item {
  background: #0d0d0d;
  border: 1px solid rgba(255, 255, 255, 0.08);
  border-radius: 8px;
  padding: 0.6rem;
}
.block-head {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 0.4rem;
}
.block-label {
  font-size: 0.72rem;
  color: rgba(255, 255, 255, 0.5);
  text-transform: uppercase;
  letter-spacing: 0.05em;
}
.block-remove {
  background: transparent;
  border: none;
  color: #ff8a80;
  font-size: 0.9rem;
  cursor: pointer;
  padding: 0.1rem 0.35rem;
  border-radius: 4px;
}
.block-remove:hover { background: rgba(231, 76, 60, 0.15); }

.block-item textarea {
  width: 100%;
  background: transparent;
  border: none;
  color: #fff;
  font-size: 0.95rem;
  font-family: inherit;
  resize: vertical;
  box-sizing: border-box;
}
.block-item textarea:focus { outline: none; }

.uploading-hint {
  color: rgba(255, 255, 255, 0.5);
  font-size: 0.85rem;
  padding: 0.5rem 0;
}

.media-preview img,
.media-preview video {
  max-width: 100%;
  border-radius: 6px;
  display: block;
}

.add-block-row {
  display: flex;
  gap: 0.4rem;
  margin-top: 0.75rem;
}
.add-btn {
  flex: 1;
  background: rgba(255, 255, 255, 0.06);
  border: 1px dashed rgba(255, 255, 255, 0.2);
  color: rgba(255, 255, 255, 0.85);
  border-radius: 8px;
  padding: 0.5rem;
  font-size: 0.85rem;
  cursor: pointer;
}
.add-btn:hover {
  border-color: #e5b80b;
  color: #e5b80b;
}

input[type="url"],
input[type="text"] {
  width: 100%;
  background: #0d0d0d;
  border: 1px solid rgba(255, 255, 255, 0.12);
  border-radius: 8px;
  color: #fff;
  padding: 0.6rem 0.75rem;
  font-size: 0.95rem;
  box-sizing: border-box;
}
input[type="url"]:focus,
input[type="text"]:focus {
  outline: none;
  border-color: #e5b80b;
}

.submit-btn {
  width: 100%;
  background: #e5b80b;
  color: #111;
  border: none;
  border-radius: 10px;
  padding: 0.85rem 1rem;
  font-size: 1rem;
  font-weight: 700;
  cursor: pointer;
  margin-top: 0.5rem;
}
.submit-btn:disabled {
  opacity: 0.4;
  cursor: not-allowed;
}

.notice {
  padding: 0.7rem 1rem;
  border-radius: 8px;
  margin-bottom: 0.75rem;
  font-size: 0.88rem;
}
.notice-error {
  background: rgba(231, 76, 60, 0.15);
  border: 1px solid #e74c3c;
  color: #ff8a80;
}
.notice-ok {
  background: rgba(46, 204, 113, 0.15);
  border: 1px solid #2ecc71;
  color: #a5f5c6;
}

@media (max-width: 720px) {
  .radio-grid { grid-template-columns: repeat(2, minmax(0, 1fr)); }
}
</style>