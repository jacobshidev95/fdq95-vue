<script setup lang="ts">
import { ref, reactive, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { AxiosError } from 'axios'
import { useI18nStore } from '@/stores/i18n'
import { api } from '@/api/client'
import { COUNTRIES } from '@/data/countries'

const i18n = useI18nStore()
const router = useRouter()

type Role = 'provider' | 'consumer'
type Category =
  | 'medical'
  | 'health'
  | 'education'
  | 'entertainment'
  | 'travel'
  | 'food'
  | 'clothing'
  | 'industry'
  | 'tech'
  | 'iot'

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
]

// --- Birth Year options: from currentYear-10 down to currentYear-100 ---
const currentYear = new Date().getFullYear()
const BIRTH_YEARS = Array.from({ length: 91 }, (_, i) => currentYear - 10 - i)
const DEFAULT_BIRTH_YEAR = currentYear - 20

const form = reactive({
  role: 'consumer' as Role,
  user_id: '',
  email: '',
  gender: '',
  birth_year: DEFAULT_BIRTH_YEAR,
  country: '',
  password: '',
  service_category: null as Category | null,
  phone_dial: '+86',
  phone_number: '',
  first_name: '',
  family_name: '',
})

const error = ref('')
const success = ref('')
const loading = ref(false)

const computedAge = computed(() => {
  if (!form.birth_year) return null
  return currentYear - form.birth_year
})

function close() {
  router.push('/')
}

function toggleCategory(cat: Category, checked: boolean) {
  form.service_category = checked ? cat : null
}

// Detect user country by IP (best-effort; silently ignore failures)
onMounted(async () => {
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
  } catch {
    /* offline or blocked — leave defaults */
  }
})

async function submit() {
  error.value = ''
  success.value = ''

  if (!form.email || !form.password || !form.user_id) {
    error.value = i18n.t('please_fill_required')
    return
  }
  if (!form.service_category) {
    error.value = i18n.t('please_pick_one_category')
    return
  }

  const payload: Record<string, unknown> = {
    email: form.email,
    password: form.password,
    user_id: form.user_id,
    gender: form.gender || null,
    age: computedAge.value,
    country: form.country || null,
    role: form.role,
    service_category: form.service_category,
  }

  if (form.role === 'provider') {
    const phone = form.phone_number
      ? `${form.phone_dial} ${form.phone_number}`.trim()
      : null
    const realName = [form.first_name, form.family_name]
      .filter((s) => s.trim())
      .join(' ')
    payload.phone = phone
    payload.real_name = realName || null
    payload.provider_level = 'level_4'
  }

  loading.value = true
  try {
    await api.post('/auth/register', payload)
    success.value = i18n.t('register_success')
    setTimeout(() => router.push('/login'), 1500)
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

    <label>{{ i18n.t('user_id') }} *</label>
    <input v-model="form.user_id" type="text" />

    <label>{{ i18n.t('email') }} *</label>
    <input v-model="form.email" type="email" autocomplete="email" />

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

    <label>{{ i18n.t('password') }} *</label>
    <input
      v-model="form.password"
      type="password"
      autocomplete="new-password"
    />

    <label>{{ i18n.t('service_category') }} *</label>
    <div class="checkbox-grid">
      <label v-for="cat in CATEGORIES" :key="cat.value" class="checkbox-item">
        <input
          type="checkbox"
          :checked="form.service_category === cat.value"
          @change="
            toggleCategory(
              cat.value,
              ($event.target as HTMLInputElement).checked
            )
          "
        />
        <span>{{ cat.key }}</span>
      </label>
    </div>

    <template v-if="form.role === 'provider'">
      <label>{{ i18n.t('phone') }}</label>
      <div class="phone-row">
        <select v-model="form.phone_dial" class="dial-select">
          <option v-for="c in COUNTRIES" :key="c.code" :value="c.dial">
            {{ c.dial }} · {{ c.code }}
          </option>
        </select>
        <input
          v-model="form.phone_number"
          type="tel"
          class="phone-input"
          inputmode="tel"
        />
      </div>

      <label>{{ i18n.t('first_name') }}</label>
      <input v-model="form.first_name" type="text" autocomplete="given-name" />

      <label>{{ i18n.t('family_name') }}</label>
      <input
        v-model="form.family_name"
        type="text"
        autocomplete="family-name"
      />
    </template>

    <button
      class="btn btn-primary btn-block submit-btn"
      :disabled="loading"
      @click="submit"
    >
      {{ i18n.t('register') }}
    </button>

    <p class="hint">
      <router-link to="/login">{{ i18n.t('login') }}</router-link>
    </p>
  </div>
</template>

<style scoped>
.register-card {
  position: relative;
  width: 100%;
  max-width: 680px;
}
.card-title {
  text-align: center;
  margin: 0 0 1rem;
}

/* 10 checkboxes → 5 columns × 2 rows */
.checkbox-grid {
  display: grid;
  grid-template-columns: repeat(5, minmax(0, 1fr));
  gap: 0.5rem 0.75rem;
  margin-top: 0.35rem;
}
.checkbox-item {
  display: inline-flex;
  align-items: center;
  gap: 0.4rem;
  margin: 0;
  color: var(--text);
  cursor: pointer;
  user-select: none;
}
.checkbox-item input {
  width: auto;
  margin: 0;
  accent-color: var(--gold);
}
.checkbox-item span {
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

/* Phone row: dial code + local number */
.phone-row {
  display: flex;
  gap: 0.5rem;
  align-items: center;
}
.dial-select {
  flex: 0 0 140px;
  margin-top: 0.25rem;
}
.phone-input {
  flex: 1;
}

.submit-btn {
  margin-top: 1.5rem;
}
.hint {
  text-align: center;
  margin-top: 1rem;
  font-size: 0.9rem;
}

.close-btn {
  position: absolute;
  top: 0.5rem;
  right: 0.75rem;
  background: transparent;
  border: none;
  color: var(--text-dim);
  font-size: 1.75rem;
  line-height: 1;
  padding: 0.15rem 0.5rem;
  cursor: pointer;
  transition: color 0.15s;
}
.close-btn:hover {
  color: var(--gold);
}

@media (max-width: 720px) {
  .checkbox-grid {
    grid-template-columns: repeat(3, minmax(0, 1fr));
  }
}
@media (max-width: 480px) {
  .checkbox-grid {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
  .phone-row {
    flex-direction: column;
    align-items: stretch;
  }
  .dial-select {
    flex: 1;
  }
}
</style>