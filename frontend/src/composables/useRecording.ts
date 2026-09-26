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
  const duration = ref(0)
  const sizeMB = ref(0)
  const autoStoppedReason = ref('')

  // ★ 录制结束后保存 blob 与预览 URL（供预览弹窗播放）
  const pendingBlob = ref<Blob | null>(null)
  const pendingUrl = ref<string>('')

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

    // 每次开始前清掉上一次的残留
    discard()

    const stream = await (navigator.mediaDevices as any).getDisplayMedia({
      video: {
        frameRate: 30,
        width: { ideal: 1280 },
        height: { ideal: 720 },
        displaySurface: 'browser',       // ★ 提示优先显示标签页
      },
      audio: true,
      preferCurrentTab: true,            // ★ Chrome 自动选中当前标签页
      selfBrowserSurface: 'include',     // 允许共享当前标签页
      surfaceSwitching: 'include',       // 允许录制中切换共享源
      systemAudio: 'include',            // 尽量捕获系统音频
    })
    displayStream = stream as MediaStream

    const hasAudio = displayStream.getAudioTracks().length > 0
    if (!hasAudio) {
      try {
        micStream = await navigator.mediaDevices.getUserMedia({ audio: true })
        micStream.getAudioTracks().forEach((t) => displayStream!.addTrack(t))
      } catch {
        // 麦克风被拒，继续无音频录制
      }
    }

    chunks = []
    sizeMB.value = 0
    duration.value = 0
    autoStoppedReason.value = ''
    const mimeType = pickMimeType()
    const recorder = new MediaRecorder(displayStream, {
      mimeType: mimeType || undefined,
      videoBitsPerSecond: 2_500_000,
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

    displayStream.getVideoTracks()[0].addEventListener('ended', () => {
      if (isRecording.value) void stop()
    })
  }

  function stop(): Promise<Blob | null> {
    return new Promise((resolve) => {
      const recorder = mediaRecorder
      if (!recorder || recorder.state === 'inactive') {
        cleanupStreams()
        resolve(null)
        return
      }
      recorder.onstop = () => {
        const blob = new Blob(chunks, {
          type: recorder.mimeType || 'video/webm',
        })
        cleanupStreams()
        // ★ 保留 blob 供预览与上传
        setPending(blob)
        resolve(blob)
      }
      try {
        recorder.stop()
      } catch {
        cleanupStreams()
        resolve(null)
      }
    })
  }

  function setPending(blob: Blob) {
    // 清掉上一个
    if (pendingUrl.value) URL.revokeObjectURL(pendingUrl.value)
    pendingBlob.value = blob
    pendingUrl.value = URL.createObjectURL(blob)
  }

  /** 丢弃当前待处理的录制（关弹窗、重新录制时调用） */
  function discard() {
    if (pendingUrl.value) {
      URL.revokeObjectURL(pendingUrl.value)
      pendingUrl.value = ''
    }
    pendingBlob.value = null
  }

  /** 取用 blob 后自动清空（上传成功后调用） */
  function takeBlob(): Blob | null {
    const b = pendingBlob.value
    pendingBlob.value = null
    if (pendingUrl.value) {
      URL.revokeObjectURL(pendingUrl.value)
      pendingUrl.value = ''
    }
    return b
  }

  function cleanupStreams() {
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
    discard()
  })

  return {
    isRecording,
    duration,
    sizeMB,
    autoStoppedReason,
    pendingBlob,
    pendingUrl,
    start,
    stop,
    discard,
    takeBlob,
  }
}