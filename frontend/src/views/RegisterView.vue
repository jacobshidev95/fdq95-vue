<script setup lang="ts">
import { ref, reactive } from 'vue'
import { useRouter } from 'vue-router'
import { AxiosError } from 'axios'
import { useI18nStore } from '@/stores/i18n'
import { api } from '@/api/client'

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

const CATEGORIES: { value: Category; label: string }[] = [
  { value: 'medical', label: 'Medical' },
  { value: 'health', label: 'Health' },
  { value: 'education', label: 'Education' },
  { value: 'entertainment', label: 'Entertainment' },
  { value: 'travel', label: 'Travel' },
  { value: 'food', label: 'Food' },
  { value: 'clothing', label: 'Clothing' },
  { value: 'industry', label: 'Industry' },
]

const form = reactive({
  role: 'consumer' as Role,
  user_id: '',
  email: '',
  gender: '',
  age: null as number | null,
  country: '',
  password: '',
  service_category: null as Category | null,
  phone: '',
  real_name: '',
})

const error = ref('')
const success = ref('')
const loading = ref(false)

function close() {
  router.push('/')
}

// 单选行为：勾选新的会自动取消旧的
function toggleCategory(cat: Category, checked: boolean) {
  form.service_category = checked ? cat : null
}

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
    age: form.age,
    country: form.country || null,
    role: form.role,
    service_category: form.service_category,
  }
  if (form.role === 'provider') {
    payload.phone = form.phone || null
    payload.real_name = form.real_name || null
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

    <label>{{ i18n.t('age') }}</label>
    <input v-model.number="form.age" type="number" min="1" max="120" />

    <label>{{ i18n.t('country') }}</label>
    <input v-model="form.country" type="text" />

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
        <span>{{ cat.label }}</span>
      </label>
    </div>

    <template v-if="form.role === 'provider'">
      <label>{{ i18n.t('phone') }}</label>
      <input v-model="form.phone" type="tel" />

      <label>{{ i18n.t('real_name') }}</label>
      <input v-model="form.real_name" type="text" />
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
  max-width: 640px;
}
.card-title {
  text-align: center;
  margin: 0 0 1rem;
}

/* 8 checkboxes in 2 rows x 4 columns, aligned */
.checkbox-grid {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 0.5rem 1rem;
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

@media (max-width: 640px) {
  .checkbox-grid {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
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
</style>