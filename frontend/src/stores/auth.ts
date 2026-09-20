import { defineStore } from 'pinia'
import { api } from '@/api/client'

export interface AppUser {
  id: string
  email: string
  user_id: string
  gender: string | null
  age: number | null
  country: string | null
  region: string | null
  first_name: string | null
  last_name: string | null
  real_name: string | null
  real_verified: boolean
  face_enrolled: boolean
  role: 'provider' | 'consumer'
  service_category: string | null
  provider_level:
    | 'level_0' | 'level_1' | 'level_2' | 'level_3' | 'level_4' | null
  /** Derived numeric level: 0..4 or null */
  admin_level: number | null
  /** True for level_0 / level_1 / level_2 */
  is_admin: boolean
  managed_by_id: string | null
  admin_scope_country: string | null
  admin_scope_region: string | null
  is_frozen: boolean
  phone: string | null
  phone_verified: boolean
  is_verified: boolean
  is_active: boolean
}

interface AuthState {
  token: string
  user: AppUser | null
}

export const useAuthStore = defineStore('auth', {
  state: (): AuthState => ({
    token: localStorage.getItem('fdq95_token') || '',
    user: null,
  }),
  getters: {
    isAuthenticated: (s) => !!s.token,
    isAdmin: (s) => s.user?.is_admin === true,
  },
  actions: {
    async login(email: string, password: string) {
      const form = new URLSearchParams()
      form.append('username', email)
      form.append('password', password)
      const { data } = await api.post('/auth/jwt/login', form, {
        headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
      })
      this.token = data.access_token
      localStorage.setItem('fdq95_token', this.token)
      await this.fetchMe()
    },
    async fetchMe() {
      if (!this.token) return
      try {
        const { data } = await api.get('/users/me')
        this.user = data
      } catch {
        this.logout()
      }
    },
    logout() {
      this.token = ''
      this.user = null
      localStorage.removeItem('fdq95_token')
    },
    async enrollFace(credentialId: string) {
      await api.post('/api/auth/face/enroll', {
        face_credential_id: credentialId,
      })
      if (this.user) this.user.face_enrolled = true
    },
    async disableFace() {
      await api.delete('/api/auth/face/enroll')
      if (this.user) this.user.face_enrolled = false
    },
  },
})