import { useState, useEffect, useMemo } from 'react'
import { useRouter } from 'next/router'
import Head from 'next/head'
import Link from 'next/link'
import { api, Job, JobLog, JobResult } from '@/lib/api'
import { createJobLogStreamer, JobLogStreamer } from '@/lib/websocket'
import Card from '@/components/Card'
import Button from '@/components/Button'
import StatusBadge from '@/components/StatusBadge'
import ProgressBar from '@/components/ProgressBar'
import LogViewer from '@/components/LogViewer'
import LoadingSpinner from '@/components/LoadingSpinner'
import Badge from '@/components/Badge'
import AlgorithmPerformanceChart from '@/components/charts/AlgorithmPerformanceChart'
import TimeSeriesChart from '@/components/charts/TimeSeriesChart'

export default function JobDetail() {
  const router = useRouter()
  const { id } = router.query

  const [job, setJob] = useState<Job | null>(null)
  const [logs, setLogs] = useState<JobLog[]>([])
  const [results, setResults] = useState<JobResult[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [streamer, setStreamer] = useState<JobLogStreamer | null>(null)
  const [wsConnected, setWsConnected] = useState(false)
  const [actionLoading, setActionLoading] = useState<string | null>(null)
  const [showCharts, setShowCharts] = useState(false)

  // Fetch job details
  useEffect(() => {
    if (!id) return

    const fetchJobDetails = async () => {
      try {
        setLoading(true)
        const [jobData, logsData, resultsData] = await Promise.all([
          api.getJob(id as string),
          api.getLogs(id as string, 1000),
          api.getResults(id as string),
        ])

        setJob(jobData)
        setLogs(logsData)
        setResults(resultsData)
        setLoading(false)
      } catch (err: any) {
        setError(err.response?.data?.detail || err.message || 'Failed to fetch job details')
        setLoading(false)
      }
    }

    fetchJobDetails()

    // Refresh job details periodically
    const interval = setInterval(async () => {
      try {
        const [jobData, resultsData] = await Promise.all([
          api.getJob(id as string),
          api.getResults(id as string),
        ])
        setJob(jobData)
        setResults(resultsData)
      } catch (err) {
        console.error('Failed to refresh job:', err)
      }
    }, 3000)

    return () => clearInterval(interval)
  }, [id])

  // WebSocket connection for real-time logs
  useEffect(() => {
    if (!id || !job) return

    // Only connect WebSocket for running jobs
    if (job.status === 'running' || job.status === 'pending') {
      const newStreamer = createJobLogStreamer(
        id as string,
        (log) => {
          setLogs((prev) => [...prev, log])
        },
        (error) => {
          console.error('WebSocket error:', error)
          setWsConnected(false)
        },
        () => {
          setWsConnected(false)
        }
      )

      setStreamer(newStreamer)
      setWsConnected(true)

      return () => {
        newStreamer.disconnect()
      }
    }
  }, [id, job?.status])

  const handlePause = async () => {
    if (!id) return
    try {
      setActionLoading('pause')
      await api.pauseJob(id as string)
      const updatedJob = await api.getJob(id as string)
      setJob(updatedJob)
    } catch (err: any) {
      alert(`Failed to pause job: ${err.response?.data?.detail || err.message}`)
    } finally {
      setActionLoading(null)
    }
  }

  const handleResume = async () => {
    if (!id) return
    try {
      setActionLoading('resume')
      await api.resumeJob(id as string)
      const updatedJob = await api.getJob(id as string)
      setJob(updatedJob)
    } catch (err: any) {
      alert(`Failed to resume job: ${err.response?.data?.detail || err.message}`)
    } finally {
      setActionLoading(null)
    }
  }

  const handleCancel = async () => {
    if (!id) return
    if (!confirm('Are you sure you want to cancel this job?')) return

    try {
      setActionLoading('cancel')
      await api.cancelJob(id as string)
      const updatedJob = await api.getJob(id as string)
      setJob(updatedJob)
    } catch (err: any) {
      alert(`Failed to cancel job: ${err.response?.data?.detail || err.message}`)
    } finally {
      setActionLoading(null)
    }
  }

  const formatDuration = (seconds?: number) => {
    if (!seconds) return '-'
    const hours = Math.floor(seconds / 3600)
    const minutes = Math.floor((seconds % 3600) / 60)
    const secs = Math.floor(seconds % 60)
    return `${hours}h ${minutes}m ${secs}s`
  }

  // Prepare chart data
  const algorithmPerformanceData = useMemo(() => {
    const grouped: Record<string, { timeSeconds: number; factorsFound: number }> = {}

    results.forEach(result => {
      if (!grouped[result.algorithm]) {
        grouped[result.algorithm] = { timeSeconds: 0, factorsFound: 0 }
      }
      grouped[result.algorithm].timeSeconds += result.elapsed_seconds
      grouped[result.algorithm].factorsFound += 1
    })

    return Object.entries(grouped).map(([name, data]) => ({
      name,
      timeSeconds: parseFloat(data.timeSeconds.toFixed(2)),
      factorsFound: data.factorsFound
    }))
  }, [results])

  const progressTimelineData = useMemo(() => {
    // Extract progress updates from logs
    const progressLogs = logs
      .filter(log => log.message.includes('progress') || log.message.includes('%'))
      .map(log => {
        const timeStr = new Date(log.created_at).toLocaleTimeString()
        // Try to extract percentage from message
        const percentMatch = log.message.match(/(\d+(?:\.\d+)?)\s*%/)
        const value = percentMatch ? parseFloat(percentMatch[1]) : 0
        return { time: timeStr, value, label: log.stage || 'Progress' }
      })

    // Add current progress
    if (job) {
      progressLogs.push({
        time: 'Now',
        value: job.progress_percent,
        label: 'Current'
      })
    }

    return progressLogs
  }, [logs, job])

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 dark:bg-gray-900 py-8 px-4 flex items-center justify-center">
        <LoadingSpinner size="xl" text="Loading job details..." />
      </div>
    )
  }

  if (error || !job) {
    return (
      <div className="min-h-screen bg-gray-50 dark:bg-gray-900 py-8 px-4">
        <div className="max-w-4xl mx-auto">
          <Card>
            <div className="text-center">
              <h1 className="text-2xl font-bold text-red-600 mb-4">Error</h1>
              <p className="text-gray-700 dark:text-gray-300">{error || 'Job not found'}</p>
              <Link href="/" className="inline-block mt-4">
                <Button variant="primary">Back to Home</Button>
              </Link>
            </div>
          </Card>
        </div>
      </div>
    )
  }

  return (
    <>
      <Head>
        <title>Job {job.id} - SemiPrime Factor</title>
      </Head>

      <div className="min-h-screen bg-gray-50 dark:bg-gray-900 py-8 px-4">
        <div className="max-w-7xl mx-auto">
          {/* Header */}
          <div className="mb-6">
            <Link href="/">
              <Button variant="secondary" size="sm">← Back to Home</Button>
            </Link>
          </div>

          {/* Job Overview */}
          <Card className="mb-6">
            <div className="flex justify-between items-start mb-6">
              <div>
                <h1 className="text-3xl font-bold text-gray-900 dark:text-white mb-2">
                  Job Details
                </h1>
                <p className="text-gray-600 dark:text-gray-400">
                  Job ID: <span className="font-mono">{job.id}</span>
                </p>
              </div>
              <div className="flex items-center gap-3">
                <StatusBadge status={job.status} />
                {wsConnected && (
                  <Badge variant="success" size="sm">
                    <span className="mr-1">●</span> Live
                  </Badge>
                )}
              </div>
            </div>

            {/* Progress */}
            <div className="mb-6">
              <h3 className="text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                Progress
              </h3>
              <ProgressBar percent={job.progress_percent} size="lg" />
            </div>

            {/* Job Info Grid */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-6">
              <div>
                <h3 className="text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                  Number (N)
                </h3>
                <p className="font-mono text-sm text-gray-900 dark:text-gray-100 break-all">
                  {job.n}
                </p>
              </div>
              <div>
                <h3 className="text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                  Mode
                </h3>
                <p className="text-gray-900 dark:text-gray-100">{job.mode}</p>
              </div>
              {job.lower_bound && (
                <div>
                  <h3 className="text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                    Lower Bound
                  </h3>
                  <p className="font-mono text-sm text-gray-900 dark:text-gray-100">
                    {job.lower_bound}
                  </p>
                </div>
              )}
              {job.upper_bound && (
                <div>
                  <h3 className="text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                    Upper Bound
                  </h3>
                  <p className="font-mono text-sm text-gray-900 dark:text-gray-100">
                    {job.upper_bound}
                  </p>
                </div>
              )}
              <div>
                <h3 className="text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                  Created At
                </h3>
                <p className="text-gray-900 dark:text-gray-100">
                  {new Date(job.created_at).toLocaleString()}
                </p>
              </div>
              {job.started_at && (
                <div>
                  <h3 className="text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                    Started At
                  </h3>
                  <p className="text-gray-900 dark:text-gray-100">
                    {new Date(job.started_at).toLocaleString()}
                  </p>
                </div>
              )}
              {job.completed_at && (
                <div>
                  <h3 className="text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                    Completed At
                  </h3>
                  <p className="text-gray-900 dark:text-gray-100">
                    {new Date(job.completed_at).toLocaleString()}
                  </p>
                </div>
              )}
              <div>
                <h3 className="text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                  Duration
                </h3>
                <p className="text-gray-900 dark:text-gray-100">
                  {formatDuration(job.elapsed_seconds)}
                </p>
              </div>
            </div>

            {/* Algorithm Policy */}
            <div className="mb-6">
              <h3 className="text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                Algorithm Configuration
              </h3>
              <div className="flex flex-wrap gap-2">
                {job.use_equation && <Badge variant="info">Equation-Guided</Badge>}
                {job.algorithm_policy.use_trial_division && (
                  <Badge variant="info">
                    Trial Division (limit: {job.algorithm_policy.trial_division_limit.toLocaleString()})
                  </Badge>
                )}
                {job.algorithm_policy.use_pollard_rho && (
                  <Badge variant="info">Pollard-rho</Badge>
                )}
                {job.algorithm_policy.use_ecm && <Badge variant="info">ECM</Badge>}
              </div>
            </div>

            {/* Error Message */}
            {job.error_message && (
              <div className="mb-6 p-4 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded">
                <h3 className="text-sm font-medium text-red-800 dark:text-red-300 mb-1">
                  Error
                </h3>
                <p className="text-sm text-red-700 dark:text-red-400">{job.error_message}</p>
              </div>
            )}

            {/* Control Buttons */}
            <div className="flex gap-3">
              {job.status === 'running' && (
                <Button
                  variant="secondary"
                  onClick={handlePause}
                  loading={actionLoading === 'pause'}
                >
                  ⏸ Pause
                </Button>
              )}
              {job.status === 'paused' && (
                <Button
                  variant="success"
                  onClick={handleResume}
                  loading={actionLoading === 'resume'}
                >
                  ▶ Resume
                </Button>
              )}
              {(job.status === 'running' || job.status === 'paused' || job.status === 'pending') && (
                <Button
                  variant="danger"
                  onClick={handleCancel}
                  loading={actionLoading === 'cancel'}
                >
                  ✗ Cancel
                </Button>
              )}
            </div>
          </Card>

          {/* Analytics Toggle */}
          {(results.length > 0 || logs.length > 10) && (
            <Card className="mb-6">
              <div className="flex justify-between items-center">
                <h2 className="text-xl font-bold text-gray-900 dark:text-white">
                  Analytics & Visualizations
                </h2>
                <Button
                  variant={showCharts ? 'primary' : 'secondary'}
                  size="sm"
                  onClick={() => setShowCharts(!showCharts)}
                >
                  {showCharts ? '📊 Hide Charts' : '📊 Show Charts'}
                </Button>
              </div>

              {showCharts && (
                <div className="mt-6 space-y-6">
                  {/* Algorithm Performance */}
                  {results.length > 0 && (
                    <div>
                      <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-3">
                        Algorithm Performance
                      </h3>
                      <AlgorithmPerformanceChart data={algorithmPerformanceData} height={300} />
                    </div>
                  )}

                  {/* Progress Timeline */}
                  {progressTimelineData.length > 1 && (
                    <div>
                      <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-3">
                        Progress Over Time
                      </h3>
                      <TimeSeriesChart
                        data={progressTimelineData}
                        dataKey="value"
                        color="#10b981"
                        height={250}
                        yLabel="Progress (%)"
                      />
                    </div>
                  )}
                </div>
              )}
            </Card>
          )}

          {/* Results */}
          {results.length > 0 && (
            <Card className="mb-6">
              <h2 className="text-2xl font-bold text-gray-900 dark:text-white mb-4">
                Found Factors ({results.length})
              </h2>
              <div className="overflow-x-auto">
                <table className="min-w-full divide-y divide-gray-200 dark:divide-gray-700">
                  <thead className="bg-gray-50 dark:bg-gray-800">
                    <tr>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">
                        Factor
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">
                        Algorithm
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">
                        Prime?
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">
                        Time
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">
                        Found At
                      </th>
                    </tr>
                  </thead>
                  <tbody className="bg-white dark:bg-gray-900 divide-y divide-gray-200 dark:divide-gray-700">
                    {results.map((result) => (
                      <tr key={result.id}>
                        <td className="px-6 py-4 text-sm font-mono text-gray-900 dark:text-gray-100 break-all">
                          {result.factor}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900 dark:text-gray-100">
                          <Badge variant="info">{result.algorithm}</Badge>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm">
                          {result.is_prime ? (
                            <Badge variant="success">Prime</Badge>
                          ) : (
                            <Badge variant="warning">Composite</Badge>
                          )}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900 dark:text-gray-100">
                          {formatDuration(result.elapsed_seconds)}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900 dark:text-gray-100">
                          {new Date(result.created_at).toLocaleString()}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </Card>
          )}

          {/* Logs */}
          <Card>
            <div className="flex justify-between items-center mb-4">
              <h2 className="text-2xl font-bold text-gray-900 dark:text-white">
                Logs ({logs.length})
              </h2>
              {wsConnected && (
                <Badge variant="success" size="sm">
                  <span className="animate-pulse mr-1">●</span> Live Updates
                </Badge>
              )}
            </div>
            <LogViewer logs={logs} autoScroll={true} />
          </Card>
        </div>
      </div>
    </>
  )
}
