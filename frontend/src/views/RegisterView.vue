<script setup lang="ts">
import { ref, reactive, computed, onMounted, watch } from 'vue'
import { useRouter } from 'vue-router'
import { AxiosError } from 'axios'
import { useI18nStore } from '@/stores/i18n'
import { api } from '@/api/client'
import { COUNTRIES } from '@/data/countries'
import { getRegionsByCountry } from '@/data/regions'
// ★ 新增：引入通用分类 COMBOX 组件
import CategorySelect from '@/components/CategorySelect.vue'

const i18n = useI18nStore()
const router = useRouter()

type Role = 'provider' | 'consumer'
type Category =
  | 'medical' | 'health' | 'education' | 'entertainment' | 'travel'
  | 'food' | 'clothing' | 'industry' | 'tech' | 'iot' | 'life' | 'ai'

const currentYear = new Date().getFullYear()
const BIRTH_YEARS = Array.from({ length: 91 }, (_, i) => currentYear - 10 - i)
const DEFAULT_BIRTH_YEAR = currentYear - 20

// ★ 注册时所有新用户的客户等级固定为 0（后续根据行为升级）
const NEW_USER_CUSTOMER_LEVEL = 0

const form = reactive({
  role: 'consumer' as Role,
  user_id: '',
  email: '',
  gender: '',
  birth_year: DEFAULT_BIRTH_YEAR,
  country: '',
  region: '',
  password: '',
  password_confirm: '',
  service_category: null as Category | null,
  phone_dial: '+86',
  phone_number: '',
  first_name: '',
  last_name: '',
})

const error = ref('')
const success = ref('')
const loading = ref(false)
const checking = ref(false)

const userIdAvailable = ref<boolean | null>(null)
const emailAvailable = ref<boolean | null>(null)

const computedAge = computed(() => {
  if (!form.birth_year) return null
  return currentYear - form.birth_year
})

const passwordsMatch = computed(
  () => !form.password_confirm || form.password === form.password_confirm,
)

const availableRegions = computed(() => getRegionsByCountry(form.country))

watch(
  () => form.country,
  (code) => {
    const list = getRegionsByCountry(code)
    form.region = list.length === 1 ? list[0] : ''
  },
)

function close() {
  router.push('/')
}

let debounceTimer: number | null = null

async function checkAvailability() {
  if (!form.user_id && !form.email) return
  checking.value = true
  try {
    const { data } = await api.post('/api/auth/check-availability', {
      user_id: form.user_id || null,
      email: form.email || null,
    })
    userIdAvailable.value = !data.user_id_taken
    emailAvailable.value = !data.email_taken
  } catch {
    userIdAvailable.value = null
    emailAvailable.value = null
  } finally {
    checking.value = false
  }
}

watch(
  () => [form.user_id, form.email],
  () => {
    if (debounceTimer) window.clearTimeout(debounceTimer)
    debounceTimer = window.setTimeout(checkAvailability, 500)
  },
)

onMounted(async () => {
  // ★ 恢复上次选择的分类（如果表单里还没有值）
  const saved = localStorage.getItem('fdq95_register_category')
  if (saved && !form.service_category) {
    form.service_category = saved as Category
  }

  try {
    const resp = await fetch('https://ipapi.co/json/', { cache: 'no-store' })
    if (!resp.ok) return
    const data = await resp.json()
    const code = (data?.country_code || '').toUpperCase()
    if (code && COUNTRIES.some((c) => c.code === code)) {
      form.country = code
      const match = COUNTRIES.find((c) => c.code === code)
      if (match) form.phone_dial = match.dial
    }
  } catch { /* offline */ }
})

async function submit() {
  error.value = ''
  success.value = ''

  if (!form.email || !form.password || !form.user_id) {
    error.value = i18n.t('please_fill_required')
    return
  }
  if (form.password !== form.password_confirm) {
    error.value = i18n.t('passwords_do_not_match')
    return
  }
  if (form.password.length < 8) {
    error.value = i18n.t('password_too_short')
    return
  }
  if (!form.service_category) {
    error.value = i18n.t('please_pick_one_category')
    return
  }
  if (!form.region) {
    error.value = i18n.t('please_select_region')
    return
  }
  if (userIdAvailable.value === false) {
    error.value = i18n.t('user_id_taken')
    return
  }
  if (emailAvailable.value === false) {
    error.value = i18n.t('email_taken')
    return
  }

  const payload: Record<string, unknown> = {
    email: form.email,
    password: form.password,
    user_id: form.user_id,
    gender: form.gender || null,
    age: computedAge.value,
    country: form.country || null,
    region: form.region || null,
    role: form.role,
    service_category: form.service_category,
    first_name: form.first_name || null,
    last_name: form.last_name || null,
    customer_level: NEW_USER_CUSTOMER_LEVEL,
  }
  if (form.role === 'provider') {
    const phone = form.phone_number
      ? `${form.phone_dial} ${form.phone_number}`.trim()
      : null
    payload.phone = phone
    payload.provider_level = 'level_4'
  }

  loading.value = true
  try {
    await api.post('/auth/register', payload)
    success.value = i18n.t('register_success_verify_email')
    setTimeout(() => router.push('/login'), 2500)
  } catch (e) {
    const ax = e as AxiosError<{ detail?: unknown }>
    let msg = i18n.t('register_failed')
    if (ax.response?.data?.detail) {
      const d = ax.response.data.detail
      msg = typeof d === 'string' ? d : JSON.stringify(d)
    }
    error.value = msg
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <div class="card register-card">
    <button class="close-btn" aria-label="Close" @click="close">×</button>
    <h2 class="title-gold card-title">{{ i18n.t('register') }}</h2>

    <div v-if="error" class="notice notice-error">{{ error }}</div>
    <div v-if="success" class="notice notice-ok">{{ success }}</div>

    <label>{{ i18n.t('account_type') }}</label>
    <select v-model="form.role">
      <option value="consumer">{{ i18n.t('consumer') }}</option>
      <option value="provider">{{ i18n.t('provider') }}</option>
    </select>

    <label>{{ i18n.t('first_name') }}</label>
    <input v-model="form.first_name" type="text" autocomplete="given-name" />

    <label>{{ i18n.t('last_name') }}</label>
    <input v-model="form.last_name" type="text" autocomplete="family-name" />

    <label>{{ i18n.t('user_id') }} *</label>
    <input v-model="form.user_id" type="text" />
    <p
      class="field-hint"
      :class="{ ok: userIdAvailable === true, err: userIdAvailable === false }"
    >
      <template v-if="checking && form.user_id">… {{ i18n.t('checking') }}</template>
      <template v-else-if="form.user_id && userIdAvailable === false">
        ✗ {{ i18n.t('user_id_taken') }}
      </template>
      <template v-else-if="form.user_id && userIdAvailable === true">
        ✓ {{ i18n.t('available') }}
      </template>
      <template v-else>&nbsp;</template>
    </p>

    <label>{{ i18n.t('email') }} *</label>
    <input v-model="form.email" type="email" autocomplete="email" />
    <p
      class="field-hint"
      :class="{ ok: emailAvailable === true, err: emailAvailable === false }"
    >
      <template v-if="checking && form.email">… {{ i18n.t('checking') }}</template>
      <template v-else-if="form.email && emailAvailable === false">
        ✗ {{ i18n.t('email_taken') }}
      </template>
      <template v-else-if="form.email && emailAvailable === true">
        ✓ {{ i18n.t('available') }}
      </template>
      <template v-else>&nbsp;</template>
    </p>

    <label>{{ i18n.t('gender') }}</label>
    <select v-model="form.gender">
      <option value="">--</option>
      <option value="male">{{ i18n.t('male') }}</option>
      <option value="female">{{ i18n.t('female') }}</option>
      <option value="other">{{ i18n.t('other') }}</option>
    </select>

    <label>{{ i18n.t('birth_year') }}</label>
    <select v-model.number="form.birth_year">
      <option v-for="y in BIRTH_YEARS" :key="y" :value="y">{{ y }}</option>
    </select>

    <label>{{ i18n.t('country') }}</label>
    <select v-model="form.country">
      <option value="">--</option>
      <option v-for="c in COUNTRIES" :key="c.code" :value="c.code">
        {{ c.name }}
      </option>
    </select>

    <label>{{ i18n.t('region') }} *</label>
    <select v-model="form.region" :disabled="!form.country || availableRegions.length === 0">
      <option value="" disabled>
        {{ !form.country ? i18n.t('select_country_first') : i18n.t('select_region') }}
      </option>
      <option v-for="r in availableRegions" :key="r" :value="r">{{ r }}</option>
    </select>

    <label>{{ i18n.t('password') }} *</label>
    <input v-model="form.password" type="password" autocomplete="new-password" />

    <label>{{ i18n.t('password_confirm') }} *</label>
    <input
      v-model="form.password_confirm"
      type="password"
      autocomplete="new-password"
    />
    <p
      class="field-hint"
      :class="{ ok: passwordsMatch, err: !passwordsMatch && !!form.password_confirm }"
    >
      <template v-if="form.password_confirm">
        {{ passwordsMatch ? '✓ ' + i18n.t('passwords_match') : '✗ ' + i18n.t('passwords_do_not_match') }}
      </template>
      <template v-else>&nbsp;</template>
    </p>

    <label>{{ i18n.t('service_category') }} *</label>
    <!-- ★ 分类选择：COMBOX（搜索 + 记忆上次选择） -->
    <CategorySelect
      v-model="form.service_category"
      storage-key="fdq95_register_category"
      :placeholder="i18n.t('select_category') || '选择分类'"
    />

    <label>{{ i18n.t('customer_level') }}</label>
    <input
      :value="NEW_USER_CUSTOMER_LEVEL"
      type="number"
      readonly
      class="readonly-input"
    />
    <p class="field-hint">
      {{ i18n.t('customer_level_hint') }}
    </p>

    <template v-if="form.role === 'provider'">
      <label>{{ i18n.t('phone') }}</label>
      <div class="phone-row">
        <select v-model="form.phone_dial" class="dial-select">
          <option v-for="c in COUNTRIES" :key="c.code" :value="c.dial">
            {{ c.dial }} · {{ c.code }}
          </option>
        </select>
        <input v-model="form.phone_number" type="tel" class="phone-input" />
      </div>
    </template>

    <button
      class="btn btn-primary btn-block submit-btn"
      :disabled="loading"
      @click="submit"
    >
      {{ i18n.t('register') }}
    </button>
  </div>
</template>

<style scoped>
.register-card { position: relative; width: 100%; max-width: 680px; }
.card-title { text-align: center; margin: 0 0 1rem; }

/* ★ 只读输入框视觉 */
.readonly-input {
  background: rgba(255, 255, 255, 0.04);
  color: var(--text-dim);
  cursor: not-allowed;
}

.phone-row { display: flex; gap: 0.5rem; align-items: center; }
.dial-select { flex: 0 0 140px; margin-top: 0.25rem; }
.phone-input { flex: 1; }

.field-hint {
  min-height: 1.05rem;
  font-size: 0.78rem;
  line-height: 1.05rem;
  margin: 0.15rem 0 0;
  color: var(--text-dim);
}
.field-hint.ok  { color: #2ecc71; }
.field-hint.err { color: #e74c3c; }

.register-card input,
.register-card select,
.register-card textarea {
  transition: none !important;
}

.submit-btn { margin-top: 1.5rem; }

.close-btn {
  position: absolute; top: 0.5rem; right: 0.75rem;
  background: transparent; border: none; color: var(--text-dim);
  font-size: 1.75rem; cursor: pointer;
}
.close-btn:hover { color: var(--gold); }

@media (max-width: 480px) {
  .phone-row { flex-direction: column; align-items: stretch; }
  .dial-select { flex: 1; }
}
</style>