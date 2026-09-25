<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useI18nStore } from '@/stores/i18n'
import { useAuthStore } from '@/stores/auth'
import { liveApi, type LiveSession } from '@/api/live'
import CategorySelect from '@/components/CategorySelect.vue'
import { api } from '@/api/client'
import { useRecording } from '@/composables/useRecording'

const route = useRoute()
const router = useRouter()
const i18n = useI18nStore()
const auth = useAuthStore()

const isHost = computed(() => route.meta.host === true)
const roomId = computed(() => String(route.params.roomId || ''))

const session = ref<LiveSession | null>(null)
const loading = ref(true)
const errorMsg = ref('')
const videoCallUrl = ref('')

const liveTitle = ref('')
const liveCategory = ref<string | null>(null)

const chatMessage = ref('')
const chatMessages = ref<Array<{ from: string; text: string; time: string }>>([])

const showInvite = ref(false)
const friends = ref<any[]>([])
const invitees = ref<any[]>([])

let pollTimer: number | null = null

const FIELD_CAMERA_BASE =
  import.meta.env.VITE_FIELD_CAMERA_URL || 'https://webcam.fdq95.com'
const fieldCameraUrl = computed(() =>
  isHost.value ? FIELD_CAMERA_BASE : `${FIELD_CAMERA_BASE}?readonly=1`
)

const isFullscreen = ref(false)
const canGoFullscreen = computed(
  () => !!liveTitle.value.trim() && !!liveCategory.value,
)

function toggleFullscreen() {
  if (!isFullscreen.value && !canGoFullscreen.value) return
  isFullscreen.value = !isFullscreen.value
}

// ★ 录制
const recorder = useRecording({ maxDurationSec: 20 * 60, maxSizeMB: 400 })
const uploadProgress = ref(0)
const isUploading = ref(false)

async function onStartRecord() {
  try {
    await recorder.start()
  } catch (e: any) {
    alert('无法开始录制：' + (e?.message || '权限被拒绝'))
  }
}
async function onStopRecord() {
  const blob = await recorder.stop()
  if (blob) {
    alert(
      `录制已停止，大小 ${(blob.size / 1024 / 1024).toFixed(1)} MB。\n` +
      `点击「结束」时会上传并发布。`
    )
  }
}

function fmtRecTime(sec: number): string {
  const m = Math.floor(sec / 60)
  const s = sec % 60
  return `${m.toString().padStart(2, '0')}:${s.toString().padStart(2, '0')}`
}

async function loadAll() {
  if (!roomId.value) {
    errorMsg.value = '缺少房间号'
    loading.value = false
    return
  }
  try {
    const s = await liveApi.getRoom(roomId.value)
    session.value = s
    liveTitle.value = s.title || localStorage.getItem('fdq95_live_title') || ''
    liveCategory.value =
      s.category || localStorage.getItem('fdq95_live_category')

    if (isHost.value && auth.user && s.host_user_id !== auth.user.user_id) {
      errorMsg.value = '你不是该直播间的主播'
      loading.value = false
      return
    }

    const t = await liveApi.getToken(roomId.value)
    videoCallUrl.value = `${t.server_url}/${t.room_id}?jwt=${encodeURIComponent(
      t.token
    )}`
  } catch (e: any) {
    errorMsg.value =
      e?.response?.data?.detail ||
      (e?.response?.status === 403
        ? '你没有权限进入该直播间（需要是主播好友或被邀请）'
        : '加载失败')
  } finally {
    loading.value = false
  }
}

function startPolling() {
  pollTimer = window.setInterval(async () => {
    try {
      await liveApi.getRoom(roomId.value)
    } catch {
      router.replace('/live')
    }
  }, 15000)
}

async function onEndLive() {
  if (!confirm('确定结束这场直播吗？')) return

  // 1. 若在录制，先停止
  let blob: Blob | null = null
  if (recorder.isRecording.value) {
    blob = await recorder.stop()
  }

  // 2. 结束直播会话
  try {
    await liveApi.end(roomId.value)
  } catch (e) {
    console.warn('[end] failed', e)
  }

  // 3. 上传录制并发布到 Video 表
  if (blob && blob.size > 0) {
    isUploading.value = true
    try {
      const ext = blob.type.includes('mp4') ? 'mp4' : 'webm'
      const fd = new FormData()
      fd.append('file', blob, `live-${Date.now()}.${ext}`)
      const { data: upload } = await api.post(
        '/api/videos/upload-video',
        fd,
        {
          headers: { 'Content-Type': 'multipart/form-data' },
          timeout: 1_800_000,
          onUploadProgress: (e) => {
            if (e.total) {
              uploadProgress.value = Math.round((e.loaded / e.total) * 100)
            }
          },
        }
      )
      await api.post('/api/videos', {
        title: liveTitle.value || '直播录制',
        category: 'live',
        content_type: 'file',
        url: upload.url,
        duration_sec: recorder.duration.value,
        file_size: upload.size,
      })
      alert('直播已结束，录制视频已发布到「直播」列表。')
    } catch (e: any) {
      alert(e?.response?.data?.detail || '录制上传失败')
    } finally {
      isUploading.value = false
      uploadProgress.value = 0
    }
  }

  router.replace('/live')
}

function saveTitleAndCategory() {
  localStorage.setItem('fdq95_live_title', liveTitle.value)
  if (liveCategory.value) {
    localStorage.setItem('fdq95_live_category', liveCategory.value)
  }
}

function sendChatMessage() {
  const text = chatMessage.value.trim()
  if (!text) return
  chatMessages.value.push({
    from: isHost.value ? '主播' : auth.user?.first_name || '我',
    text,
    time: new Date().toLocaleTimeString(),
  })
  chatMessage.value = ''
}

function shareRoom() {
  if (navigator.clipboard) {
    navigator.clipboard.writeText(window.location.href)
  }
}

async function openInvite() {
  showInvite.value = true
  try {
    const { data } = await api.get('/api/friends/list')
    friends.value = data || []
  } catch {
    friends.value = []
  }
  try {
    invitees.value = await liveApi.listInvitees(roomId.value)
  } catch {
    invitees.value = []
  }
}

async function inviteFriend(userStringId: string) {
  try {
    await liveApi.invite(roomId.value, userStringId)
    invitees.value = await liveApi.listInvitees(roomId.value)
  } catch (e: any) {
    alert(e?.response?.data?.detail || '邀请失败')
  }
}

function goBack() {
  router.back()
}

onMounted(async () => {
  document.documentElement.style.overflow = 'hidden'
  document.body.style.overflow = 'hidden'
  await loadAll()
  if (session.value) startPolling()
})

onBeforeUnmount(() => {
  document.documentElement.style.overflow = ''
  document.body.style.overflow = ''
  if (pollTimer) window.clearInterval(pollTimer)
})
</script>

<template>
  <div class="live-page" :class="{ 'is-fullscreen': isFullscreen }">
    <div v-show="!isFullscreen" class="live-top">
      <div class="title-row">
        <button type="button" class="back-btn" @click="goBack">‹</button>
        <input
          v-model="liveTitle"
          type="text"
          class="live-title-input"
          placeholder="直播标题"
          maxlength="120"
          :disabled="!isHost"
          @blur="saveTitleAndCategory"
        />
      </div>
      <div class="category-row">
        <CategorySelect
          v-model="liveCategory"
          storage-key="fdq95_live_category"
          placeholder="选择分类"
          :disabled="!isHost"
        />
      </div>
    </div>

    <div v-if="loading" class="live-status">加载中…</div>
    <div v-else-if="errorMsg" class="live-status">
      <p>{{ errorMsg }}</p>
      <button @click="router.replace('/live')">返回大厅</button>
    </div>

    <main v-else class="live-body">
      <section class="left-col">
        <div class="video-frame">
          <iframe
            v-if="videoCallUrl"
            :key="videoCallUrl"
            :src="videoCallUrl"
            class="video-call-iframe"
            frameborder="0"
            allow="camera; microphone; fullscreen; display-capture; autoplay; clipboard-write; screen-wake-lock"
          />
        </div>

        <div class="action-bar">
          <button type="button" class="action-btn">🎁<span class="label">礼物</span></button>
          <button type="button" class="action-btn">😊<span class="label">表情</span></button>
          <button
            v-if="isHost"
            type="button"
            class="action-btn"
            @click="openInvite"
          >👥<span class="label">邀请</span></button>
          <button
            v-else
            type="button"
            class="action-btn"
          >📞<span class="label">通话</span></button>
          <button
            type="button"
            class="action-btn"
            @click="shareRoom"
          >📤<span class="label">分享</span></button>
          <button type="button" class="action-btn like">❤️<span class="label">喜欢</span></button>
          <!-- ★ 录制按钮：仅主播 -->
          <button
            v-if="isHost && !recorder.isRecording.value"
            type="button"
            class="action-btn record-btn"
            @click="onStartRecord"
          >⏺<span class="label">开始录制</span></button>
          <button
            v-else-if="isHost && recorder.isRecording.value"
            type="button"
            class="action-btn recording-btn"
            @click="onStopRecord"
          >
            ⏹<span class="label">{{ fmtRecTime(recorder.duration.value) }}</span>
          </button>
          <button
            v-if="isHost"
            type="button"
            class="action-btn danger"
            @click="onEndLive"
          >⏹<span class="label">结束</span></button>
          <button
            type="button"
            class="action-btn fullscreen-btn"
            :disabled="!canGoFullscreen && !isFullscreen"
            @click.stop="toggleFullscreen"
          >
            <template v-if="isFullscreen">⤡<span class="label">退出全屏</span></template>
            <template v-else>⛶<span class="label">全屏</span></template>
          </button>
        </div>

        <!-- 上传进度 -->
        <div v-if="isUploading" class="upload-bar">
          <span>正在上传录制视频… {{ uploadProgress }}%</span>
          <div class="upload-track">
            <div class="upload-fill" :style="{ width: uploadProgress + '%' }"></div>
          </div>
        </div>
      </section>

      <aside class="right-col">
        <div class="field-camera-frame">
          <iframe
            :src="fieldCameraUrl"
            class="field-camera-iframe"
            frameborder="0"
            allow="camera; microphone; fullscreen; autoplay"
            sandbox="allow-same-origin allow-scripts allow-forms allow-popups"
          />
        </div>
        <div class="audience-panel">
          <div class="audience-messages">
            <div v-if="chatMessages.length === 0" class="empty-hint">
              暂无消息
            </div>
            <div
              v-for="(msg, idx) in chatMessages"
              :key="idx"
              class="audience-msg"
            >
              <span class="msg-from">{{ msg.from }}:</span>
              <span class="msg-text">{{ msg.text }}</span>
              <span class="msg-time">{{ msg.time }}</span>
            </div>
          </div>
          <div class="audience-input-row">
            <input
              v-model="chatMessage"
              type="text"
              class="audience-input"
              placeholder="说点什么…"
              @keyup.enter="sendChatMessage"
            />
            <button
              type="button"
              class="send-btn"
              :disabled="!chatMessage.trim()"
              @click="sendChatMessage"
            >发送</button>
          </div>
        </div>
      </aside>
    </main>

    <div v-if="showInvite" class="modal-backdrop" @click.self="showInvite = false">
      <div class="modal">
        <div class="modal-header">
          <h3>邀请好友进入直播间</h3>
          <button @click="showInvite = false">✕</button>
        </div>
        <div class="modal-section">
          <h4>已邀请 ({{ invitees.length }})</h4>
          <ul>
            <li v-for="i in invitees" :key="i.user_string_id">
              {{ i.display_name }} <span class="muted">@{{ i.user_string_id }}</span>
            </li>
            <li v-if="invitees.length === 0" class="muted">暂无</li>
          </ul>
        </div>
        <div class="modal-section">
          <h4>好友列表</h4>
          <ul>
            <li v-for="f in friends" :key="f.user_string_id">
              {{ f.display_name }} <span class="muted">@{{ f.user_string_id }}</span>
              <button
                v-if="!invitees.some(i => i.user_string_id === f.user_string_id)"
                @click="inviteFriend(f.user_string_id)"
              >邀请</button>
              <span v-else class="muted">已邀请</span>
            </li>
            <li v-if="friends.length === 0" class="muted">暂无好友</li>
          </ul>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.live-page {
  display: flex; flex-direction: column;
  width: 100vw; height: 100vh; height: 100dvh;
  background: #000; color: #fff; overflow: hidden;
  box-sizing: border-box;
}

.live-top {
  flex-shrink: 0;
  background: #0d0d0d;
  border-bottom: 1px solid #222;
}
.title-row {
  display: flex; align-items: center; gap: 0.6rem;
  padding: 0.4rem 0.7rem;
}
.back-btn {
  background: transparent; border: none; color: #fff;
  font-size: 1.8rem; line-height: 1; cursor: pointer;
  padding: 0 0.2rem; flex-shrink: 0;
}
.live-title-input {
  flex: 1; min-width: 0;
  background: #1a1a1a; border: 1px solid #333;
  border-radius: 8px; color: #fff;
  padding: 0.4rem 0.7rem; font-size: 0.9rem; font-weight: 600;
}
.live-title-input:focus { outline: none; border-color: #8b5cf6; }

.category-row { padding: 0.35rem 0.7rem 0.5rem; }

.live-status {
  display: flex; flex-direction: column;
  align-items: center; justify-content: center;
  flex: 1; gap: 1rem; color: #ccc;
}
.live-status button {
  background: #8b5cf6; color: #fff;
  border: none; padding: 0.5rem 1rem;
  border-radius: 8px; cursor: pointer;
}

.live-body {
  display: grid;
  grid-template-columns: 3fr 2fr;
  gap: 0.5rem; padding: 0.5rem;
  flex: 1 1 auto; min-height: 0; overflow: hidden;
}
.live-page.is-fullscreen .live-body {
  grid-template-columns: 1fr;
  gap: 0; padding: 0;
}

.left-col {
  display: flex; flex-direction: column; gap: 0.4rem; min-height: 0;
}
.video-frame {
  position: relative;
  flex: 1 1 auto; min-height: 0;
  background: #000; border-radius: 10px;
  overflow: hidden; border: 1px solid #222;
}
.video-call-iframe {
  width: 100%; height: 100%; display: block; border: 0;
  position: relative; z-index: 0;
}

.action-bar {
  display: flex; gap: 0.35rem; padding: 0; flex-shrink: 0;
}
.action-btn {
  flex: 1 1 0; min-width: 0;
  display: flex; flex-direction: column;
  align-items: center; gap: 0.1rem;
  padding: 0.45rem 0.2rem;
  background: #111;
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 6px; color: #fff;
  cursor: pointer; transition: all 0.15s;
  font-size: 1.1rem;
}
.action-btn:hover {
  background: rgba(139, 92, 246, 0.15);
  border-color: #8b5cf6;
}
.action-btn .label {
  font-size: 0.68rem; color: rgba(255, 255, 255, 0.75);
}
.action-btn.danger {
  border-color: rgba(231, 76, 60, 0.6);
  background: rgba(231, 76, 60, 0.1);
}
.action-btn.fullscreen-btn {
  border-color: rgba(139, 92, 246, 0.6);
  background: rgba(139, 92, 246, 0.25);
}
.action-btn.record-btn {
  border-color: rgba(231, 76, 60, 0.5);
  color: #ff8a80;
}
.action-btn.recording-btn {
  border-color: #e74c3c;
  background: rgba(231, 76, 60, 0.25);
  color: #fff;
  animation: recPulse 1.2s infinite;
}
@keyframes recPulse {
  0%, 100% { box-shadow: 0 0 0 0 rgba(231, 76, 60, 0.5); }
  50%      { box-shadow: 0 0 0 6px rgba(231, 76, 60, 0); }
}

.upload-bar {
  flex-shrink: 0;
  padding: 0.4rem 0.6rem;
  background: rgba(139, 92, 246, 0.12);
  border: 1px solid rgba(139, 92, 246, 0.4);
  border-radius: 8px;
  color: #c4b5fd;
  font-size: 0.8rem;
}
.upload-track {
  margin-top: 0.3rem;
  height: 6px; border-radius: 3px;
  background: rgba(255, 255, 255, 0.12);
  overflow: hidden;
}
.upload-fill {
  height: 100%;
  background: linear-gradient(90deg, #8b5cf6, #6366f1);
  transition: width 0.2s;
}

.right-col {
  display: grid;
  grid-template-rows: 1fr 1fr;
  gap: 0.5rem;
  min-height: 0; min-width: 0;
  overflow: hidden;
}
.field-camera-frame {
  position: relative;
  width: 100%; height: 100%;
  background: #000; border-radius: 10px;
  overflow: hidden; border: 1px solid #222;
}
.field-camera-iframe {
  position: absolute; inset: 0;
  width: 100%; height: 100%;
  display: block; border: 0;
}
.audience-panel {
  min-height: 0;
  display: flex; flex-direction: column;
  background: #111; border-radius: 10px;
  border: 1px solid #222; overflow: hidden;
}
.audience-messages {
  flex: 1 1 auto; min-height: 0; overflow-y: auto;
  padding: 0.5rem 0.7rem;
  display: flex; flex-direction: column; gap: 0.3rem;
}
.empty-hint {
  color: rgba(255, 255, 255, 0.35);
  font-size: 0.8rem; text-align: center; padding: 0.8rem 0;
}
.audience-msg { font-size: 0.82rem; line-height: 1.35; word-break: break-word; }
.msg-from { color: #c4b5fd; font-weight: 600; margin-right: 0.25rem; }
.msg-text { color: #fff; }
.msg-time { color: rgba(255, 255, 255, 0.35); font-size: 0.68rem; margin-left: 0.35rem; }
.audience-input-row {
  display: flex; gap: 0.35rem; padding: 0.4rem 0.5rem;
  background: #0d0d0d; border-top: 1px solid #222; flex-shrink: 0;
}
.audience-input {
  flex: 1; min-width: 0;
  background: #1a1a1a; border: 1px solid #333;
  border-radius: 6px; color: #fff;
  padding: 0.4rem 0.6rem; font-size: 0.85rem;
}
.send-btn {
  background: #8b5cf6; color: #fff; border: none;
  border-radius: 6px; padding: 0 0.85rem;
  font-weight: 600; font-size: 0.82rem; cursor: pointer;
}
.send-btn:disabled { opacity: 0.4; cursor: not-allowed; }

.modal-backdrop {
  position: fixed; inset: 0;
  background: rgba(0, 0, 0, 0.7);
  display: flex; align-items: center; justify-content: center;
  z-index: 200;
}
.modal {
  width: 90%; max-width: 480px; max-height: 80vh;
  overflow-y: auto; background: #111;
  border: 1px solid #333; border-radius: 12px;
  padding: 1rem; color: #fff;
}
.modal-header {
  display: flex; justify-content: space-between; align-items: center;
  margin-bottom: 0.8rem;
}
.modal-header h3 { margin: 0; font-size: 1rem; }
.modal-header button {
  background: transparent; border: none;
  color: #fff; font-size: 1.1rem; cursor: pointer;
}
.modal-section { margin-bottom: 1rem; }
.modal-section h4 { margin: 0 0 0.4rem; font-size: 0.85rem; opacity: 0.7; }
.modal-section ul { list-style: none; padding: 0; margin: 0; }
.modal-section li {
  display: flex; align-items: center; justify-content: space-between;
  gap: 0.5rem; padding: 0.4rem 0;
  border-bottom: 1px solid #222; font-size: 0.85rem;
}
.modal-section li button {
  background: #8b5cf6; color: #fff;
  border: none; padding: 0.25rem 0.6rem;
  border-radius: 6px; font-size: 0.75rem; cursor: pointer;
}
.muted { color: rgba(255, 255, 255, 0.4); font-size: 0.8rem; }

@media (max-width: 900px) {
  .live-body {
    grid-template-columns: 1fr;
    gap: 0.4rem; padding: 0.4rem; overflow-y: auto;
  }
}
</style>