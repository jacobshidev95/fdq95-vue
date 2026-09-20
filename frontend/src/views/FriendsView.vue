<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { useProfileStore } from '@/stores/profile'
import { useI18nStore } from '@/stores/i18n'

const router = useRouter()
const store = useProfileStore()
const i18n = useI18nStore()

const loading = ref(false)
const actionMsg = ref('')
const actionErr = ref('')

// 只显示 PENDING 状态的请求
const pendingRequests = computed(() =>
  store.inbox.filter((r) => r.status === 'pending' || r.status === 'PENDING'),
)

async function load() {
  loading.value = true
  actionMsg.value = ''
  actionErr.value = ''
  try {
    await store.loadIncomingRequests()
    await store.loadFriends()
  } catch {
    actionErr.value = '加载失败，请刷新重试'
  } finally {
    loading.value = false
  }
}

async function onAccept(requestId: string, name: string) {
  actionMsg.value = ''
  actionErr.value = ''
  try {
    await store.acceptRequest(requestId)
    actionMsg.value = `已同意 ${name} 的好友申请`
    await store.loadFriends()
  } catch (e: any) {
    actionErr.value =
      e?.response?.data?.detail || '同意失败，请重试'
  }
}

async function onReject(requestId: string, name: string) {
  actionMsg.value = ''
  actionErr.value = ''
  try {
    await store.rejectRequest(requestId)
    actionMsg.value = `已拒绝 ${name} 的好友申请`
  } catch (e: any) {
    actionErr.value =
      e?.response?.data?.detail || '拒绝失败，请重试'
  }
}

function goProfile(userStringId: string) {
  router.push(`/profile/${userStringId}`)
}

onMounted(load)
</script>

<template>
  <div class="friends-page">
    <h1 class="title-gold page-title">
      👥 {{ i18n.t('friend_list') || 'Friend List' }}
    </h1>

    <div v-if="actionMsg" class="notice notice-ok">{{ actionMsg }}</div>
    <div v-if="actionErr" class="notice notice-error">{{ actionErr }}</div>

    <div v-if="loading" class="loading-cell">Loading…</div>

    <template v-else>
      <!-- ========== 好友申请列表 ========== -->
      <section v-if="pendingRequests.length > 0" class="section">
        <h2 class="section-title">
          📩 好友申请 ({{ pendingRequests.length }})
        </h2>
        <div class="request-list">
          <div
            v-for="req in pendingRequests"
            :key="req.id"
            class="request-card"
          >
            <div class="request-info" @click="goProfile(req.other_string_id)">
              <div class="req-avatar">
                {{ req.other_string_id.slice(-2).toUpperCase() }}
              </div>
              <div class="req-text">
                <div class="req-name">{{ req.other_display_name }}</div>
                <div class="req-id">@{{ req.other_string_id }}</div>
              </div>
            </div>
            <div class="request-actions">
              <button
                class="btn accept-btn"
                @click="onAccept(req.id, req.other_display_name)"
              >
                ✓ 同意
              </button>
              <button
                class="btn reject-btn"
                @click="onReject(req.id, req.other_display_name)"
              >
                ✗ 拒绝
              </button>
            </div>
          </div>
        </div>
      </section>

      <section v-else class="section">
        <p class="empty-hint">暂无待处理的好友申请</p>
      </section>

      <!-- ========== 好友列表 ========== -->
      <section class="section">
        <h2 class="section-title">
          👥 我的好友 ({{ store.friends.length }})
        </h2>
        <div v-if="store.friends.length === 0" class="empty-hint">
          还没有好友，去个人主页申请添加吧
        </div>
        <div v-else class="friend-list">
          <div
            v-for="f in store.friends"
            :key="f.user_string_id"
            class="friend-card"
            @click="goProfile(f.user_string_id)"
          >
            <div class="friend-avatar">
              {{ f.user_string_id.slice(-2).toUpperCase() }}
            </div>
            <div class="friend-text">
              <div class="friend-name">{{ f.display_name }}</div>
              <div class="friend-id">@{{ f.user_string_id }}</div>
            </div>
            <span class="friend-badge">好友</span>
          </div>
        </div>
      </section>
    </template>
  </div>
</template>

<style scoped>
.friends-page {
  width: 100%;
  max-width: 640px;
  padding: 1rem 1.25rem 3rem;
  margin: 0 auto;
}
.page-title {
  margin: 0 0 1.25rem;
  font-size: 1.3rem;
}

.section {
  margin-bottom: 1.75rem;
}
.section-title {
  font-size: 1rem;
  color: var(--gold);
  margin: 0 0 0.75rem;
  font-weight: 600;
}

/* ---- request cards ---- */
.request-list {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}
.request-card {
  display: flex;
  justify-content: space-between;
  align-items: center;
  background: var(--bg-soft);
  border: 1px solid var(--border);
  border-radius: 10px;
  padding: 0.75rem 1rem;
  gap: 0.75rem;
}
.request-info {
  display: flex;
  align-items: center;
  gap: 0.65rem;
  cursor: pointer;
  flex: 1 1 0;
  min-width: 0;
}
.req-avatar {
  width: 42px;
  height: 42px;
  border-radius: 50%;
  background: hsl(210, 60%, 45%);
  color: #fff;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: 700;
  font-size: 0.85rem;
  flex-shrink: 0;
}
.req-text {
  min-width: 0;
}
.req-name {
  color: #fff;
  font-weight: 600;
  font-size: 0.9rem;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
.req-id {
  color: var(--text-dim);
  font-size: 0.78rem;
}

.request-actions {
  display: flex;
  gap: 0.4rem;
  flex-shrink: 0;
}
.accept-btn {
  background: #2ecc71;
  border: 1px solid #2ecc71;
  color: #fff;
  padding: 0.4rem 0.75rem;
  border-radius: 6px;
  font-size: 0.82rem;
  font-weight: 600;
  cursor: pointer;
}
.accept-btn:hover {
  background: #27ae60;
}
.reject-btn {
  background: transparent;
  border: 1px solid #e74c3c;
  color: #ff8a80;
  padding: 0.4rem 0.75rem;
  border-radius: 6px;
  font-size: 0.82rem;
  font-weight: 600;
  cursor: pointer;
}
.reject-btn:hover {
  background: rgba(231, 76, 60, 0.15);
}

/* ---- friend cards ---- */
.friend-list {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}
.friend-card {
  display: flex;
  align-items: center;
  gap: 0.65rem;
  background: var(--bg-soft);
  border: 1px solid var(--border);
  border-radius: 10px;
  padding: 0.65rem 1rem;
  cursor: pointer;
  transition: border-color 0.15s;
}
.friend-card:hover {
  border-color: var(--gold);
}
.friend-avatar {
  width: 42px;
  height: 42px;
  border-radius: 50%;
  background: hsl(150, 60%, 40%);
  color: #fff;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: 700;
  font-size: 0.85rem;
  flex-shrink: 0;
}
.friend-text {
  flex: 1 1 0;
  min-width: 0;
}
.friend-name {
  color: #fff;
  font-weight: 600;
  font-size: 0.9rem;
}
.friend-id {
  color: var(--text-dim);
  font-size: 0.78rem;
}
.friend-badge {
  background: #2ecc71;
  color: #fff;
  font-size: 0.68rem;
  font-weight: 700;
  padding: 0.15rem 0.5rem;
  border-radius: 4px;
}

/* ---- misc ---- */
.loading-cell {
  text-align: center;
  color: var(--text-dim);
  padding: 2rem;
}
.empty-hint {
  color: var(--text-dim);
  font-size: 0.88rem;
  text-align: center;
  padding: 1.25rem;
}
.notice {
  padding: 0.7rem 1rem;
  border-radius: 6px;
  margin: 0 0 1rem;
  font-size: 0.88rem;
}
.notice-ok {
  background: rgba(46, 204, 113, 0.15);
  border: 1px solid #2ecc71;
  color: #a5f5c6;
}
.notice-error {
  background: rgba(231, 76, 60, 0.15);
  border: 1px solid #e74c3c;
  color: #ff8a80;
}
</style>