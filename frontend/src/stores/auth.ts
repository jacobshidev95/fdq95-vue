import { defineStore } from 'pinia'
import { api } from '@/api/client'

export interface AppUser {
  id: string
  email: string
  user_id: string
  gender: string | null
  age: number | null
  country: string | null
  role: 'provider' | 'consumer'
  service_category: string | null
  phone: string | null
  real_name: string | null
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
      } catch (e) {
        console.error('[auth] fetchMe failed', e)
        this.logout()
      }
    },
    logout() {
      this.token = ''
      this.user = null
      localStorage.removeItem('fdq95_token')
    },
  },
})
