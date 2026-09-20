import { defineStore } from 'pinia'
import { api } from '@/api/client'

export interface ProfileData {
  id: string
  user_id: string
  user_string_id: string
  display_name: string
  avatar_url: string | null
  bio_line_1: string
  bio_line_2: string
  real_verified: boolean
  created_at: string
}

export interface FriendEntry {
  user_id: string
  user_string_id: string
  display_name: string
  avatar_url: string | null
}

export interface FriendRequestEntry {
  id: string
  other_id: string
  other_string_id: string
  other_display_name: string
  status: string
  created_at: string
}

interface ProfileState {
  me: ProfileData | null
  viewing: ProfileData | null
  following: boolean
  isFriend: boolean
  hasPendingRequest: boolean
  friends: FriendEntry[]
  inbox: FriendRequestEntry[]
}

export const useProfileStore = defineStore('profile', {
  state: (): ProfileState => ({
    me: null,
    viewing: null,
    following: false,
    isFriend: false,
    hasPendingRequest: false,
    friends: [],
    inbox: [],
  }),
  actions: {
    async loadMe() {
      const { data } = await api.get('/api/profile/me')
      this.me = data
    },
    async loadUser(userStringId: string) {
      const { data } = await api.get(`/api/profile/user/${userStringId}`)
      this.viewing = data
      try {
        const r = await api.get(`/api/social/follow/${userStringId}/status`)
        this.following = r.data.following
      } catch {
        this.following = false
      }
    },
    async loadFriendStatus(userStringId: string) {
      try {
        const { data } = await api.get(`/api/friends/pending/${userStringId}`)
        this.isFriend = !!data.is_friend
        this.hasPendingRequest = !!data.has_pending
      } catch {
        this.isFriend = false
        this.hasPendingRequest = false
      }
    },
    async toggleFollow() {
      if (!this.viewing) return
      const id = this.viewing.user_string_id
      if (this.following) {
        await api.delete(`/api/social/follow/${id}`)
        this.following = false
      } else {
        await api.post(`/api/social/follow/${id}`)
        this.following = true
      }
    },
    async sendFriendRequest(userStringId: string) {
      const { data } = await api.post(`/api/friends/request/${userStringId}`)
      if (data?.status === 'sent' || data?.status === 'pending') {
        this.hasPendingRequest = true
      }
      if (data?.status === 'already_friends') {
        this.isFriend = true
      }
      return data
    },
    async loadFriends() {
      const { data } = await api.get('/api/friends/list')
      this.friends = data
    },
    async loadIncomingRequests() {
      const { data } = await api.get('/api/friends/requests/inbox')
      this.inbox = data
    },
    async acceptRequest(requestId: string) {
      const { data } = await api.post(
        `/api/friends/requests/${requestId}/accept`,
      )
      this.inbox = this.inbox.filter((r) => r.id !== requestId)
      return data
    },
    async rejectRequest(requestId: string) {
      const { data } = await api.post(
        `/api/friends/requests/${requestId}/reject`,
      )
      this.inbox = this.inbox.filter((r) => r.id !== requestId)
      return data
    },
    resetViewing() {
      this.viewing = null
      this.following = false
      this.isFriend = false
      this.hasPendingRequest = false
    },
  },
})