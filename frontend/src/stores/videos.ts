import { defineStore } from 'pinia'
import { generateVideos, type VideoComment, type VideoItem } from '@/data/videos'

interface UserSettings {
  displayName: string
  userId: string
  bio: string
  email: string
  country: string
  language: string
  notifications: boolean
  privateAccount: boolean
}

interface VideosState {
  videos: VideoItem[]
  following: string[]
  likedIds: number[]
  heartedIds: number[]
  comments: Record<number, VideoComment[]>
  settings: UserSettings
}

export const useVideosStore = defineStore('videos', {
  state: (): VideosState => ({
    videos: generateVideos(),
    following: ['creator_001', 'creator_005', 'creator_009'],
    likedIds: [],
    heartedIds: [],
    comments: {},
    settings: {
      displayName: 'FDQ95 User',
      userId: 'user_001',
      bio: 'Welcome to my profile',
      email: 'user@fdq95.com',
      country: 'US',
      language: 'en',
      notifications: true,
      privateAccount: false,
    },
  }),

  getters: {
    /** Top clicked — by views desc */
    topVideos(state): VideoItem[] {
      return [...state.videos].sort((a, b) => b.views - a.views)
    },
    /** Latest — by upload date desc */
    latestVideos(state): VideoItem[] {
      return [...state.videos].sort(
        (a, b) =>
          new Date(b.uploadedAt).getTime() - new Date(a.uploadedAt).getTime(),
      )
    },
    /** Following — videos from followed creators, newest first */
    followingVideos(state): VideoItem[] {
      const set = new Set(state.following)
      return state.videos
        .filter((v) => set.has(v.authorId))
        .sort(
          (a, b) =>
            new Date(b.uploadedAt).getTime() -
            new Date(a.uploadedAt).getTime(),
        )
    },
    /** Recommended — weighted score */
    recommendedVideos(state): VideoItem[] {
      const now = Date.now()
      return [...state.videos]
        .map((v) => {
          const ageHr = (now - new Date(v.uploadedAt).getTime()) / 3_600_000
          const recency = Math.max(0, 1_000_000 - ageHr * 5_000)
          const score =
            v.views * 0.3 + v.likes * 0.4 + v.hearts * 0.3 + recency
          return { v, score }
        })
        .sort((a, b) => b.score - a.score)
        .map((x) => x.v)
    },
    isLiked: (state) => (id: number) => state.likedIds.includes(id),
    isHearted: (state) => (id: number) => state.heartedIds.includes(id),
    isFollowing: (state) => (authorId: string) =>
      state.following.includes(authorId),
    commentsFor: (state) => (id: number) => state.comments[id] || [],
  },

  actions: {
    like(id: number) {
      const v = this.videos.find((x) => x.id === id)
      if (!v) return
      if (this.likedIds.includes(id)) {
        this.likedIds = this.likedIds.filter((x) => x !== id)
        v.likes = Math.max(0, v.likes - 1)
      } else {
        this.likedIds.push(id)
        v.likes += 1
      }
    },
    heart(id: number) {
      const v = this.videos.find((x) => x.id === id)
      if (!v) return
      if (this.heartedIds.includes(id)) {
        this.heartedIds = this.heartedIds.filter((x) => x !== id)
        v.hearts = Math.max(0, v.hearts - 1)
      } else {
        this.heartedIds.push(id)
        v.hearts += 1
      }
    },
    follow(authorId: string) {
      if (!this.following.includes(authorId)) {
        this.following.push(authorId)
      }
    },
    unfollow(authorId: string) {
      this.following = this.following.filter((x) => x !== authorId)
    },
    addComment(videoId: number, text: string, authorId: string) {
      const v = this.videos.find((x) => x.id === videoId)
      if (!v) return
      const list = this.comments[videoId] || []
      list.push({
        id: `c_${Date.now()}_${Math.random().toString(36).slice(2, 7)}`,
        videoId,
        authorId,
        authorHue: (authorId.length * 47) % 360,
        text,
        createdAt: new Date().toISOString(),
      })
      this.comments[videoId] = list
      v.commentCount += 1
    },
    searchByKeyword(kw: string): VideoItem[] {
      const q = kw.trim().toLowerCase()
      if (!q) return []
      return this.videos.filter(
        (v) =>
          v.title.toLowerCase().includes(q) ||
          v.authorId.toLowerCase().includes(q) ||
          v.description.toLowerCase().includes(q),
      )
    },
    getById(id: number): VideoItem | undefined {
      return this.videos.find((v) => v.id === id)
    },
    getByAuthor(authorId: string): VideoItem[] {
      return this.videos
        .filter((v) => v.authorId === authorId)
        .sort(
          (a, b) =>
            new Date(b.uploadedAt).getTime() -
            new Date(a.uploadedAt).getTime(),
        )
    },
  },
})