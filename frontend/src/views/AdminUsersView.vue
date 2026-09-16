<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { api } from '@/api/client'
import { useI18nStore } from '@/stores/i18n'
import { useAuthStore } from '@/stores/auth'

const i18n = useI18nStore()
const auth = useAuthStore()
const router = useRouter()

interface AdminUserRow {
  id: string
  email: string
  user_id: string
  first_name: string | null
  last_name: string | null
  country: string | null
  region: string | null
  role: 'provider' | 'consumer'
  provider_level: string | null
  admin_scope_country: string | null
  admin_scope_region: string | null
  is_frozen: boolean
  is_active: boolean
  is_verified: boolean
  created_at: string | null
}

const users = ref<AdminUserRow[]>([])
const loading = ref(false)
const page = ref(1)
const pageSize = 20
const total = ref(0)
const search = ref('')
const onlyFrozen = ref<boolean | null>(null)
const actionMessage = ref('')
const actionError = ref('')

const isAdmin = computed(() => {
  const lvl = auth.user?.provider_level
  return lvl === 'level_0' || lvl === 'level_1' || lvl === 'level_2'
})

const isSystemAdmin = computed(() => auth.user?.provider_level === 'level_0')
const isNationalAdmin = computed(() => auth.user?.provider_level === 'level_1')
const isRegionalAdmin = computed(() => auth.user?.provider_level === 'level_2')

const totalPages = computed(() => Math.max(1, Math.ceil(total.value / pageSize)))

async function load() {
  if (!isAdmin.value) return
  loading.value = true
  actionMessage.value = ''
  actionError.value = ''
  try {
    const params: Record<string, unknown> = {
      page: page.value,
      page_size: pageSize,
    }
    if (search.value.trim()) params.q = search.value.trim()
    if (onlyFrozen.value === true) params.only_frozen = true
    else if (onlyFrozen.value === false) params.only_frozen = false

    const { data } = await api.get('/api/admin/users', { params })
    users.value = data.users
    total.value = data.total
  } catch (e) {
    actionError.value = i18n.t('admin_load_failed')
  } finally {
    loading.value = false
  }
}

function goPage(p: number) {
  if (p < 1 || p > totalPages.value) return
  page.value = p
  load()
}

async function freezeUser(u: AdminUserRow) {
  if (!confirm(`${i18n.t('admin_confirm_freeze')} @${u.user_id}?`)) return
  try {
    await api.post(`/api/admin/users/${u.id}/freeze`)
    actionMessage.value = `${i18n.t('admin_frozen')} @${u.user_id}`
    await load()
  } catch (e) {
    actionError.value = i18n.t('admin_action_failed')
  }
}

async function unfreezeUser(u: AdminUserRow) {
  try {
    await api.post(`/api/admin/users/${u.id}/unfreeze`)
    actionMessage.value = `${i18n.t('admin_unfrozen')} @${u.user_id}`
    await load()
  } catch (e) {
    actionError.value = i18n.t('admin_action_failed')
  }
}

async function deleteUser(u: AdminUserRow) {
  const confirmed = confirm(
    `${i18n.t('admin_confirm_delete')} @${u.user_id} (${u.email})?\n\n${i18n.t('admin_delete_warning')}`,
  )
  if (!confirmed) return
  try {
    await api.delete(`/api/admin/users/${u.id}`)
    actionMessage.value = `${i18n.t('admin_deleted')} @${u.user_id}`
    await load()
  } catch (e) {
    actionError.value = i18n.t('admin_action_failed')
  }
}

function levelLabel(lvl: string | null): string {
  if (!lvl) return '—'
  const key = `level_${lvl.replace('level_', '')}`
  return i18n.t(key) || lvl
}

function canAct(u: AdminUserRow): boolean {
  // The server enforces this too; this is only for hiding buttons
  if (!auth.user) return false
  if (auth.user.id === u.id) return false
  if (isSystemAdmin.value) return true
  if (isNationalAdmin.value) {
    if (u.provider_level === 'level_0' || u.provider_level === 'level_1') return false
    return auth.user.admin_scope_country === u.country
  }
  if (isRegionalAdmin.value) {
    if (
      u.provider_level === 'level_0' ||
      u.provider_level === 'level_1' ||
      u.provider_level === 'level_2'
    ) return false
    return (
      auth.user.admin_scope_country === u.country &&
      auth.user.admin_scope_region === u.region
    )
  }
  return false
}

onMounted(async () => {
  if (!auth.user) await auth.fetchMe()
  await load()
})
</script>

<template>
  <div class="admin-page">
    <div class="top-bar">
      <button class="back-btn" @click="router.push('/profile')">←</button>
      <h1 class="title-gold page-title">{{ i18n.t('admin_users_title') }}</h1>
    </div>

    <p v-if="!isAdmin" class="notice notice-error">
      {{ i18n.t('admin_no_access') }}
    </p>

    <template v-else>
      <!-- scope banner -->
      <div class="scope-banner">
        <template v-if="isSystemAdmin">
          {{ i18n.t('admin_scope_global') }}
        </template>
        <template v-else-if="isNationalAdmin">
          {{ i18n.t('admin_scope_country') }}:
          <strong>{{ auth.user?.admin_scope_country || '—' }}</strong>
        </template>
        <template v-else-if="isRegionalAdmin">
          {{ i18n.t('admin_scope_region') }}:
          <strong>
            {{ auth.user?.admin_scope_country || '—' }} /
            {{ auth.user?.admin_scope_region || '—' }}
          </strong>
        </template>
      </div>

      <!-- filters -->
      <div class="filters">
        <input
          v-model="search"
          type="text"
          :placeholder="i18n.t('admin_search_placeholder')"
          @keyup.enter="page = 1; load()"
        />
        <select v-model="onlyFrozen" @change="page = 1; load()">
          <option :value="null">{{ i18n.t('admin_all_accounts') }}</option>
          <option :value="true">{{ i18n.t('admin_only_frozen') }}</option>
          <option :value="false">{{ i18n.t('admin_only_active') }}</option>
        </select>
        <button class="btn btn-primary" @click="page = 1; load()">
          {{ i18n.t('search') }}
        </button>
      </div>

      <div v-if="actionMessage" class="notice notice-ok">{{ actionMessage }}</div>
      <div v-if="actionError" class="notice notice-error">{{ actionError }}</div>

      <!-- table -->
      <div class="table-wrap">
        <table class="user-table">
          <thead>
            <tr>
              <th>#</th>
              <th>User ID</th>
              <th>Email</th>
              <th>Name</th>
              <th>Country</th>
              <th>Region</th>
              <th>Role</th>
              <th>Level</th>
              <th>Status</th>
              <th>{{ i18n.t('admin_actions') }}</th>
            </tr>
          </thead>
          <tbody>
            <tr v-if="loading">
              <td colspan="10" class="empty-cell">{{ i18n.t('loading') || 'Loading…' }}</td>
            </tr>
            <tr v-else-if="users.length === 0">
              <td colspan="10" class="empty-cell">{{ i18n.t('admin_no_users') }}</td>
            </tr>
            <tr v-for="(u, idx) in users" :key="u.id" :class="{ frozen: u.is_frozen }">
              <td>{{ (page - 1) * pageSize + idx + 1 }}</td>
              <td class="mono">@{{ u.user_id }}</td>
              <td class="mono">{{ u.email }}</td>
              <td>
                {{ [u.first_name, u.last_name].filter(Boolean).join(' ') || '—' }}
              </td>
              <td>{{ u.country || '—' }}</td>
              <td>{{ u.region || '—' }}</td>
              <td>{{ u.role }}</td>
              <td>
                <span v-if="u.provider_level" class="level-badge">
                  {{ levelLabel(u.provider_level) }}
                </span>
                <span v-else>—</span>
              </td>
              <td>
                <span v-if="u.is_frozen" class="status-badge frozen">
                  {{ i18n.t('admin_status_frozen') }}
                </span>
                <span v-else class="status-badge active">
                  {{ i18n.t('admin_status_active') }}
                </span>
              </td>
              <td class="action-cell">
                <template v-if="canAct(u)">
                  <button
                    v-if="!u.is_frozen"
                    class="mini-btn freeze"
                    @click="freezeUser(u)"
                  >
                    {{ i18n.t('admin_freeze') }}
                  </button>
                  <button
                    v-else
                    class="mini-btn unfreeze"
                    @click="unfreezeUser(u)"
                  >
                    {{ i18n.t('admin_unfreeze') }}
                  </button>
                  <button class="mini-btn delete" @click="deleteUser(u)">
                    {{ i18n.t('admin_delete') }}
                  </button>
                </template>
                <span v-else class="no-action">—</span>
              </td>
            </tr>
          </tbody>
        </table>
      </div>

      <!-- pagination -->
      <div class="pager">
        <button
          class="page-btn"
          :disabled="page <= 1"
          @click="goPage(page - 1)"
        >‹</button>
        <span class="page-info">
          {{ page }} / {{ totalPages }} · {{ total }} {{ i18n.t('admin_total_users') }}
        </span>
        <button
          class="page-btn"
          :disabled="page >= totalPages"
          @click="goPage(page + 1)"
        >›</button>
      </div>
    </template>
  </div>
</template>

<style scoped>
.admin-page {
  width: 100%;
  max-width: 1200px;
  padding: 1rem 1.25rem 3rem;
}
.top-bar {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  margin-bottom: 1rem;
}
.back-btn {
  background: transparent;
  border: 1px solid var(--border);
  color: var(--text);
  padding: 0.35rem 0.75rem;
  border-radius: 6px;
  cursor: pointer;
}
.page-title {
  margin: 0;
  font-size: 1.4rem;
}
.scope-banner {
  background: rgba(229, 184, 11, 0.1);
  border: 1px solid rgba(229, 184, 11, 0.35);
  color: var(--gold);
  padding: 0.6rem 1rem;
  border-radius: 8px;
  margin-bottom: 1rem;
  font-size: 0.88rem;
}
.scope-banner strong {
  color: #fff;
}
.filters {
  display: flex;
  gap: 0.5rem;
  margin-bottom: 1rem;
  flex-wrap: wrap;
}
.filters input {
  flex: 1 1 240px;
  margin: 0;
}
.filters select {
  flex: 0 0 180px;
  margin: 0;
}

.table-wrap {
  overflow-x: auto;
  border: 1px solid var(--border);
  border-radius: 8px;
  background: var(--bg-soft);
}
.user-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 0.82rem;
}
.user-table th,
.user-table td {
  padding: 0.55rem 0.7rem;
  text-align: left;
  border-bottom: 1px solid #2f2f2f;
  white-space: nowrap;
}
.user-table th {
  background: #171717;
  color: var(--gold);
  font-weight: 700;
  position: sticky;
  top: 0;
}
.user-table tr.frozen td {
  background: rgba(231, 76, 60, 0.06);
}
.user-table .mono {
  font-family: ui-monospace, SFMono-Regular, Menlo, monospace;
  color: #ddd;
}
.empty-cell {
  text-align: center;
  color: var(--text-dim);
  padding: 2rem 1rem;
}
.level-badge {
  display: inline-block;
  padding: 0.1rem 0.45rem;
  border-radius: 4px;
  background: rgba(229, 184, 11, 0.18);
  color: var(--gold);
  font-size: 0.72rem;
}
.status-badge {
  display: inline-block;
  padding: 0.1rem 0.5rem;
  border-radius: 4px;
  font-size: 0.72rem;
  font-weight: 600;
}
.status-badge.active {
  background: rgba(46, 204, 113, 0.16);
  color: #4ade80;
}
.status-badge.frozen {
  background: rgba(231, 76, 60, 0.18);
  color: #ff8a80;
}
.action-cell {
  display: flex;
  gap: 0.35rem;
}
.mini-btn {
  padding: 0.25rem 0.55rem;
  border-radius: 4px;
  font-size: 0.72rem;
  cursor: pointer;
  border: 1px solid transparent;
  transition: all 0.15s;
}
.mini-btn.freeze {
  background: rgba(231, 76, 60, 0.15);
  color: #ff8a80;
  border-color: rgba(231, 76, 60, 0.4);
}
.mini-btn.freeze:hover {
  background: rgba(231, 76, 60, 0.3);
}
.mini-btn.unfreeze {
  background: rgba(46, 204, 113, 0.15);
  color: #4ade80;
  border-color: rgba(46, 204, 113, 0.4);
}
.mini-btn.unfreeze:hover {
  background: rgba(46, 204, 113, 0.3);
}
.mini-btn.delete {
  background: transparent;
  color: #ff8a80;
  border-color: rgba(231, 76, 60, 0.4);
}
.mini-btn.delete:hover {
  background: rgba(231, 76, 60, 0.2);
}
.no-action {
  color: var(--text-dim);
}
.pager {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 1rem;
  margin-top: 1rem;
}
.page-btn {
  background: transparent;
  border: 1px solid var(--border);
  color: var(--text);
  width: 32px;
  height: 32px;
  border-radius: 6px;
  cursor: pointer;
  font-size: 1.1rem;
}
.page-btn:hover:not(:disabled) {
  border-color: var(--gold);
  color: var(--gold);
}
.page-btn:disabled {
  opacity: 0.35;
  cursor: not-allowed;
}
.page-info {
  color: var(--text-dim);
  font-size: 0.85rem;
}
.notice {
  padding: 0.75rem 1rem;
  border-radius: 6px;
  margin: 1rem 0;
  font-size: 0.9rem;
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
</style>