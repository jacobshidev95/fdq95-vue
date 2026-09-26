<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useI18nStore } from '@/stores/i18n'
import { useAuthStore } from '@/stores/auth'
import { liveApi, type LiveSession } from '@/api/live'
import CategorySelect from '@/components/CategorySelect.vue'
import ActivityStatsPanel from '@/components/activity/ActivityStatsPanel.vue'
import PersonalStatsPanel from '@/components/activity/PersonalStatsPanel.vue'
import PersonalDataUploadDialog from '@/components/activity/PersonalDataUploadDialog.vue'
import RecordingPreviewDialog from '@/components/RecordingPreviewDialog.vue'
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

const activityTitle = ref('')
const activityCategory = ref<string | null>('activity')

const showInvite = ref(false)
const friends = ref<any[]>([])
const invitees = ref<any[]>([])

const showUploadDialog = ref(false)

let pollTimer: number | null = null

const isFullscreen = ref(false)
const canGoFullscreen = computed(
  () => !!activityTitle.value.trim() && !!activityCategory.value,
)

function toggleFullscreen() {
  if (!isFullscreen.value && !canGoFullscreen.value) return
  isFullscreen.value = !isFullscreen.value
}

const recorder = useRecording({ maxDurationSec: 20 * 60, maxSizeMB: 400 })
const showPreview = ref(false)
const isUploading = ref(false)
const uploadProgress = ref(0)

function fmtRecTime(sec: number): string {
  const m = Math.floor(sec / 60)
  const s = sec % 60
  return `${m.toString().padStart(2, '0')}:${s.toString().padStart(2, '0')}`
}

async function onToggleRecordEnd() {
  if (!recorder.isRecording.value) {
    try {
      await recorder.start()
    } catch (e: any) {
      alert((i18n.t('recording_upload_failed') || 'Record failed') + ': ' + (e?.message || ''))
    }
    return
  }
  const blob = await recorder.stop()
  if (blob && blob.size > 0) {
    showPreview.value = true
  } else {
    await endActivityAndReturn()
  }
}

function onPreviewDiscard() {
  recorder.discard()
  showPreview.value = false
  void endActivityAndReturn()
}

async function onPreviewConfirm() {
  const blob = recorder.takeBlob()
  if (!blob) {
    showPreview.value = false
    await endActivityAndReturn()
    return
  }
  await uploadAndPublish(blob)
  showPreview.value = false
  await endActivityAndReturn()
}

async function uploadAndPublish(blob: Blob) {
  isUploading.value = true
  try {
    const ext = blob.type.includes('mp4') ? 'mp4' : 'webm'
    const fd = new FormData()
    fd.append('file', blob, `activity-${Date.now()}.${ext}`)
    const { data: upload } = await api.post(
      '/api/videos/upload-video',
      fd,
      {
        headers: { 'Content-Type': 'multipart/form-data' },
        timeout: 1_800_000,
        onUploadProgress: (e) => {
          if (e.total) uploadProgress.value = Math.round((e.loaded / e.total) * 100)
        },
      }
    )
    await api.post('/api/videos', {
      title: activityTitle.value || 'Activity Recording',
      category: 'activity',       // ★ 唯一区别
      content_type: 'file',
      url: upload.url,
      duration_sec: recorder.duration.value,
      file_size: upload.size,
    })
    alert(i18n.t('recording_uploaded') || 'Recording published')
  } catch (e: any) {
    alert(e?.response?.data?.detail || i18n.t('recording_upload_failed') || 'Upload failed')
  } finally {
    isUploading.value = false
    uploadProgress.value = 0
  }
}

async function endActivityAndReturn() {
  try {
    await liveApi.end(roomId.value)
  } catch (e) {
    console.warn('[end] failed', e)
  }
  router.replace('/videos?tab=activity')
}

async function loadAll() {
  if (!roomId.value) { errorMsg.value = 'Missing room id'; loading.value = false; return }
  try {
    const s = await liveApi.getRoom(roomId.value)
    session.value = s
    activityTitle.value = s.title || localStorage.getItem('fdq95_activity_title') || ''
    activityCategory.value = s.category || localStorage.getItem('fdq95_activity_category') || 'activity'
    if (isHost.value && auth.user && s.host_user_id !== auth.user.user_id) {
      errorMsg.value = 'You are not the host of this activity'
      loading.value = false; return
    }
    const t = await liveApi.getToken(roomId.value)
    videoCallUrl.value = `${t.server_url}/${t.room_id}?jwt=${encodeURIComponent(t.token)}`
  } catch (e: any) {
    errorMsg.value = e?.response?.data?.detail ||
      (e?.response?.status === 403 ? 'You do not have permission to enter this activity' : 'Load failed')
  } finally { loading.value = false }
}

function startPolling() {
  pollTimer = window.setInterval(async () => {
    try { await liveApi.getRoom(roomId.value) } catch { router.replace('/activity') }
  }, 15000)
}

function saveTitleAndCategory() {
  localStorage.setItem('fdq95_activity_title', activityTitle.value)
  if (activityCategory.value) localStorage.setItem('fdq95_activity_category', activityCategory.value)
}

function shareRoom() {
  if (navigator.clipboard) navigator.clipboard.writeText(window.location.href)
}

async function openInvite() {
  showInvite.value = true
  try { const { data } = await api.get('/api/friends/list'); friends.value = data || [] }
  catch { friends.value = [] }
  try { invitees.value = await liveApi.listInvitees(roomId.value) } catch { invitees.value = [] }
}
async function inviteFriend(userStringId: string) {
  try {
    await liveApi.invite(roomId.value, userStringId)
    invitees.value = await liveApi.listInvitees(roomId.value)
  } catch (e: any) { alert(e?.response?.data?.detail || 'Invite failed') }
}

function onPersonalDataUploaded() {}

function goBack() {
  if (recorder.isRecording.value) {
    if (!confirm(i18n.t('recording_pending_warning') || 'You are recording. Leave anyway?')) return
    void recorder.stop()
    recorder.discard()
  }
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
  <div class="activity-page" :class="{ 'is-fullscreen': isFullscreen }">
    <div v-show="!isFullscreen" class="activity-top">
      <div class="title-row">
        <button type="button" class="back-btn" @click="goBack">‹</button>
        <input
          v-model="activityTitle" type="text" class="activity-title-input"
          :placeholder="i18n.t('activity_title_ph')" maxlength="120"
          :disabled="!isHost" @blur="saveTitleAndCategory"
        />
      </div>
      <div class="category-row">
        <CategorySelect
          v-model="activityCategory" storage-key="fdq95_activity_category"
          :placeholder="i18n.t('activity_category')" :disabled="!isHost"
        />
      </div>
    </div>

    <div v-if="loading" class="activity-status">{{ i18n.t('video_loading') }}</div>
    <div v-else-if="errorMsg" class="activity-status">
      <p>{{ errorMsg }}</p>
      <button @click="router.replace('/activity')">{{ i18n.t('back_to_list') }}</button>
    </div>

    <main v-else class="activity-body">
      <section class="left-col">
        <div class="video-frame">
          <iframe
            v-if="videoCallUrl" :key="videoCallUrl" :src="videoCallUrl"
            class="video-call-iframe" frameborder="0"
            allow="camera; microphone; fullscreen; display-capture; autoplay; clipboard-write; screen-wake-lock"
          />
        </div>

        <div class="action-bar">
          <button type="button" class="action-btn">
            🎁<span class="label">{{ i18n.t('live_btn_gift') }}</span>
          </button>
          <button type="button" class="action-btn">
            😊<span class="label">{{ i18n.t('live_btn_emoji') }}</span>
          </button>
          <button v-if="isHost" type="button" class="action-btn" @click="openInvite">
            👥<span class="label">{{ i18n.t('activity_btn_invite') }}</span>
          </button>
          <button v-else type="button" class="action-btn">
            📞<span class="label">{{ i18n.t('live_btn_call') }}</span>
          </button>
          <button type="button" class="action-btn" @click="shareRoom">
            📤<span class="label">{{ i18n.t('live_btn_share') }}</span>
          </button>
          <button type="button" class="action-btn like">
            ❤️<span class="label">{{ i18n.t('live_btn_like') }}</span>
          </button>

          <!-- ★ 单个切换按钮：Record / End -->
          <button
            v-if="isHost"
            type="button"
            class="action-btn"
            :class="recorder.isRecording.value ? 'recording-btn' : 'record-btn'"
            @click="onToggleRecordEnd"
          >
            <span>{{ recorder.isRecording.value ? '⏹' : '⏺' }}</span>
            <span class="label">
              {{ recorder.isRecording.value
                  ? `${fmtRecTime(recorder.duration.value)} · ${i18n.t('activity_btn_end')}`
                  : i18n.t('recording_start') }}
            </span>
          </button>

          <button
            type="button"
            class="action-btn fullscreen-btn"
            :disabled="!canGoFullscreen && !isFullscreen"
            @click.stop="toggleFullscreen"
          >
            <template v-if="isFullscreen">⤡<span class="label">{{ i18n.t('activity_exit_fullscreen') }}</span></template>
            <template v-else>⛶<span class="label">{{ i18n.t('activity_fullscreen') }}</span></template>
          </button>
        </div>

        <div v-if="isUploading" class="upload-bar">
          <span>{{ i18n.t('recording_uploading') }} {{ uploadProgress }}%</span>
          <div class="upload-track">
            <div class="upload-fill" :style="{ width: uploadProgress + '%' }"></div>
          </div>
        </div>
      </section>

      <aside class="right-col">
        <ActivityStatsPanel :room-id="roomId" class="activity-stats" />
        <PersonalStatsPanel :room-id="roomId" class="personal-stats" />
        <button
          type="button" class="personal-upload-btn"
          @click="showUploadDialog = true"
        >
          <span>⬆️</span>
          <span class="label">{{ i18n.t('personal_data_upload_btn') }}</span>
        </button>
      </aside>
    </main>

    <div v-if="showInvite" class="modal-backdrop" @click.self="showInvite = false">
      <div class="modal">
        <div class="modal-header">
          <h3>{{ i18n.t('activity_invite_title') }}</h3>
          <button @click="showInvite = false">✕</button>
        </div>
        <div class="modal-section">
          <h4>{{ i18n.t('activity_invited_count') }} ({{ invitees.length }})</h4>
          <ul>
            <li v-for="i in invitees" :key="i.user_string_id">
              {{ i.display_name }} <span class="muted">@{{ i.user_string_id }}</span>
            </li>
            <li v-if="invitees.length === 0" class="muted">{{ i18n.t('activity_none') }}</li>
          </ul>
        </div>
        <div class="modal-section">
          <h4>{{ i18n.t('friend_list') }}</h4>
          <ul>
            <li v-for="f in friends" :key="f.user_string_id">
              {{ f.display_name }} <span class="muted">@{{ f.user_string_id }}</span>
              <button
                v-if="!invitees.some(i => i.user_string_id === f.user_string_id)"
                @click="inviteFriend(f.user_string_id)"
              >{{ i18n.t('activity_invite_btn') }}</button>
              <span v-else class="muted">{{ i18n.t('activity_invited') }}</span>
            </li>
            <li v-if="friends.length === 0" class="muted">{{ i18n.t('no_friends_yet') }}</li>
          </ul>
        </div>
      </div>
    </div>

    <PersonalDataUploadDialog
      v-model:visible="showUploadDialog"
      :room-id="roomId"
      @uploaded="onPersonalDataUploaded"
    />

    <RecordingPreviewDialog
      v-model:visible="showPreview"
      :video-url="recorder.pendingUrl.value"
      :duration-sec="recorder.duration.value"
      :size-m-b="recorder.sizeMB.value"
      @confirm="onPreviewConfirm"
      @discard="onPreviewDiscard"
    />
  </div>
</template>

<style scoped>
.activity-page {
  position: fixed; inset: 0; z-index: 9999;
  display: flex; flex-direction: column;
  background: #000; color: #fff; overflow: hidden;
  box-sizing: border-box;
}
.activity-top {
  flex-shrink: 0; background: #0d0d0d;
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
.activity-title-input {
  flex: 1; min-width: 0;
  background: #1a1a1a; border: 1px solid #333;
  border-radius: 8px; color: #fff;
  padding: 0.4rem 0.7rem; font-size: 0.9rem; font-weight: 600;
}
.activity-title-input:focus { outline: none; border-color: #8b5cf6; }
.category-row { padding: 0.35rem 0.7rem 0.5rem; }
.activity-status {
  display: flex; flex-direction: column;
  align-items: center; justify-content: center;
  flex: 1; gap: 1rem; color: #ccc;
}
.activity-status button {
  background: #8b5cf6; color: #fff;
  border: none; padding: 0.5rem 1rem;
  border-radius: 8px; cursor: pointer;
}
.activity-body {
  display: grid; grid-template-columns: 3fr 2fr;
  gap: 0.5rem; padding: 0.5rem;
  flex: 1 1 auto; min-height: 0; overflow: hidden;
}
.left-col {
  display: flex; flex-direction: column;
  gap: 0.4rem; min-height: 0; min-width: 0;
}
.video-frame {
  position: relative; flex: 1 1 auto; min-height: 0;
  background: #000; border-radius: 10px;
  overflow: hidden; border: 1px solid #222;
}
.is-fullscreen .video-frame { border-radius: 0; border: none; }
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
.action-btn.like:hover {
  background: rgba(231, 76, 60, 0.15);
  border-color: #e74c3c;
}
.action-btn.fullscreen-btn {
  border-color: rgba(139, 92, 246, 0.6);
  background: rgba(139, 92, 246, 0.25);
}
.action-btn.fullscreen-btn:hover:not(:disabled) {
  background: rgba(139, 92, 246, 0.7);
}
.action-btn.fullscreen-btn:disabled {
  opacity: 0.35; cursor: not-allowed;
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
  flex-shrink: 0; padding: 0.4rem 0.6rem;
  background: rgba(139, 92, 246, 0.12);
  border: 1px solid rgba(139, 92, 246, 0.4);
  border-radius: 8px; color: #c4b5fd; font-size: 0.8rem;
}
.upload-track {
  margin-top: 0.3rem; height: 6px;
  border-radius: 3px; background: rgba(255, 255, 255, 0.12);
  overflow: hidden;
}
.upload-fill {
  height: 100%;
  background: linear-gradient(90deg, #8b5cf6, #6366f1);
  transition: width 0.2s;
}
.right-col {
  display: grid; grid-template-rows: 3fr 1fr auto;
  gap: 0.5rem; min-height: 0; min-width: 0;
  overflow: hidden;
}
.activity-stats, .personal-stats { min-height: 0; }
.personal-upload-btn {
  flex-shrink: 0;
  display: flex; flex-direction: column;
  align-items: center; justify-content: center;
  gap: 0.1rem; padding: 0.45rem 0.2rem;
  background: linear-gradient(135deg, #8b5cf6, #6366f1);
  border: none; border-radius: 10px;
  color: #fff; font-size: 1.1rem; font-weight: 700;
  cursor: pointer;
  box-shadow: 0 4px 14px rgba(139, 92, 246, 0.4);
}
.personal-upload-btn .label {
  font-size: 0.68rem; color: #fff; font-weight: 500;
}
.modal-backdrop {
  position: fixed; inset: 0;
  background: rgba(0, 0, 0, 0.7);
  display: flex; align-items: center; justify-content: center;
  z-index: 200;
}
.modal {
  width: 90%; max-width: 480px;
  max-height: 80vh; overflow-y: auto;
  background: #111; border: 1px solid #333;
  border-radius: 12px; padding: 1rem; color: #fff;
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
  .activity-body {
    grid-template-columns: 1fr;
    gap: 0.4rem; padding: 0.4rem; overflow-y: auto;
  }
  .right-col { grid-template-rows: 300px 200px auto; }
}
</style>