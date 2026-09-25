<script setup lang="ts">
import { ref, computed, onMounted, reactive } from 'vue'
import { useRouter } from 'vue-router'
import { api } from '@/api/client'
import { useI18nStore } from '@/stores/i18n'
import { useAuthStore } from '@/stores/auth'

const i18n = useI18nStore()
const auth = useAuthStore()
const router = useRouter()

interface AdminRow {
  id: string
  email: string
  user_id: string
  role: 'provider' | 'consumer' | null
  first_name: string | null
  last_name: string | null
  provider_level: string | null
  country: string | null
  region: string | null
  admin_scope_country: string | null
  admin_scope_region: string | null
  is_frozen: boolean
  is_active: boolean
  created_at: string | null
  customer_level?: number
}

interface AdminMe {
  id: string
  user_id: string
  email: string
  provider_level: string
  admin_scope_country: string | null
  admin_scope_region: string | null
  customer_level?: number
  can_create: string[]
  can_manage_levels: string[]
}

const me = ref<AdminMe | null>(null)
const rows = ref<AdminRow[]>([])
const total = ref(0)
const page = ref(1)
const pageSize = 20
const search = ref('')
const frozenFilter = ref<boolean | null>(null)
const loading = ref(false)
const actionMessage = ref('')
const actionError = ref('')

const showCreate = ref(false)
const creating = ref(false)
const createError = ref('')
const createForm = reactive({
  email: '',
  password: '',
  user_id: '',
  first_name: '',
  last_name: '',
  provider_level: 'level_2',
  admin_scope_country: '',
  admin_scope_region: '',
})

const showChangeEmail = ref(false)
const changingEmail = ref(false)
const changeEmailError = ref('')
const changeEmailSuccess = ref('')
const newEmail = ref('')
const confirmPassword = ref('')

const EMAIL_REGEX = /^[^\s@]+@[^\s@]+\.[^\s@]+$/

const totalPages = computed(() => Math.max(1, Math.ceil(total.value / pageSize)))
const isSystemAdmin = computed(() => me.value?.provider_level === 'level_0')
const isNationalAdmin = computed(() => me.value?.provider_level === 'level_1')
const isRegionalAdmin = computed(() => me.value?.provider_level === 'level_2')
const canCreate = computed(() => (me.value?.can_create || []).length > 0)
const createLevelOptions = computed(() => me.value?.can_create || [])

const showScopeCountry = computed(() => {
  if (createForm.provider_level === 'level_1') return true
  if (createForm.provider_level === 'level_2' && isSystemAdmin.value) return true
  return false
})
const showScopeRegion = computed(() => {
  if (createForm.provider_level === 'level_2') return true
  return false
})
const scopeCountryReadonly = computed(
  () => isNationalAdmin.value && createForm.provider_level === 'level_2',
)

const computedCustomerLevel = computed<number>(() => {
  switch (createForm.provider_level) {
    case 'level_0': return 9
    case 'level_1': return 2
    case 'level_2': return 1
    case 'level_3': return 3
    default: return 0
  }
})

async function loadMe() {
  const { data } = await api.get('/api/admin/me')
  me.value = data
}

async function loadUsers() {
  loading.value = true
  try {
    const params: Record<string, unknown> = {
      page: page.value,
      page_size: pageSize,
    }
    if (search.value.trim()) params.q = search.value.trim()
    if (frozenFilter.value === true) params.only_frozen = true
    else if (frozenFilter.value === false) params.only_frozen = false

    const { data } = await api.get('/api/admin/users', { params })
    rows.value = data.users
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
  loadUsers()
}

function isConsumerRow(u: AdminRow): boolean {
  if (u.provider_level) return false
  if (u.role === 'consumer') return true
  return !u.role
}

function levelLabel(lvl: string | null): string {
  if (!lvl) return '—'
  const key = `level_${lvl.replace('level_', '')}`
  return (i18n.t && i18n.t(key)) || lvl
}

function displayCountry(u: AdminRow): string {
  return (u.country ?? u.admin_scope_country ?? '') || '—'
}

function displayRegion(u: AdminRow): string {
  return (u.region ?? u.admin_scope_region ?? '') || '—'
}

async function freezeUser(u: AdminRow) {
  if (!confirm(`${i18n.t('admin_confirm_freeze')} @${u.user_id}?`)) return
  actionMessage.value = ''
  actionError.value = ''
  try {
    await api.post(`/api/admin/users/${u.id}/freeze`)
    actionMessage.value = `${i18n.t('admin_frozen')} @${u.user_id}`
    await loadUsers()
  } catch (e: any) {
    actionError.value = e?.response?.data?.detail || i18n.t('admin_action_failed')
  }
}

async function unfreezeUser(u: AdminRow) {
  actionMessage.value = ''
  actionError.value = ''
  try {
    await api.post(`/api/admin/users/${u.id}/unfreeze`)
    actionMessage.value = `${i18n.t('admin_unfrozen')} @${u.user_id}`
    await loadUsers()
  } catch (e: any) {
    actionError.value = e?.response?.data?.detail || i18n.t('admin_action_failed')
  }
}

async function deleteUser(u: AdminRow) {
  const confirmed = confirm(
    `${i18n.t('admin_confirm_delete')} @${u.user_id} (${u.email})?\n\n${i18n.t('admin_delete_warning')}`,
  )
  if (!confirmed) return
  actionMessage.value = ''
  actionError.value = ''
  try {
    await api.delete(`/api/admin/users/${u.id}`)
    actionMessage.value = `${i18n.t('admin_deleted')} @${u.user_id}`
    await loadUsers()
  } catch (e: any) {
    actionError.value = e?.response?.data?.detail || i18n.t('admin_action_failed')
  }
}

function openCreate() {
  createError.value = ''
  createForm.email = ''
  createForm.password = ''
  createForm.user_id = ''
  createForm.first_name = ''
  createForm.last_name = ''
  createForm.provider_level = createLevelOptions.value[0] || 'level_2'
  createForm.admin_scope_country = isNationalAdmin.value
    ? me.value?.admin_scope_country || ''
    : ''
  createForm.admin_scope_region = ''
  showCreate.value = true
}

async function submitCreate() {
  createError.value = ''
  if (!createForm.email || !createForm.password || !createForm.user_id) {
    createError.value = i18n.t('please_fill_required')
    return
  }
  if (createForm.password.length < 8) {
    createError.value = i18n.t('password_too_short')
    return
  }

  const payload: Record<string, unknown> = {
    email: createForm.email,
    password: createForm.password,
    user_id: createForm.user_id,
    first_name: createForm.first_name || null,
    last_name: createForm.last_name || null,
    provider_level: createForm.provider_level,
  }
  if (showScopeCountry.value) {
    payload.admin_scope_country = createForm.admin_scope_country || null
  }
  if (showScopeRegion.value) {
    payload.admin_scope_region = createForm.admin_scope_region || null
  }

  creating.value = true
  try {
    await api.post('/api/admin/users', payload)
    showCreate.value = false
    actionMessage.value = i18n.t('admin_created')
    await loadUsers()
  } catch (e: any) {
    createError.value = e?.response?.data?.detail || i18n.t('admin_create_failed')
  } finally {
    creating.value = false
  }
}

function openChangeEmail() {
  changeEmailError.value = ''
  changeEmailSuccess.value = ''
  newEmail.value = ''
  confirmPassword.value = ''
  showChangeEmail.value = true
}

async function submitChangeEmail() {
  changeEmailError.value = ''
  changeEmailSuccess.value = ''

  const trimmed = newEmail.value.trim()

  if (!trimmed) {
    changeEmailError.value = i18n.t('please_fill_required')
    return
  }
  if (!EMAIL_REGEX.test(trimmed)) {
    changeEmailError.value = i18n.t('email_format_invalid')
    return
  }
  if (!confirmPassword.value) {
    changeEmailError.value = i18n.t('password_required')
    return
  }

  changingEmail.value = true
  try {
    const { data } = await api.post('/api/auth/change-email', {
      new_email: trimmed,
      password: confirmPassword.value,
    })
    changeEmailSuccess.value = i18n.t('change_email_success')
    if (me.value) me.value.email = data.email
    await auth.fetchMe()
    setTimeout(() => {
      showChangeEmail.value = false
    }, 2000)
  } catch (e: any) {
    changeEmailError.value =
      e?.response?.data?.detail || i18n.t('change_email_failed')
  } finally {
    changingEmail.value = false
  }
}

// ★ 保留函数，模板中已移除按钮
function logout() {
  auth.logout()
  router.push('/admin/login')
}

function goUserPages() {
  router.push('/profile')
}

onMounted(async () => {
  if (!auth.token) {
    router.push('/admin/login')
    return
  }
  try {
    await loadMe()
    await loadUsers()
  } catch {
    router.push('/admin/login')
  }
})
</script>

<template>
  <div class="admin-page">
    <div class="top-bar">
      <button class="back-btn" @click="router.push('/')">←</button>
      <h1 class="title-gold page-title">🛡️ {{ i18n.t('admin_portal') }}</h1>
      <div class="spacer" />
      <div v-if="me" class="me-info">
        <span class="me-name">@{{ me.user_id }}</span>
        <span class="me-level">{{ levelLabel(me.provider_level) }}</span>
        <span class="me-scope">
          {{
            me.provider_level === 'level_0'
              ? i18n.t('admin_scope_global_short')
              : me.provider_level === 'level_1'
              ? `${me.admin_scope_country || '—'}`
              : `${me.admin_scope_country || '—'} / ${me.admin_scope_region || '—'}`
          }}
        </span>
        <span v-if="me.customer_level !== undefined" class="me-customer-level">
          Lv.{{ me.customer_level }}
        </span>
      </div>

      <button
        v-if="isSystemAdmin"
        class="btn btn-outline top-btn"
        @click="openChangeEmail"
      >
        ✉️ {{ i18n.t('change_email') }}
      </button>

      <!-- ★ User Pages：背景改为纯深色 -->
      <button class="btn top-btn bg-dark-btn" @click="goUserPages">
        👤 {{ i18n.t('back_to_user_pages') }}
      </button>

      <!-- ★ 已移除 Logout 按钮 -->
    </div>

    <div class="filters">
      <input
        v-model="search"
        type="text"
        :placeholder="i18n.t('admin_search_placeholder')"
        @keyup.enter="page = 1; loadUsers()"
      />
      <select v-model="frozenFilter" @change="page = 1; loadUsers()">
        <option :value="null">{{ i18n.t('admin_all_accounts') }}</option>
        <option :value="true">{{ i18n.t('admin_only_frozen') }}</option>
        <option :value="false">{{ i18n.t('admin_only_active') }}</option>
      </select>
      <!-- ★ Search：背景改为纯深色 -->
      <button class="btn bg-dark-btn" @click="page = 1; loadUsers()">
        {{ i18n.t('search') }}
      </button>
      <button v-if="canCreate" class="btn btn-primary" @click="openCreate">
        + {{ i18n.t('admin_create') }}
      </button>
    </div>

    <div class="notice-slot">
      <div v-if="actionMessage" class="notice notice-ok">{{ actionMessage }}</div>
      <div v-else-if="actionError" class="notice notice-error">{{ actionError }}</div>
    </div>

    <div class="table-wrap">
      <div v-if="loading" class="table-loading-overlay">
        <span>Loading…</span>
      </div>
      <table class="user-table">
        <thead>
          <tr>
            <th>#</th>
            <th>User ID</th>
            <th>Email</th>
            <th>Name</th>
            <th>{{ i18n.t('provider_level') }}</th>
            <th>{{ i18n.t('customer_level') }}</th>
            <th>{{ i18n.t('admin_scope_country') }}</th>
            <th>{{ i18n.t('admin_scope_region') }}</th>
            <th>{{ i18n.t('admin_status') }}</th>
            <th>{{ i18n.t('admin_actions') }}</th>
          </tr>
        </thead>
        <tbody>
          <tr v-if="!loading && rows.length === 0">
            <td colspan="10" class="empty-cell">{{ i18n.t('admin_no_users') }}</td>
          </tr>
          <tr
            v-for="(u, idx) in rows"
            :key="u.id"
            :class="{ frozen: u.is_frozen }"
          >
            <td>{{ (page - 1) * pageSize + idx + 1 }}</td>
            <td class="mono">@{{ u.user_id }}</td>
            <td class="mono">{{ u.email }}</td>
            <td>{{ [u.first_name, u.last_name].filter(Boolean).join(' ') || '—' }}</td>
            <td>
              <span v-if="u.provider_level" class="level-badge">
                {{ levelLabel(u.provider_level) }}
              </span>
              <span v-else-if="isConsumerRow(u)" class="level-badge consumer">
                Consumer
              </span>
              <span v-else>—</span>
            </td>
            <td>
              <span class="level-badge customer-lv">
                Lv.{{ u.customer_level ?? 0 }}
              </span>
            </td>
            <td>{{ displayCountry(u) }}</td>
            <td>{{ displayRegion(u) }}</td>
            <td>
              <span v-if="u.is_frozen" class="status-badge frozen">
                {{ i18n.t('admin_status_frozen') }}
              </span>
              <span v-else class="status-badge active">
                {{ i18n.t('admin_status_active') }}
              </span>
            </td>
            <td class="action-cell">
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
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <div class="pager">
      <button class="page-btn" :disabled="page <= 1" @click="goPage(page - 1)">‹</button>
      <span class="page-info">
        {{ page }} / {{ totalPages }} · {{ total }} {{ i18n.t('admin_total_users') }}
      </span>
      <button
        class="page-btn"
        :disabled="page >= totalPages"
        @click="goPage(page + 1)"
      >
        ›
      </button>
    </div>

    <!-- ============ create dialog ============ -->
    <div v-if="showCreate" class="modal-overlay">
      <div class="modal-card">
        <h3 class="modal-title">{{ i18n.t('admin_create') }}</h3>

        <div v-if="createError" class="notice notice-error">{{ createError }}</div>

        <label>{{ i18n.t('email') }} *</label>
        <input v-model="createForm.email" type="email" />

        <label>{{ i18n.t('password') }} *</label>
        <input v-model="createForm.password" type="password" />

        <label>{{ i18n.t('user_id') }} *</label>
        <input v-model="createForm.user_id" type="text" />

        <label>{{ i18n.t('first_name') }}</label>
        <input v-model="createForm.first_name" type="text" />

        <label>{{ i18n.t('last_name') }}</label>
        <input v-model="createForm.last_name" type="text" />

        <label>{{ i18n.t('provider_level') }} *</label>
        <select v-model="createForm.provider_level">
          <option v-for="lvl in createLevelOptions" :key="lvl" :value="lvl">
            {{ levelLabel(lvl) }}
          </option>
        </select>

        <label>{{ i18n.t('customer_level') }}</label>
        <input
          :value="computedCustomerLevel"
          type="number"
          readonly
          class="readonly-input"
        />

        <template v-if="showScopeCountry">
          <label>{{ i18n.t('admin_scope_country') }} *</label>
          <input
            v-model="createForm.admin_scope_country"
            type="text"
            placeholder="e.g. CN"
            :readonly="scopeCountryReadonly"
          />
        </template>

        <template v-if="showScopeRegion">
          <label>{{ i18n.t('admin_scope_region') }} *</label>
          <input
            v-model="createForm.admin_scope_region"
            type="text"
            placeholder="e.g. Shanghai"
          />
        </template>

        <div class="modal-actions">
          <button
            class="btn btn-primary modal-btn"
            :disabled="creating"
            @click="submitCreate"
          >
            {{ creating ? '…' : i18n.t('admin_create') }}
          </button>
          <button class="btn btn-outline modal-btn" @click="showCreate = false">
            {{ i18n.t('cancel') }}
          </button>
        </div>
      </div>
    </div>

    <!-- ============ change email dialog ============ -->
    <div v-if="showChangeEmail" class="modal-overlay">
      <div class="modal-card">
        <h3 class="modal-title">{{ i18n.t('change_email') }}</h3>

        <div v-if="changeEmailError" class="notice notice-error">
          {{ changeEmailError }}
        </div>
        <div v-if="changeEmailSuccess" class="notice notice-ok">
          {{ changeEmailSuccess }}
        </div>

        <label>{{ i18n.t('current_email') }}</label>
        <input :value="me?.email || ''" type="email" readonly />

        <label>{{ i18n.t('new_email') }} *</label>
        <input
          v-model="newEmail"
          type="email"
          autocomplete="email"
          :placeholder="i18n.t('new_email_placeholder')"
        />

        <label>{{ i18n.t('confirm_password') }} *</label>
        <input
          v-model="confirmPassword"
          type="password"
          autocomplete="current-password"
        />

        <div class="modal-actions">
          <button
            class="btn btn-primary modal-btn"
            :disabled="changingEmail"
            @click="submitChangeEmail"
          >
            {{ changingEmail ? '…' : i18n.t('submit_change') }}
          </button>
          <button
            class="btn btn-outline modal-btn"
            @click="showChangeEmail = false"
          >
            {{ i18n.t('cancel') }}
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.admin-page {
  width: 100%;
  max-width: 1280px;
  padding: 1rem 1.25rem 3rem;
  margin: 0 auto;
}

.level-badge.consumer {
  background: rgba(120, 144, 156, 0.2);
  color: #b0bec5;
}
.level-badge.customer-lv {
  background: rgba(46, 204, 113, 0.15);
  color: #4ade80;
}

.top-bar {
  display: flex;
  align-items: center;
  gap: 0.6rem;
  margin-bottom: 1rem;
  flex-wrap: wrap;
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
  font-size: 1.3rem;
}
.spacer { flex: 1; }
.me-info {
  display: flex;
  gap: 0.75rem;
  align-items: center;
  font-size: 0.82rem;
  color: var(--text-dim);
  flex-wrap: wrap;
}
.me-name { color: var(--gold); font-weight: 600; }
.me-level {
  background: rgba(229, 184, 11, 0.15);
  color: var(--gold);
  padding: 0.1rem 0.5rem;
  border-radius: 4px;
  font-size: 0.75rem;
}
.me-customer-level {
  background: rgba(46, 204, 113, 0.15);
  color: #4ade80;
  padding: 0.1rem 0.5rem;
  border-radius: 4px;
  font-size: 0.75rem;
}
.me-scope {
  font-family: ui-monospace, monospace;
  font-size: 0.75rem;
}
.top-btn {
  padding: 0.35rem 0.85rem;
  font-size: 0.82rem;
}

/* ★ User Pages / Search 按钮：纯深色背景 */
.bg-dark-btn {
  background: rgba(32, 32, 32, 1.0);
  color: var(--text);
  border: 1px solid var(--border);
}
.bg-dark-btn:hover {
  background: rgba(50, 50, 50, 1.0);
  border-color: var(--gold);
  color: var(--gold);
}

.filters {
  display: flex;
  gap: 0.5rem;
  margin-bottom: 1rem;
  flex-wrap: wrap;
  align-items: center;
}
.filters input { flex: 1 1 240px; margin: 0; }
.filters select { flex: 0 0 180px; margin: 0; }

.notice-slot { min-height: 3.2rem; }

.table-wrap {
  position: relative;
  overflow-x: auto;
  border: 1px solid var(--border);
  border-radius: 8px;
  background: var(--bg-soft);
  min-height: 220px;
}
.table-loading-overlay {
  position: absolute;
  inset: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  background: rgba(0, 0, 0, 0.35);
  color: var(--text-dim);
  font-size: 0.9rem;
  z-index: 5;
  pointer-events: none;
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
.action-cell { display: flex; gap: 0.35rem; }
.mini-btn {
  padding: 0.25rem 0.55rem;
  border-radius: 4px;
  font-size: 0.72rem;
  cursor: pointer;
  border: 1px solid transparent;
}
.mini-btn.freeze {
  background: rgba(231, 76, 60, 0.15);
  color: #ff8a80;
  border-color: rgba(231, 76, 60, 0.4);
}
.mini-btn.freeze:hover { background: rgba(231, 76, 60, 0.3); }
.mini-btn.unfreeze {
  background: rgba(46, 204, 113, 0.15);
  color: #4ade80;
  border-color: rgba(46, 204, 113, 0.4);
}
.mini-btn.unfreeze:hover { background: rgba(46, 204, 113, 0.3); }
.mini-btn.delete {
  background: transparent;
  color: #ff8a80;
  border-color: rgba(231, 76, 60, 0.4);
}
.mini-btn.delete:hover { background: rgba(231, 76, 60, 0.2); }

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
.page-btn:disabled { opacity: 0.35; cursor: not-allowed; }
.page-info { color: var(--text-dim); font-size: 0.85rem; }

.modal-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.65);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 2000;
  padding: 1rem;
}
.modal-card {
  background: #2a2a2a;
  border: 1px solid var(--border);
  border-radius: 12px;
  padding: 1.5rem;
  max-width: 480px;
  width: 100%;
  max-height: 90vh;
  overflow-y: auto;
  box-shadow: 0 12px 40px rgba(0, 0, 0, 0.7);
}
.modal-title {
  color: var(--gold);
  margin: 0 0 1rem;
  font-size: 1.15rem;
  text-align: center;
}
.modal-actions {
  display: flex;
  gap: 0.75rem;
  margin-top: 1.25rem;
}
.modal-btn {
  flex: 1 1 0;
  padding: 0.6rem 1rem;
  font-size: 0.9rem;
}

.readonly-input {
  background: rgba(255, 255, 255, 0.04);
  color: var(--text-dim);
  cursor: not-allowed;
}

.notice {
  padding: 0.7rem 1rem;
  border-radius: 6px;
  margin: 0;
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
</style>