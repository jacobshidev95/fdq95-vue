<script setup lang="ts">
import { computed, onMounted, ref, nextTick } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { api } from '@/api/client'
import { useProfileStore } from '@/stores/profile'
import { useI18nStore } from '@/stores/i18n'

const route = useRoute()
const router = useRouter()
const store = useProfileStore()
const i18n = useI18nStore()

const targetId = computed(() => String(route.params.userId || ''))

interface Msg {
  id: string
  sender_string_id: string
  sender_display_name: string
  content: string
  content_type: string
  media_url: string | null
  created_at: string
}

const messages = ref<Msg[]>([])
const draft = ref('')
const sending = ref(false)
const errorBanner = ref('')
const listRef = ref<HTMLElement | null>(null)
const showEmoji = ref(false)

const EMOJIS = ['😀', '😂', '❤️', '👍', '🎉', '🔥', '😢', '🙏', '👏', '💯']

const canSend = computed(() => {
  // Rule: until the other side has replied, the visitor may send only one msg.
  const theyReplied = messages.value.some(
    (m) => m.sender_string_id === targetId.value,
  )
  const iSentCount = messages.value.filter(
    (m) => m.sender_string_id === store.me?.user_string_id,
  ).length
  return theyReplied || iSentCount < 1
})

async function load() {
  if (!store.me) await store.loadMe()
  const { data } = await api.get(`/api/messages/${targetId.value}`)
  messages.value = data
  await scrollToBottom()
}

async function scrollToBottom() {
  await nextTick()
  if (listRef.value) listRef.value.scrollTop = listRef.value.scrollHeight
}

onMounted(load)

async function send() {
  const text = draft.value.trim()
  if (!text || !canSend.value) return
  sending.value = true
  errorBanner.value = ''
  try {
    await api.post(`/api/messages/${targetId.value}`, { content: text })
    draft.value = ''
    await load()
  } catch (e: any) {
    errorBanner.value =
      e?.response?.data?.detail || i18n.t('message_send_failed')
  } finally {
    sending.value = false
  }
}

function pickEmoji(e: string) {
  draft.value += e
  showEmoji.value = false
}

function attach(type: 'image' | 'video' | 'voice') {
  alert(`${i18n.t('upload_placeholder')}: ${type}`)
}
</script>

<template>
  <div class="msg-page">
    <!-- Top banner: the one-message rule -->
    <div class="banner">
      {{ i18n.t('msg_rule_hint') }}
    </div>

    <!-- Messages -->
    <div ref="listRef" class="msg-list">
      <div
        v-for="m in messages"
        :key="m.id"
        class="msg-row"
        :class="{
          me: m.sender_string_id === store.me?.user_string_id,
          other: m.sender_string_id !== store.me?.user_string_id,
        }"
      >
        <div class="msg-bubble">
          <span v-if="m.content_type === 'text'">{{ m.content }}</span>
          <span v-else>[{{ m.content_type }}] {{ m.media_url }}</span>
        </div>
      </div>
      <p v-if="messages.length === 0" class="empty">
        {{ i18n.t('no_messages_yet') }}
      </p>
    </div>

    <div v-if="errorBanner" class="error-banner">{{ errorBanner }}</div>

    <!-- Composer -->
    <div class="composer">
      <div
        class="composer-avatar"
        :style="{ background: `hsl(${(store.me?.user_string_id?.length ?? 3) * 47 % 360},60%,45%)` }"
      >
        {{ store.me?.user_string_id?.slice(-2) || '??' }}
      </div>

      <input
        v-model="draft"
        :disabled="!canSend || sending"
        :placeholder="canSend ? i18n.t('message_placeholder') : i18n.t('wait_for_reply')"
        @keyup.enter="send"
      />

      <button class="icon-btn" @click="showEmoji = !showEmoji">😊</button>

      <div class="emoji-pop" v-if="showEmoji">
        <span v-for="e in EMOJIS" :key="e" @click="pickEmoji(e)">{{ e }}</span>
      </div>

      <button class="icon-btn" @click="attach('image')">🖼️</button>
      <button class="icon-btn" @click="attach('video')">🎬</button>
      <button class="icon-btn" @click="attach('voice')">🎤</button>

      <button class="send-btn" :disabled="!canSend || sending" @click="send">
        {{ i18n.t('send') }}
      </button>
    </div>
  </div>
</template>

<style scoped>
.msg-page {
  position: fixed;
  inset: 0;
  display: flex;
  flex-direction: column;
  background: #1a1a1a;
  z-index: 1000;
}
.banner {
  flex-shrink: 0;
  padding: 0.6rem 1rem;
  background: rgba(229, 184, 11, 0.12);
  color: var(--gold);
  font-size: 0.82rem;
  text-align: center;
  border-bottom: 1px solid rgba(229, 184, 11, 0.25);
}
.msg-list {
  flex: 1;
  overflow-y: auto;
  padding: 1rem 1rem 0.5rem;
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}
.msg-row {
  display: flex;
}
.msg-row.me {
  justify-content: flex-end;
}
.msg-row.other {
  justify-content: flex-start;
}
.msg-bubble {
  max-width: 70%;
  padding: 0.55rem 0.85rem;
  border-radius: 12px;
  font-size: 0.9rem;
  line-height: 1.5;
  word-break: break-word;
  color: #fff;
}
.msg-row.me .msg-bubble {
  background: #3b6f3b;
  border-bottom-right-radius: 2px;
}
.msg-row.other .msg-bubble {
  background: #3a3a3a;
  border-bottom-left-radius: 2px;
}
.empty {
  color: var(--text-dim);
  text-align: center;
  margin-top: 2rem;
}
.error-banner {
  flex-shrink: 0;
  padding: 0.5rem 1rem;
  background: rgba(231, 76, 60, 0.15);
  color: #ff8a80;
  text-align: center;
  font-size: 0.82rem;
}

/* ---------- composer ---------- */
.composer {
  flex-shrink: 0;
  display: flex;
  align-items: center;
  gap: 0.4rem;
  padding: 0.55rem 0.75rem;
  background: #0d0d0d;
  border-top: 1px solid #222;
  position: relative;
}
.composer-avatar {
  width: 34px;
  height: 34px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #fff;
  font-weight: 700;
  font-size: 0.72rem;
  flex-shrink: 0;
  border: 2px solid var(--gold);
}
.composer input {
  flex: 1;
  margin: 0;
  background: #1e1e1e;
  border: 1px solid #333;
  color: #fff;
  padding: 0.5rem 0.75rem;
  border-radius: 18px;
}
.icon-btn {
  background: transparent;
  border: none;
  color: #ccc;
  font-size: 1.15rem;
  cursor: pointer;
  padding: 0.25rem;
  flex-shrink: 0;
}
.icon-btn:hover {
  color: var(--gold);
}
.send-btn {
  background: var(--gold);
  color: #111;
  border: none;
  border-radius: 16px;
  padding: 0.45rem 0.9rem;
  font-weight: 700;
  font-size: 0.85rem;
  cursor: pointer;
  flex-shrink: 0;
}
.send-btn:disabled {
  opacity: 0.4;
  cursor: not-allowed;
}
.emoji-pop {
  position: absolute;
  bottom: calc(100% + 6px);
  right: 5rem;
  background: #1e1e1e;
  border: 1px solid #333;
  border-radius: 8px;
  padding: 0.35rem;
  display: flex;
  gap: 0.25rem;
  flex-wrap: wrap;
  max-width: 260px;
  z-index: 5;
}
.emoji-pop span {
  cursor: pointer;
  font-size: 1.15rem;
  padding: 0.15rem;
}
.emoji-pop span:hover {
  background: rgba(229, 184, 11, 0.15);
  border-radius: 4px;
}
</style>