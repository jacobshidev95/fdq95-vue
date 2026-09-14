<script setup lang="ts">
import { ref, watch, onMounted } from 'vue'
import { api } from '@/api/client'
import { useI18nStore } from '@/stores/i18n'
import { COUNTRIES } from '@/data/countries'

const i18n = useI18nStore()

interface Job {
  id: string
  title: string
  category: string
  country: string
  location: string
  requirements: string
  description: string
}

const JOB_CATEGORIES = [
  { value: 'tech', key: 'job_category_tech' },
  { value: 'management', key: 'job_category_management' },
  { value: 'sales', key: 'job_category_sales' },
]

const selectedCountry = ref('')
const selectedCategory = ref('')
const jobs = ref<Job[]>([])
const loading = ref(false)

const selectedJob = ref<Job | null>(null)
const showApplyForm = ref(false)

const applicantName = ref('')
const applicantEmail = ref('')
const coverFile = ref<File | null>(null)
const submitMessage = ref('')
const submitError = ref('')
const submitting = ref(false)

async function loadJobs() {
  if (!selectedCountry.value || !selectedCategory.value) {
    jobs.value = []
    return
  }
  loading.value = true
  try {
    const { data } = await api.get('/api/jobs', {
      params: {
        country: selectedCountry.value,
        category: selectedCategory.value,
      },
    })
    jobs.value = data.jobs || []
  } catch (e) {
    console.error('[jobs] load failed', e)
    jobs.value = []
  } finally {
    loading.value = false
  }
}

// Reset selection and reload when filters change
watch([selectedCountry, selectedCategory], () => {
  selectedJob.value = null
  showApplyForm.value = false
  loadJobs()
})

function openJob(job: Job) {
  selectedJob.value = job
  showApplyForm.value = false
  submitMessage.value = ''
  submitError.value = ''
}

function backToList() {
  selectedJob.value = null
  showApplyForm.value = false
}

function openApplyForm() {
  showApplyForm.value = true
  applicantName.value = ''
  applicantEmail.value = ''
  coverFile.value = null
  submitMessage.value = ''
  submitError.value = ''
}

function onFileChange(e: Event) {
  const input = e.target as HTMLInputElement
  coverFile.value = input.files?.[0] || null
}

async function submitApplication() {
  submitMessage.value = ''
  submitError.value = ''

  if (
    !applicantName.value.trim() ||
    !applicantEmail.value.trim() ||
    !coverFile.value ||
    !selectedJob.value
  ) {
    submitError.value = i18n.t('application_missing_fields')
    return
  }

  submitting.value = true
  try {
    const fd = new FormData()
    fd.append('job_id', selectedJob.value.id)
    fd.append('name', applicantName.value.trim())
    fd.append('email', applicantEmail.value.trim())
    fd.append('file', coverFile.value)

    await api.post('/api/applications', fd, {
      headers: { 'Content-Type': 'multipart/form-data' },
    })
    submitMessage.value = i18n.t('application_success')
    applicantName.value = ''
    applicantEmail.value = ''
    coverFile.value = null
  } catch (e) {
    console.error('[jobs] submit failed', e)
    submitError.value = i18n.t('application_failed')
  } finally {
    submitting.value = false
  }
}

function countryName(code: string): string {
  const c = COUNTRIES.find((c) => c.code === code)
  return c ? c.name : code
}

// Best-effort: preselect the user's country by IP
onMounted(async () => {
  try {
    const resp = await fetch('https://ipapi.co/json/', { cache: 'no-store' })
    if (!resp.ok) return
    const data = await resp.json()
    const code = (data?.country_code || '').toUpperCase()
    if (code && COUNTRIES.some((c) => c.code === code)) {
      selectedCountry.value = code
    }
  } catch {
    /* offline — leave empty */
  }
})
</script>

<template>
  <section class="jobs-page">
    <h1 class="title-gold page-title">{{ i18n.t('jobs_title') }}</h1>
    <p class="page-sub">{{ i18n.t('jobs_subtitle') }}</p>

    <!-- ---------- Filter row ---------- -->
    <div class="filters">
      <div class="filter">
        <label>{{ i18n.t('select_country') }}</label>
        <select v-model="selectedCountry">
          <option value="">--</option>
          <option v-for="c in COUNTRIES" :key="c.code" :value="c.code">
            {{ c.name }}
          </option>
        </select>
      </div>

      <div class="filter">
        <label>{{ i18n.t('select_category') }}</label>
        <select v-model="selectedCategory">
          <option value="">--</option>
          <option v-for="cat in JOB_CATEGORIES" :key="cat.value" :value="cat.value">
            {{ i18n.t(cat.key) }}
          </option>
        </select>
      </div>
    </div>

    <!-- ---------- States ---------- -->
    <p v-if="loading" class="hint">{{ i18n.t('loading') || 'Loading…' }}</p>

    <p
      v-else-if="!selectedJob && (selectedCountry && selectedCategory) && jobs.length === 0"
      class="hint"
    >
      {{ i18n.t('no_jobs_found') }}
    </p>

    <!-- ---------- Job list ---------- -->
    <ul v-if="!selectedJob && jobs.length > 0" class="job-list">
      <li
        v-for="job in jobs"
        :key="job.id"
        class="job-item"
        @click="openJob(job)"
      >
        <div class="job-title">{{ job.title }}</div>
        <div class="job-meta">
          {{ countryName(job.country) }} · {{ job.location }}
        </div>
      </li>
    </ul>

    <!-- ---------- Job detail ---------- -->
    <div v-if="selectedJob" class="job-detail card">
      <button class="back-btn" @click="backToList">
        ← {{ i18n.t('back_to_list') }}
      </button>

      <h2 class="job-detail-title">{{ selectedJob.title }}</h2>
      <p class="job-detail-meta">
        {{ countryName(selectedJob.country) }} · {{ selectedJob.location }}
      </p>

      <h3 class="section-h">{{ i18n.t('job_requirements') }}</h3>
      <pre class="requirements">{{ selectedJob.requirements }}</pre>

      <p v-if="selectedJob.description" class="job-desc">
        {{ selectedJob.description }}
      </p>

      <button
        v-if="!showApplyForm"
        class="btn btn-primary apply-btn"
        @click="openApplyForm"
      >
        {{ i18n.t('apply_now') }}
      </button>

      <!-- ---------- Apply form ---------- -->
      <div v-if="showApplyForm" class="apply-form">
        <h3 class="section-h">{{ i18n.t('apply_form_title') }}</h3>

        <div v-if="submitError" class="notice notice-error">
          {{ submitError }}
        </div>
        <div v-if="submitMessage" class="notice notice-ok">
          {{ submitMessage }}
        </div>

        <label>{{ i18n.t('applicant_name') }}</label>
        <input v-model="applicantName" type="text" />

        <label>{{ i18n.t('applicant_email') }}</label>
        <input v-model="applicantEmail" type="email" />

        <label>{{ i18n.t('cover_letter_file') }}</label>
        <input
          type="file"
          accept=".pdf,.doc,.docx,application/pdf,application/msword,application/vnd.openxmlformats-officedocument.wordprocessingml.document"
          @change="onFileChange"
        />

        <button
          class="btn btn-primary btn-block"
          :disabled="submitting"
          @click="submitApplication"
        >
          {{ i18n.t('submit_application') }}
        </button>
      </div>
    </div>
  </section>
</template>

<style scoped>
.jobs-page {
  width: 100%;
  max-width: 760px;
  text-align: center;
}
.page-title {
  font-size: 2rem;
  margin: 0 0 0.5rem;
}
.page-sub {
  color: var(--text-dim);
  margin-bottom: 2rem;
}

.filters {
  display: flex;
  gap: 1rem;
  justify-content: center;
  flex-wrap: wrap;
  margin-bottom: 1.5rem;
}
.filter {
  text-align: left;
  flex: 1 1 220px;
  max-width: 260px;
}
.filter label {
  margin-top: 0;
}

.hint {
  color: var(--text-dim);
  margin: 1.5rem 0;
}

/* ---------------- Job list ---------------- */
.job-list {
  list-style: none;
  padding: 0;
  margin: 0;
  text-align: left;
}
.job-item {
  background: var(--bg-soft);
  border: 1px solid var(--border);
  border-radius: 8px;
  padding: 1rem 1.25rem;
  margin-bottom: 0.75rem;
  cursor: pointer;
  transition: border-color 0.15s, background 0.15s;
}
.job-item:hover {
  border-color: var(--gold);
  background: #2f2f2f;
}
.job-title {
  font-weight: 700;
  color: var(--gold);
  margin-bottom: 0.25rem;
}
.job-meta {
  font-size: 0.85rem;
  color: var(--text-dim);
}

/* ---------------- Job detail ---------------- */
.job-detail {
  text-align: left;
}
.back-btn {
  background: transparent;
  border: none;
  color: var(--gold);
  padding: 0;
  margin-bottom: 0.75rem;
  cursor: pointer;
  font-size: 0.9rem;
}
.back-btn:hover {
  text-decoration: underline;
}
.job-detail-title {
  margin: 0 0 0.25rem;
  color: var(--gold);
}
.job-detail-meta {
  color: var(--text-dim);
  font-size: 0.85rem;
  margin-bottom: 1rem;
}
.section-h {
  margin: 1.25rem 0 0.5rem;
  color: var(--text);
  font-size: 1rem;
}
.requirements {
  white-space: pre-wrap;
  font-family: inherit;
  color: var(--text);
  background: #1e1e1e;
  border: 1px solid var(--border);
  border-radius: 6px;
  padding: 0.75rem 1rem;
  font-size: 0.9rem;
  line-height: 1.6;
  margin: 0;
}
.job-desc {
  color: var(--text-dim);
  font-size: 0.9rem;
  margin: 0.75rem 0 0;
}
.apply-btn {
  margin-top: 1.25rem;
}
.apply-form {
  margin-top: 1rem;
  padding-top: 1rem;
  border-top: 1px solid var(--border);
}
.apply-form input[type="file"] {
  padding: 0.5rem;
  cursor: pointer;
}
</style>