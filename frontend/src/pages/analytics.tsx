import { useState, useEffect } from 'react'
import Head from 'next/head'
import Link from 'next/link'
import { api, Job } from '@/lib/api'
import Card from '@/components/Card'
import Button from '@/components/Button'
import LoadingSpinner from '@/components/LoadingSpinner'
import FactorDistributionChart from '@/components/charts/FactorDistributionChart'
import AlgorithmPerformanceChart from '@/components/charts/AlgorithmPerformanceChart'
import ProgressChart from '@/components/charts/ProgressChart'

export default function Analytics() {
  const [jobs, setJobs] = useState<Job[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    fetchJobs()
  }, [])

  const fetchJobs = async () => {
    try {
      const data = await api.getJobs(100)
      setJobs(data)
      setLoading(false)
    } catch (err) {
      console.error('Failed to fetch jobs:', err)
      setLoading(false)
    }
  }

  // Calculate statistics
  const stats = {
    total: jobs.length,
    completed: jobs.filter(j => j.status === 'completed').length,
    running: jobs.filter(j => j.status === 'running').length,
    failed: jobs.filter(j => j.status === 'failed').length,
    avgProgress: jobs.length > 0
      ? (jobs.reduce((sum, j) => sum + j.progress_percent, 0) / jobs.length).toFixed(1)
      : 0
  }

  // Status distribution for pie chart
  const statusDistribution = [
    { name: 'Completed', value: stats.completed, color: '#10b981' },
    { name: 'Running', value: stats.running, color: '#3b82f6' },
    { name: 'Failed', value: stats.failed, color: '#ef4444' },
    { name: 'Other', value: stats.total - stats.completed - stats.running - stats.failed, color: '#6b7280' }
  ].filter(item => item.value > 0)

  // Recent progress data
  const progressData = jobs
    .slice(0, 20)
    .reverse()
    .map((job, idx) => ({
      timestamp: `Job ${idx + 1}`,
      progress: job.progress_percent
    }))

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 dark:bg-gray-900 py-8 px-4 flex items-center justify-center">
        <LoadingSpinner size="xl" text="Loading analytics..." />
      </div>
    )
  }

  return (
    <>
      <Head>
        <title>Analytics Dashboard - SemiPrime Factor</title>
      </Head>

      <div className="min-h-screen bg-gradient-to-br from-gray-50 to-gray-100 dark:from-gray-900 dark:to-gray-800 py-8 px-4">
        <div className="max-w-7xl mx-auto">
          {/* Header */}
          <div className="mb-6 flex justify-between items-center">
            <div>
              <h1 className="text-4xl font-bold text-gray-900 dark:text-white mb-2">
                Analytics Dashboard
              </h1>
              <p className="text-gray-600 dark:text-gray-400">
                Comprehensive insights into factorization performance
              </p>
            </div>
            <Link href="/">
              <Button variant="secondary">← Back to Home</Button>
            </Link>
          </div>

          {/* Stats Overview */}
          <div className="grid grid-cols-2 md:grid-cols-5 gap-4 mb-8">
            <Card className="text-center">
              <p className="text-sm text-gray-600 dark:text-gray-400 mb-1">Total Jobs</p>
              <p className="text-3xl font-bold text-gray-900 dark:text-white">{stats.total}</p>
            </Card>
            <Card className="text-center">
              <p className="text-sm text-gray-600 dark:text-gray-400 mb-1">Completed</p>
              <p className="text-3xl font-bold text-green-600 dark:text-green-400">{stats.completed}</p>
            </Card>
            <Card className="text-center">
              <p className="text-sm text-gray-600 dark:text-gray-400 mb-1">Running</p>
              <p className="text-3xl font-bold text-blue-600 dark:text-blue-400">{stats.running}</p>
            </Card>
            <Card className="text-center">
              <p className="text-sm text-gray-600 dark:text-gray-400 mb-1">Failed</p>
              <p className="text-3xl font-bold text-red-600 dark:text-red-400">{stats.failed}</p>
            </Card>
            <Card className="text-center">
              <p className="text-sm text-gray-600 dark:text-gray-400 mb-1">Avg Progress</p>
              <p className="text-3xl font-bold text-purple-600 dark:text-purple-400">{stats.avgProgress}%</p>
            </Card>
          </div>

          {/* Charts Grid */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
            {/* Status Distribution */}
            <Card>
              <h2 className="text-xl font-bold text-gray-900 dark:text-white mb-4">
                Job Status Distribution
              </h2>
              {statusDistribution.length > 0 ? (
                <FactorDistributionChart data={statusDistribution} height={300} />
              ) : (
                <p className="text-gray-500 text-center py-12">No data available</p>
              )}
            </Card>

            {/* Progress Trend */}
            <Card>
              <h2 className="text-xl font-bold text-gray-900 dark:text-white mb-4">
                Recent Jobs Progress
              </h2>
              {progressData.length > 0 ? (
                <ProgressChart data={progressData} height={300} />
              ) : (
                <p className="text-gray-500 text-center py-12">No data available</p>
              )}
            </Card>
          </div>

          {/* Algorithm Usage */}
          <Card className="mb-8">
            <h2 className="text-xl font-bold text-gray-900 dark:text-white mb-4">
              Algorithm Configuration Usage
            </h2>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              <div className="text-center p-4 bg-blue-50 dark:bg-blue-900/20 rounded-lg">
                <p className="text-sm text-gray-600 dark:text-gray-400 mb-1">Equation-Guided</p>
                <p className="text-2xl font-bold text-blue-600 dark:text-blue-400">
                  {jobs.filter(j => j.use_equation).length}
                </p>
              </div>
              <div className="text-center p-4 bg-green-50 dark:bg-green-900/20 rounded-lg">
                <p className="text-sm text-gray-600 dark:text-gray-400 mb-1">Trial Division</p>
                <p className="text-2xl font-bold text-green-600 dark:text-green-400">
                  {jobs.filter(j => j.algorithm_policy?.use_trial_division).length}
                </p>
              </div>
              <div className="text-center p-4 bg-purple-50 dark:bg-purple-900/20 rounded-lg">
                <p className="text-sm text-gray-600 dark:text-gray-400 mb-1">Pollard-Rho</p>
                <p className="text-2xl font-bold text-purple-600 dark:text-purple-400">
                  {jobs.filter(j => j.algorithm_policy?.use_pollard_rho).length}
                </p>
              </div>
              <div className="text-center p-4 bg-yellow-50 dark:bg-yellow-900/20 rounded-lg">
                <p className="text-sm text-gray-600 dark:text-gray-400 mb-1">ECM</p>
                <p className="text-2xl font-bold text-yellow-600 dark:text-yellow-400">
                  {jobs.filter(j => j.algorithm_policy?.use_ecm).length}
                </p>
              </div>
            </div>
          </Card>

          {/* Recent Jobs Table */}
          <Card>
            <h2 className="text-xl font-bold text-gray-900 dark:text-white mb-4">
              Recent Jobs
            </h2>
            <div className="overflow-x-auto">
              <table className="min-w-full divide-y divide-gray-200 dark:divide-gray-700">
                <thead className="bg-gray-50 dark:bg-gray-800">
                  <tr>
                    <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">
                      Created
                    </th>
                    <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">
                      Number Digits
                    </th>
                    <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">
                      Status
                    </th>
                    <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">
                      Progress
                    </th>
                    <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">
                      Mode
                    </th>
                  </tr>
                </thead>
                <tbody className="bg-white dark:bg-gray-900 divide-y divide-gray-200 dark:divide-gray-700">
                  {jobs.slice(0, 10).map(job => (
                    <tr key={job.id} className="hover:bg-gray-50 dark:hover:bg-gray-800">
                      <td className="px-4 py-3 text-sm text-gray-900 dark:text-gray-100">
                        {new Date(job.created_at).toLocaleDateString()}
                      </td>
                      <td className="px-4 py-3 text-sm text-gray-900 dark:text-gray-100">
                        {job.n.length} digits
                      </td>
                      <td className="px-4 py-3 text-sm">
                        <span className={`px-2 py-1 rounded-full text-xs ${
                          job.status === 'completed' ? 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200' :
                          job.status === 'running' ? 'bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200' :
                          job.status === 'failed' ? 'bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200' :
                          'bg-gray-100 text-gray-800 dark:bg-gray-700 dark:text-gray-200'
                        }`}>
                          {job.status}
                        </span>
                      </td>
                      <td className="px-4 py-3 text-sm text-gray-900 dark:text-gray-100">
                        {job.progress_percent.toFixed(1)}%
                      </td>
                      <td className="px-4 py-3 text-sm text-gray-900 dark:text-gray-100">
                        {job.mode}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </Card>
        </div>
      </div>
    </>
  )
}
