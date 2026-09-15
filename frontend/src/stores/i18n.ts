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
  last_name: 'Last Name',
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

  // ---- profile / messages / friends ----
  personal_home: 'Personal Home',
  video_list: 'Video List',
  launch_activity: 'Launch Activity',
  activity_replay: 'Activity Replay',
  product_list: 'Product List',
  friend_list: 'Friend List',
  message: 'Message',
  add_as_friend: 'Add as Friend',
  friend_request_sent: 'Friend request sent',
  friend_request_failed: 'Failed to send request',
  no_friends_yet: 'No friends yet',
  no_videos_yet: 'No videos yet',
  no_activity_replays: 'No activity replays yet',
  no_products_yet: 'No products yet',

  recommend_to_wechat: 'Recommend to WeChat',
  recommend_to_whatsapp: 'Recommend to WhatsApp',
  recommend_whatsapp_text: 'Check out this profile on FDQ95',
  complaint: 'Complaint',
  complaint_requires_real_name:
    'Only real-name verified users can file a complaint.',
  cancel: 'Cancel',

  msg_rule_hint: 'Until they reply, you can only send one message.',
  message_placeholder: 'Write a message…',
  wait_for_reply: 'Waiting for reply',
  message_send_failed: 'Failed to send',
  send: 'Send',
  no_messages_yet: 'No messages yet',
  upload_placeholder: 'Upload',

  // ---- registration v2 ----
  password_confirm: 'Confirm Password',
  passwords_do_not_match: 'Passwords do not match',
  passwords_match: 'Passwords match',
  password_too_short: 'Password must be at least 8 characters',
  user_id_taken: 'This User ID is already taken',
  email_taken: 'This email is already registered',
  available: 'Available',
  checking: 'Checking...',
  register_success_verify_email:
    'Registration successful! Please check your email to verify your account before logging in.',

  // ---- forgot / reset password ----
  forgot_password: 'Forgot Password?',
  // ▼▼▼ UPDATED to match requirement ▼▼▼
  forgot_password_desc: 'Enter your email address below:',
  // ▲▲▲
  send_reset_link: 'Send Reset Link',
  reset_link_sent:
    'If that email exists, a password reset link has been sent. Check your inbox.',
  reset_password: 'Reset Password',
  reset_success: 'Password reset successful! Redirecting to login...',
  reset_failed: 'Password reset failed. The link may be expired.',
  invalid_reset_link: 'Invalid reset link',
  new_password: 'New Password',
  back_to_login: 'Back to Login',

  // ---- face recognition ----
  face_recognition: 'Face Recognition',
  face_prompt_message:
    'Would you like to enable face recognition for faster login?',
  add: 'Add',
  dont_show_again: "Don't show this dialog again",
  face_enroll_title: 'Setup Face Recognition',
  face_enroll_hint:
    'Position your face within the frame and capture samples to enable face login.',
  face_enroll_success: 'Face recognition enabled successfully!',
  face_enroll_failed: 'Failed to set up face recognition. Please try again.',
  face_capture: 'Capture Face',
  face_scanning: 'Scanning...',
  continue_to_profile: 'Continue to Profile',
  face_login_title: 'Face Login',
  face_login_hint:
    'Position your face within the frame to log in with your face credential.',
  face_login_button: 'Scan Face',
  no_face_credential:
    'No face credential found on this device. Please set up face recognition first.',
  face_setup_link: 'Set up face recognition',
  enable_face_login: 'Enable Face Recognition Login',
  face_login_prompt: 'Enter your face credential ID',
  face_login_failed: 'Face login failed. Please use your password.',
  face_enrolled: 'Face recognition is enabled for this account',
  disable_face: 'Disable Face Recognition',
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