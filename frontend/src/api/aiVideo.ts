/**
 * AI 视频生成 API 客户端
 */
import axios from 'axios'

const api = axios.create({
  baseURL: '/api/ai-video',
  timeout: 30000,
})

export interface GenerateRequest {
  idea: string
  target_duration: number
  language: string
  idempotency_key?: string
}

export interface TaskStatus {
  task_id: string
  status: string
  progress: number
  current_step: string
  final_video_url: string | null
  errors: string[]
}

/** 启动视频生成任务 */
export async function startGeneration(req: GenerateRequest): Promise<{ task_id: string; status: string; message: string }> {
  const { data } = await api.post('/generate', req)
  return data
}

/** 查询任务状态 */
export async function getTaskStatus(taskId: string): Promise<TaskStatus> {
  const { data } = await api.get(`/status/${taskId}`)
  return data
}

/** 订阅 SSE 进度流 */
export function subscribeProgress(
  taskId: string,
  onProgress: (data: { progress: number; step: string }) => void,
  onCompleted: (data: TaskStatus) => void,
  onError: (message: string) => void,
): EventSource {
  const es = new EventSource(`/api/ai-video/stream/${taskId}`)

  es.addEventListener('progress', (e: MessageEvent) => {
    const data = JSON.parse(e.data)
    onProgress(data)
  })

  es.addEventListener('completed', (e: MessageEvent) => {
    const data = JSON.parse(e.data)
    onCompleted(data)
    es.close()
  })

  es.addEventListener('error', (e: MessageEvent) => {
    try {
      const data = JSON.parse(e.data)
      onError(data.message || '生成失败')
    } catch {
      onError('连接中断')
    }
    es.close()
  })

  return es
}

/** 获取视频播放地址 */
export function getVideoUrl(videoId: string): string {
  return `/api/ai-video/video/${videoId}`
}

/** 把生成的 AI 视频转正到 uploads/videos/ */

export interface PublishResult {
  ok: boolean
  video_id: string
  public_url: string
  file_size: number
}

/** 把生成的 AI 视频转正到 uploads/videos/ */
export async function publishAiVideo(
  videoId: string,
  title: string,
): Promise<PublishResult> {
  const { data } = await api.post('/publish', { video_id: videoId, title })
  return data
}