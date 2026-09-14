<script setup lang="ts">
import { ref } from 'vue'
import { useI18nStore } from '@/stores/i18n'

const i18n = useI18nStore()

type Tab = 'about' | 'services' | 'news' | 'partners' | 'contact'
const active = ref<Tab>('about')

interface Service {
  name: string
  desc: string
}

const SERVICES: Service[] = [
  {
    name: 'Medical',
    desc: 'Access certified medical practitioners, telehealth consultations, and appointment booking.',
  },
  {
    name: 'Health',
    desc: 'Wellness coaching, nutrition guidance, mental health support, and fitness programmes.',
  },
  {
    name: 'Education',
    desc: 'Tutoring, exam preparation, language courses, and professional certification training.',
  },
  {
    name: 'Entertainment',
    desc: 'Event ticketing, live-streaming access, artist booking, and content production services.',
  },
  {
    name: 'Travel',
    desc: 'Flight and hotel booking, guided tours, visa assistance, and travel insurance.',
  },
  {
    name: 'Food',
    desc: 'Restaurant discovery, catering, meal delivery, and chef-at-home experiences.',
  },
  {
    name: 'Clothing',
    desc: 'Personal styling, custom tailoring, wholesale sourcing, and fashion retail partnerships.',
  },
  {
    name: 'Industry',
    desc: 'Industrial equipment sourcing, manufacturing consulting, and supply-chain coordination.',
  },
  {
    name: 'Technology',
    desc: 'Software development, cloud migration, cybersecurity, and IT support for businesses.',
  },
  {
    name: 'IoT',
    desc: 'Smart-device installation, sensor networks, home and industrial automation solutions.',
  },
]

const NEWS = [
  { date: '2026-09-10', title: 'FDQ95 expands to 12 new countries across Asia-Pacific' },
  { date: '2026-08-28', title: 'Mobile app surpasses 1 million downloads' },
  { date: '2026-08-15', title: 'New IoT service category now live on the platform' },
  { date: '2026-07-30', title: 'FDQ95 completes Series A funding round' },
  { date: '2026-07-12', title: 'Multi-language support rolled out to all users' },
  { date: '2026-06-20', title: 'Partnership announced with leading logistics providers' },
]

const PARTNERS = [
  { name: 'Google Cloud', field: 'Cloud Infrastructure' },
  { name: 'Amazon Web Services', field: 'Cloud Infrastructure' },
  { name: 'Microsoft Azure', field: 'Cloud Infrastructure' },
  { name: 'Stripe', field: 'Payment Processing' },
  { name: 'PayPal', field: 'Payment Processing' },
  { name: 'DHL', field: 'Logistics' },
  { name: 'FedEx', field: 'Logistics' },
  { name: 'Twilio', field: 'Communications' },
]

const TEAM = [
  { name: 'Alex Chen', role: 'Chief Executive Officer' },
  { name: 'Maria Rodriguez', role: 'Chief Technology Officer' },
  { name: 'David Okonkwo', role: 'Chief Operating Officer' },
  { name: 'Sophie Laurent', role: 'Chief Marketing Officer' },
  { name: 'Kenji Tanaka', role: 'Chief Financial Officer' },
]

const TABS: { key: Tab; labelKey: string }[] = [
  { key: 'about', labelKey: 'about_fdq95' },
  { key: 'services', labelKey: 'service_center' },
  { key: 'news', labelKey: 'news' },
  { key: 'partners', labelKey: 'partners' },
  { key: 'contact', labelKey: 'contact_us' },
]
</script>

<template>
  <section class="center-panel">
    <!-- Tab bar -->
    <nav class="tab-bar">
      <button
        v-for="t in TABS"
        :key="t.key"
        class="tab-btn"
        :class="{ active: active === t.key }"
        @click="active = t.key"
      >
        {{ i18n.t(t.labelKey) }}
      </button>
    </nav>

    <div class="tab-content">
      <!-- ---------------- About ---------------- -->
      <section v-if="active === 'about'">
        <h2 class="section-title">{{ i18n.t('about_fdq95') }}</h2>

        <h3 class="sub-title">{{ i18n.t('introduction') }}</h3>
        <p class="paragraph">
          FDQ95 is a global service marketplace that connects consumers with
          verified providers across medical, health, education, entertainment,
          travel, food, clothing, industry, technology, and IoT. Our mission is
          to make high-quality services affordable and accessible to everyone,
          everywhere.
        </p>
        <p class="paragraph">
          Since our founding, we have onboarded thousands of providers in more
          than 60 countries, built a multi-language platform supporting
          eight languages, and launched native mobile apps for iOS, Android,
          and F-Droid.
        </p>

        <h3 class="sub-title">{{ i18n.t('management_team') }}</h3>
        <ul class="team-list">
          <li v-for="m in TEAM" :key="m.name" class="team-item">
            <strong>{{ m.name }}</strong>
            <span class="role">{{ m.role }}</span>
          </li>
        </ul>
      </section>

      <!-- ---------------- Services ---------------- -->
      <section v-else-if="active === 'services'">
        <h2 class="section-title">{{ i18n.t('service_center') }}</h2>

        <div class="service-grid">
          <div v-for="s in SERVICES" :key="s.name" class="service-card">
            <h4 class="service-name">{{ s.name }}</h4>
            <p class="service-desc">{{ s.desc }}</p>
          </div>
        </div>
      </section>

      <!-- ---------------- News ---------------- -->
      <section v-else-if="active === 'news'">
        <h2 class="section-title">{{ i18n.t('news') }}</h2>

        <ul class="news-list">
          <li v-for="n in NEWS" :key="n.title" class="news-item">
            <span class="news-date">{{ n.date }}</span>
            <span class="news-title">{{ n.title }}</span>
          </li>
        </ul>
      </section>

      <!-- ---------------- Partners ---------------- -->
      <section v-else-if="active === 'partners'">
        <h2 class="section-title">{{ i18n.t('partners') }}</h2>

        <ul class="partner-list">
          <li v-for="p in PARTNERS" :key="p.name" class="partner-item">
            <strong class="partner-name">{{ p.name }}</strong>
            <span class="partner-field">{{ p.field }}</span>
          </li>
        </ul>
      </section>

      <!-- ---------------- Contact ---------------- -->
      <section v-else-if="active === 'contact'">
        <h2 class="section-title">{{ i18n.t('contact_us') }}</h2>

        <ul class="contact-list">
          <li><strong>Email</strong> — contact@fdq95.com</li>
          <li><strong>Support</strong> — support@fdq95.com</li>
          <li><strong>Phone</strong> — +1 (800) 373-9500</li>
          <li><strong>Address</strong> — 100 Market Street, Suite 500, San Francisco, CA 94105, USA</li>
          <li><strong>Business Hours</strong> — Monday to Friday, 09:00–18:00 (PST)</li>
        </ul>
      </section>
    </div>
  </section>
</template>

<style scoped>
.center-panel {
  display: flex;
  flex-direction: column;
  background: var(--bg);
  overflow-y: auto;
}

/* ---------- Tab bar ---------- */
.tab-bar {
  display: flex;
  flex-wrap: wrap;
  gap: 0.5rem;
  padding: 0.75rem 1rem;
  background: #1a1a1a;
  border-bottom: 1px solid var(--border);
  position: sticky;
  top: 0;
  z-index: 2;
}
.tab-btn {
  flex: 1 1 auto;
  min-width: 110px;
  padding: 0.5rem 0.75rem;
  background: transparent;
  color: var(--text-dim);
  border: 1px solid var(--border);
  border-radius: 6px;
  font-size: 0.85rem;
  cursor: pointer;
  transition: all 0.15s;
}
.tab-btn:hover {
  color: var(--gold);
  border-color: var(--gold);
}
.tab-btn.active {
  background: var(--gold);
  color: #111;
  border-color: var(--gold);
  font-weight: 600;
}

/* ---------- Content area ---------- */
.tab-content {
  padding: 1.25rem 1.5rem 2rem;
}
.section-title {
  margin: 0 0 1rem;
  color: var(--gold);
  font-size: 1.25rem;
}
.sub-title {
  margin: 1.25rem 0 0.5rem;
  color: var(--text);
  font-size: 1rem;
}
.paragraph {
  color: var(--text-dim);
  line-height: 1.7;
  font-size: 0.92rem;
  margin: 0 0 0.75rem;
}

/* ---------- Team ---------- */
.team-list {
  list-style: none;
  padding: 0;
  margin: 0;
}
.team-item {
  display: flex;
  justify-content: space-between;
  align-items: baseline;
  padding: 0.5rem 0.75rem;
  border-bottom: 1px solid var(--border);
  font-size: 0.9rem;
}
.team-item:last-child {
  border-bottom: none;
}
.role {
  color: var(--text-dim);
  font-size: 0.82rem;
}

/* ---------- Services ---------- */
.service-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 0.75rem;
}
.service-card {
  background: var(--bg-soft);
  border: 1px solid var(--border);
  border-radius: 8px;
  padding: 0.85rem 1rem;
}
.service-name {
  margin: 0 0 0.35rem;
  color: var(--gold);
  font-size: 0.95rem;
}
.service-desc {
  margin: 0;
  color: var(--text-dim);
  font-size: 0.82rem;
  line-height: 1.55;
}

/* ---------- News ---------- */
.news-list {
  list-style: none;
  padding: 0;
  margin: 0;
}
.news-item {
  display: flex;
  gap: 0.75rem;
  align-items: baseline;
  padding: 0.6rem 0.25rem;
  border-bottom: 1px solid var(--border);
  font-size: 0.9rem;
}
.news-item:last-child {
  border-bottom: none;
}
.news-date {
  flex: 0 0 90px;
  color: var(--text-dim);
  font-size: 0.78rem;
}
.news-title {
  color: var(--text);
}

/* ---------- Partners ---------- */
.partner-list {
  list-style: none;
  padding: 0;
  margin: 0;
}
.partner-item {
  display: flex;
  justify-content: space-between;
  align-items: baseline;
  padding: 0.6rem 0.75rem;
  border-bottom: 1px solid var(--border);
  font-size: 0.9rem;
}
.partner-item:last-child {
  border-bottom: none;
}
.partner-name {
  color: var(--gold);
}
.partner-field {
  color: var(--text-dim);
  font-size: 0.8rem;
}

/* ---------- Contact ---------- */
.contact-list {
  list-style: none;
  padding: 0;
  margin: 0;
}
.contact-list li {
  padding: 0.6rem 0.25rem;
  border-bottom: 1px solid var(--border);
  font-size: 0.9rem;
  color: var(--text-dim);
  line-height: 1.6;
}
.contact-list li:last-child {
  border-bottom: none;
}
.contact-list strong {
  color: var(--text);
  display: inline-block;
  min-width: 110px;
}

/* ---------- Responsive ---------- */
@media (max-width: 700px) {
  .service-grid {
    grid-template-columns: 1fr;
  }
  .tab-btn {
    min-width: 80px;
    font-size: 0.8rem;
  }
}
</style>