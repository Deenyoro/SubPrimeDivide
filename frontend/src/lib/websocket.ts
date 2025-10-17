import { JobLog } from './api'

const WS_URL = process.env.NEXT_PUBLIC_API_URL?.replace(/^http/, 'ws') || 'ws://localhost:8080'

export type LogCallback = (log: JobLog) => void
export type ErrorCallback = (error: Event) => void
export type CloseCallback = () => void

export class JobLogStreamer {
  private ws: WebSocket | null = null
  private jobId: string
  private onLog: LogCallback
  private onError?: ErrorCallback
  private onClose?: CloseCallback
  private reconnectAttempts = 0
  private maxReconnectAttempts = 5
  private reconnectDelay = 1000
  private shouldReconnect = true

  constructor(
    jobId: string,
    onLog: LogCallback,
    onError?: ErrorCallback,
    onClose?: CloseCallback
  ) {
    this.jobId = jobId
    this.onLog = onLog
    this.onError = onError
    this.onClose = onClose
  }

  connect(): void {
    try {
      this.ws = new WebSocket(`${WS_URL}/api/jobs/${this.jobId}/stream`)

      this.ws.onopen = () => {
        console.log(`WebSocket connected for job ${this.jobId}`)
        this.reconnectAttempts = 0
      }

      this.ws.onmessage = (event) => {
        try {
          const log = JSON.parse(event.data) as JobLog
          this.onLog(log)
        } catch (error) {
          console.error('Failed to parse WebSocket message:', error)
        }
      }

      this.ws.onerror = (error) => {
        console.error('WebSocket error:', error)
        if (this.onError) {
          this.onError(error)
        }
      }

      this.ws.onclose = () => {
        console.log(`WebSocket closed for job ${this.jobId}`)
        if (this.onClose) {
          this.onClose()
        }

        // Attempt reconnection
        if (this.shouldReconnect && this.reconnectAttempts < this.maxReconnectAttempts) {
          this.reconnectAttempts++
          console.log(`Reconnecting (attempt ${this.reconnectAttempts}/${this.maxReconnectAttempts})...`)
          setTimeout(() => this.connect(), this.reconnectDelay * this.reconnectAttempts)
        }
      }
    } catch (error) {
      console.error('Failed to create WebSocket:', error)
    }
  }

  disconnect(): void {
    this.shouldReconnect = false
    if (this.ws) {
      this.ws.close()
      this.ws = null
    }
  }

  isConnected(): boolean {
    return this.ws !== null && this.ws.readyState === WebSocket.OPEN
  }
}

export function createJobLogStreamer(
  jobId: string,
  onLog: LogCallback,
  onError?: ErrorCallback,
  onClose?: CloseCallback
): JobLogStreamer {
  const streamer = new JobLogStreamer(jobId, onLog, onError, onClose)
  streamer.connect()
  return streamer
}
