import { onBeforeUnmount, ref } from 'vue'

export interface UseRecordingOptions {
  /** 最长录制秒数（自动停止），默认 20 分钟 */
  maxDurationSec?: number
  /** 最大文件大小 MB（自动停止），默认 400 */
  maxSizeMB?: number
}

export function useRecording(options: UseRecordingOptions = {}) {
  const maxDurationSec = options.maxDurationSec ?? 20 * 60
  const maxSizeMB = options.maxSizeMB ?? 400

  const isRecording = ref(false)
  const duration = ref(0)         // 秒
  const sizeMB = ref(0)
  const autoStoppedReason = ref('')

  let mediaRecorder: MediaRecorder | null = null
  let displayStream: MediaStream | null = null
  let micStream: MediaStream | null = null
  let chunks: BlobPart[] = []
  let timer: number | null = null
  let startedAt = 0

  function pickMimeType(): string {
    const candidates = [
      'video/webm;codecs=vp9,opus',
      'video/webm;codecs=vp8,opus',
      'video/webm',
      'video/mp4',
    ]
    for (const t of candidates) {
      if (typeof MediaRecorder !== 'undefined' && MediaRecorder.isTypeSupported(t)) {
        return t
      }
    }
    return ''
  }

  async function start() {
    if (isRecording.value) return
    if (typeof navigator === 'undefined' || !navigator.mediaDevices) {
      throw new Error('浏览器不支持录制 API')
    }

    // 1. 请求屏幕共享（全屏录制）
    const stream = await (navigator.mediaDevices as any).getDisplayMedia({
      video: {
        frameRate: 30,
        width: { ideal: 1280 },
        height: { ideal: 720 },
      },
      audio: true,          // 尝试录标签页/系统音频（Chrome 会弹窗询问）
    })
    displayStream = stream as MediaStream

    // 2. 若用户没给标签页音频，则尝试加麦克风
    const hasAudio = displayStream.getAudioTracks().length > 0
    if (!hasAudio) {
      try {
        micStream = await navigator.mediaDevices.getUserMedia({ audio: true })
        micStream.getAudioTracks().forEach((t) => displayStream!.addTrack(t))
      } catch {
        // 麦克风被拒，继续无音频录制
      }
    }

    // 3. 创建 MediaRecorder
    chunks = []
    sizeMB.value = 0
    duration.value = 0
    autoStoppedReason.value = ''
    const mimeType = pickMimeType()
    const recorder = new MediaRecorder(displayStream, {
      mimeType: mimeType || undefined,
      videoBitsPerSecond: 2_500_000,   // 2.5 Mbps，约 18 MB/分钟
    })
    mediaRecorder = recorder

    recorder.ondataavailable = (e) => {
      if (e.data && e.data.size > 0) {
        chunks.push(e.data)
        const total = chunks.reduce((s, c) => s + (c as Blob).size, 0)
        sizeMB.value = total / 1024 / 1024
        if (sizeMB.value > maxSizeMB) {
          autoStoppedReason.value = `超过 ${maxSizeMB} MB，已自动停止`
          void stop()
        }
      }
    }

    recorder.start(1000)
    isRecording.value = true
    startedAt = Date.now()

    timer = window.setInterval(() => {
      duration.value = Math.floor((Date.now() - startedAt) / 1000)
      if (duration.value >= maxDurationSec) {
        autoStoppedReason.value = `超过 ${Math.round(maxDurationSec / 60)} 分钟，已自动停止`
        void stop()
      }
    }, 1000)

    // 用户在浏览器原生条上点"停止共享"时同步停止
    displayStream.getVideoTracks()[0].addEventListener('ended', () => {
      if (isRecording.value) void stop()
    })
  }

  function stop(): Promise<Blob | null> {
    return new Promise((resolve) => {
      const recorder = mediaRecorder
      if (!recorder || recorder.state === 'inactive') {
        cleanup()
        resolve(null)
        return
      }
      recorder.onstop = () => {
        const blob = new Blob(chunks, {
          type: recorder.mimeType || 'video/webm',
        })
        cleanup()
        resolve(blob)
      }
      try {
        recorder.stop()
      } catch {
        cleanup()
        resolve(null)
      }
    })
  }

  function cleanup() {
    if (displayStream) {
      displayStream.getTracks().forEach((t) => t.stop())
      displayStream = null
    }
    if (micStream) {
      micStream.getTracks().forEach((t) => t.stop())
      micStream = null
    }
    if (timer) {
      clearInterval(timer)
      timer = null
    }
    isRecording.value = false
    mediaRecorder = null
  }

  onBeforeUnmount(() => {
    if (isRecording.value) void stop()
  })

  return {
    isRecording,
    duration,
    sizeMB,
    autoStoppedReason,
    start,
    stop,
  }
}