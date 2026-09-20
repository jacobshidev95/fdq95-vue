export interface Video {
  id: number
  title: string
  views: number
}

/**
 * Top-clicked videos (50 in total, shown in 5 pages of 10).
 * Page 1: 1-10, Page 2: 11-20, ... Page 5: 41-50
 */
export const TOP_CLICKED: Video[] = Array.from({ length: 50 }, (_, i) => {
  const rank = i + 1
  return {
    id: rank,
    title: `Top Video #${rank}`,
    views: 5_000_000 - i * 60_000,
  }
})

/**
 * Latest uploaded videos (100 in total, shown in 10 pages of 10).
 * Page 1: 1-10, Page 2: 11-20, ... Page 10: 91-100
 */
export const LATEST_UPLOADS: Video[] = Array.from({ length: 100 }, (_, i) => {
  const n = i + 1
  return {
    id: n,
    title: `Latest Video #${n}`,
    views: 500_000 - i * 3_500,
  }
})

/** Deterministic pastel hue per video id, used for the thumbnail placeholder. */
export function hueFor(id: number): number {
  return (id * 47) % 360
}