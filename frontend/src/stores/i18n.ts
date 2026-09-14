import { defineStore } from 'pinia'
import { api } from '@/api/client'

export const BASE_TEXT: Record<string, string> = {
  welcome_title: 'FDQ95',
  welcome_desc:
    'Connect with trusted service providers across medical, education, entertainment, travel, food, clothing, and industry.',
  login: 'Login',
  register: 'Register',
  email: 'Email',
  password: 'Password',
  user_id: 'User ID',
  gender: 'Gender',
  age: 'Age',
  country: 'Country',
  phone: 'Phone',
  real_name: 'Real Name',
  service_category: 'Service Category',
  account_type: 'Account Type',
  provider: 'Service Provider',
  consumer: 'Service Consumer',
  verify_email: 'Verify Email',
  verify_phone: 'Verify Phone',
  footer_text:
    'FDQ95 mobile - download our apps\nto enjoy affordable services from anywhere',
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
