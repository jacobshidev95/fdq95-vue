export interface VideoComment {
  id: string
  videoId: number
  authorId: string
  authorHue: number
  text: string
  createdAt: string
}

export interface VideoItem {
  id: number
  title: string
  authorId: string
  authorHue: number
  views: number
  likes: number
  hearts: number
  commentCount: number
  uploadedAt: string
  durationSec: number
  hue: number
  description: string
}

const now = Date.now()
const HOUR = 3_600_000

export function generateVideos(): VideoItem[] {
  const tags = ['Cooking', 'Travel', 'Tech', 'Music', 'Fitness', 'Nature']
  return Array.from({ length: 100 }, (_, i) => {
    const rank = i + 1
    const authorIdx = (i % 20) + 1
    const denom = rank * 0.3 + 1
    return {
      id: rank,
      title: `Video #${rank} — ${tags[i % tags.length]} Showcase`,
      authorId: `creator_${String(authorIdx).padStart(3, '0')}`,
      authorHue: (authorIdx * 37) % 360,
      views: Math.floor(5_000_000 / denom),
      likes: Math.floor(500_000 / denom),
      hearts: Math.floor(200_000 / denom),
      commentCount: Math.floor(50_000 / denom),
      uploadedAt: new Date(now - rank * 2 * HOUR).toISOString(),
      durationSec: 15 + (rank % 60),
      hue: (rank * 47) % 360,
      description: `Description for video #${rank}. Tap to play.`,
    }
  })
}

export function timeAgo(iso: string): string {
  const diff = Date.now() - new Date(iso).getTime()
  const sec = Math.floor(diff / 1000)
  if (sec < 60) return `${sec}s ago`
  const min = Math.floor(sec / 60)
  if (min < 60) return `${min}m ago`
  const hr = Math.floor(min / 60)
  if (hr < 24) return `${hr}h ago`
  const day = Math.floor(hr / 24)
  if (day < 30) return `${day}d ago`
  const month = Math.floor(day / 30)
  if (month < 12) return `${month}mo ago`
  return `${Math.floor(month / 12)}y ago`
}

export function formatCount(n: number): string {
  if (n >= 1_000_000) return `${(n / 1_000_000).toFixed(1)}M`
  if (n >= 1_000) return `${(n / 1_000).toFixed(1)}K`
  return String(n)
}