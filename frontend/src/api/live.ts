import { api } from '@/api/client'

export interface LiveSession {
  room_id: string
  host_user_id: string
  host_uuid: string
  host_display_name: string
  host_avatar_url: string | null
  title: string
  category: string | null
  status: 'live' | 'ended'
  started_at: string
  ended_at: string | null
  viewer_count: number
  is_live: boolean
}

export interface LiveTokenResponse {
  token: string
  room_id: string
  is_moderator: boolean
  server_url: string
  expires_in: number
}

export const liveApi = {
  async start(title: string, category: string | null): Promise<LiveSession> {
    const { data } = await api.post('/api/live/start', { title, category })
    return data
  },
  async end(roomId: string) {
    const { data } = await api.post(`/api/live/${roomId}/end`)
    return data
  },
  async listActive(limit = 20, offset = 0): Promise<LiveSession[]> {
    const { data } = await api.get('/api/live/active', {
      params: { limit, offset },
    })
    return data
  },
  async getRoom(roomId: string): Promise<LiveSession> {
    const { data } = await api.get(`/api/live/${roomId}`)
    return data
  },
  async getToken(roomId: string): Promise<LiveTokenResponse> {
    const { data } = await api.get(`/api/live/${roomId}/token`)
    return data
  },
  async invite(roomId: string, inviteeUserId: string) {
    const { data } = await api.post(
      `/api/live/${roomId}/invite/${inviteeUserId}`
    )
    return data
  },
  async listInvitees(roomId: string) {
    const { data } = await api.get(`/api/live/${roomId}/invitees`)
    return data
  },
}