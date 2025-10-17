import axios, { AxiosInstance } from 'axios'

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8080'

export interface Job {
  id: string
  created_at: string
  n: string
  mode: string
  status: 'pending' | 'running' | 'paused' | 'completed' | 'failed' | 'cancelled'
  progress_percent: number
  lower_bound?: string
  upper_bound?: string
  use_equation: boolean
  algorithm_policy: AlgorithmPolicy
  error_message?: string
  started_at?: string
  completed_at?: string
  elapsed_seconds?: number
}

export interface AlgorithmPolicy {
  use_trial_division: boolean
  trial_division_limit: number
  use_pollard_rho: boolean
  pollard_rho_iterations: number
  use_ecm: boolean
}

export interface JobLog {
  id: string
  job_id: string
  created_at: string
  level: 'INFO' | 'WARNING' | 'ERROR'
  message: string
  stage?: string
  payload?: any
}

export interface JobResult {
  id: string
  job_id: string
  created_at: string
  factor: string
  algorithm: string
  is_prime: boolean
  elapsed_seconds: number
}

export interface CreateJobRequest {
  n: string
  mode: string
  lower_bound?: string | null
  upper_bound?: string | null
  use_equation: boolean
  algorithm_policy: AlgorithmPolicy
}

export interface UploadResponse {
  upload_id: string
  total_jobs: number
  created_jobs: number
  failed_rows: number
  errors: string[]
}

class ApiClient {
  private client: AxiosInstance

  constructor() {
    this.client = axios.create({
      baseURL: API_URL,
      headers: {
        'Content-Type': 'application/json',
      },
    })
  }

  // Jobs
  async getJobs(limit: number = 20): Promise<Job[]> {
    const response = await this.client.get(`/api/jobs?limit=${limit}`)
    return response.data
  }

  async getJob(id: string): Promise<Job> {
    const response = await this.client.get(`/api/jobs/${id}`)
    return response.data
  }

  async createJob(data: CreateJobRequest): Promise<Job> {
    const response = await this.client.post('/api/jobs', data)
    return response.data
  }

  async pauseJob(id: string): Promise<void> {
    await this.client.post(`/api/jobs/${id}/control`, { action: 'pause' })
  }

  async resumeJob(id: string): Promise<void> {
    await this.client.post(`/api/jobs/${id}/control`, { action: 'resume' })
  }

  async cancelJob(id: string): Promise<void> {
    await this.client.post(`/api/jobs/${id}/control`, { action: 'cancel' })
  }

  // Logs
  async getLogs(jobId: string, limit: number = 100): Promise<JobLog[]> {
    const response = await this.client.get(`/api/jobs/${jobId}/logs?limit=${limit}`)
    return response.data
  }

  // Results
  async getResults(jobId: string): Promise<JobResult[]> {
    const response = await this.client.get(`/api/jobs/${jobId}/results`)
    return response.data
  }

  // Upload
  async uploadCSV(file: File): Promise<UploadResponse> {
    const formData = new FormData()
    formData.append('file', file)

    const response = await this.client.post('/api/upload/csv', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    })
    return response.data
  }

  // Health
  async checkHealth(): Promise<{ status: string; timestamp: string }> {
    const response = await this.client.get('/api/health')
    return response.data
  }
}

export const api = new ApiClient()
export { API_URL }
