import { defineStore } from 'pinia'
import { api } from '@/api/client'

export const BASE_TEXT: Record<string, string> = {
  welcome_title: 'FDQ95-Solutions for affordable services',
  welcome_desc:
    'Connect with trusted service providers across medical, education, entertainment, travel, food, clothing, and industry.',
  home: 'Home',
  login: 'Login',
  register: 'Register',
  email: 'Email',
  password: 'Password',
  user_id: 'User ID',
  gender: 'Gender',
  age: 'Age',
  birth_year: 'Birth Year',
  country: 'Country',
  phone: 'Phone',
  phone_code: 'Code',
  first_name: 'First Name',
  family_name: 'Family Name',
  real_name: 'Real Name',
  service_category: 'Service Category',
  account_type: 'Account Type',
  provider: 'Service Provider',
  consumer: 'Service Consumer',
  verify_email: 'Verify Email',
  verify_phone: 'Verify Phone',
  footer_text:
    'FDQ95 mobile - download our apps to\nenjoy affordable services from anywhere',
  app_store: 'Download on the App Store',
  google_play: 'Get it on Google Play',
  fdroid: 'Get it on F-Droid',
  invalid_credentials: 'Invalid credentials',
  login_success: 'Login successful',
  register_success: 'Registration successful! Please check your email.',
  register_failed: 'Registration failed',
  please_fill_required: 'Please fill required fields',
  please_pick_one_category: 'Please select exactly one service category',
  male: 'Male',
  female: 'Female',
  other: 'Other',

  provider_level: 'Provider Level',
  level_0: 'System Administrator',
  level_1: 'National Administrator',
  level_2: 'Regional Administrator',
  level_3: 'Sales Administrator',
  level_4: 'Service Provider',

  careers: 'Careers',
  jobs_title: 'Job Openings',
  jobs_subtitle: 'Select a country and a job category to view open positions.',
  select_country: 'Country',
  select_category: 'Job Category',
  job_category_tech: 'Technology',
  job_category_management: 'Management',
  job_category_sales: 'Sales',
  no_jobs_found: 'No jobs found for the selected criteria.',
  please_select_filters: 'Please select both country and category.',
  job_requirements: 'Requirements',
  job_location: 'Location',
  apply_now: 'Apply Now',
  back_to_list: 'Back to job list',
  apply_form_title: 'Apply for this position',
  applicant_name: 'Your Name',
  applicant_email: 'Your Email',
  cover_letter_file: 'Resume / Cover Letter (PDF, DOC, DOCX, max 10 MB)',
  submit_application: 'Submit Application',
  application_success: 'Application submitted successfully!',
  application_failed: 'Submission failed. Please try again.',
  application_missing_fields: 'Please fill in all fields and attach a file.',

  // ---- Home page panels ----
  top_clicked_videos: 'Top Clicked Videos',
  latest_uploads: 'Latest Uploads',

  // ---- Center tabs ----
  about_fdq95: 'About FDQ95',
  service_center: 'Service Center',
  news: 'News',
  partners: 'Partners',
  contact_us: 'Contact Us',
  introduction: 'Introduction',
  management_team: 'Management Team',
  play_video: 'Play Video',

  // ---- Video player page ----
  tab_best: 'Best',
  tab_latest: 'Latest',
  tab_following: 'Following',
  tab_recommended: 'Recommended',
  tab_search: 'Search',
  tab_settings: 'Settings',
  search: 'Search',
  search_placeholder: 'Search videos, creators, keywords…',
  no_results: 'No results found.',
  no_comments: 'No comments yet. Be the first!',
  comment_placeholder: 'Write a comment…',
  post_comment: 'Post',
  comments: 'Comments',
  share: 'Share',
  copy_link: 'Copy Link',
  link_copied: 'Link copied',
  views: 'views',
  publisher_profile: 'Publisher',
  follow: 'Follow',
  unfollow: 'Unfollow',
  videos: 'videos',

  // ---- Settings ----
  display_name: 'Display Name',
  user_id_label: 'User ID',
  bio: 'Bio',
  language: 'Language',
  notifications: 'Enable notifications',
  private_account: 'Private account',
  save: 'Save',
}

export const LANGUAGES: Record<string, string> = {
  en: 'English',
  'zh-CN': '中文',
  es: 'Español',
  fr: 'Français',
  de: 'Deutsch',
  ja: '日本語',
  ko: '한국어',
  ar: 'العربية',
}

interface I18nState {
  language: string
  translations: Record<string, string>
  cache: Record<string, Record<string, string>>
}

export const useI18nStore = defineStore('i18n', {
  state: (): I18nState => ({
    language: localStorage.getItem('fdq95_lang') || 'en',
    translations: { ...BASE_TEXT },
    cache: { en: { ...BASE_TEXT } },
  }),
  actions: {
    t(key: string): string {
      return this.translations[key] ?? BASE_TEXT[key] ?? key
    },
    async init() {
      if (this.language !== 'en') {
        await this.setLanguage(this.language)
      }
    },
    async setLanguage(lang: string) {
      this.language = lang
      localStorage.setItem('fdq95_lang', lang)

      if (this.cache[lang]) {
        this.translations = this.cache[lang]
        return
      }
      if (lang === 'en') {
        this.translations = { ...BASE_TEXT }
        return
      }
      try {
        const { data } = await api.post('/api/translate', {
          texts: BASE_TEXT,
          target: lang,
          source: 'en',
        })
        this.cache[lang] = data.translations
        this.translations = data.translations
      } catch (e) {
        console.error('[i18n] translation failed', e)
        this.translations = { ...BASE_TEXT }
      }
    },
  },
})