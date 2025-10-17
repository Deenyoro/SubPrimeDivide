import { useState } from 'react'
import { useRouter } from 'next/router'
import Head from 'next/head'
import Link from 'next/link'
import { useDropzone } from 'react-dropzone'
import { api, UploadResponse } from '@/lib/api'
import Card from '@/components/Card'
import Button from '@/components/Button'
import Badge from '@/components/Badge'

export default function BulkUpload() {
  const router = useRouter()
  const [uploading, setUploading] = useState(false)
  const [result, setResult] = useState<UploadResponse | null>(null)
  const [error, setError] = useState<string | null>(null)

  const onDrop = async (acceptedFiles: File[]) => {
    if (acceptedFiles.length === 0) return

    const file = acceptedFiles[0]

    // Validate file type
    if (!file.name.endsWith('.csv')) {
      setError('Please upload a CSV file')
      return
    }

    setUploading(true)
    setError(null)
    setResult(null)

    try {
      const uploadResult = await api.uploadCSV(file)
      setResult(uploadResult)
    } catch (err: any) {
      setError(err.response?.data?.detail || err.message || 'Failed to upload CSV')
    } finally {
      setUploading(false)
    }
  }

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      'text/csv': ['.csv'],
    },
    multiple: false,
  })

  const downloadTemplate = () => {
    const csvContent = `n,mode,lower_bound,upper_bound,use_equation,use_trial_division,trial_division_limit,use_pollard_rho,pollard_rho_iterations,use_ecm
123456789,auto,,,true,true,10000000,true,1000000,true
987654321,equation_guided,1e5,1e10,true,false,,false,,false`

    const blob = new Blob([csvContent], { type: 'text/csv' })
    const url = window.URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = 'semiprime_template.csv'
    a.click()
    window.URL.revokeObjectURL(url)
  }

  return (
    <>
      <Head>
        <title>Bulk CSV Upload - SemiPrime Factor</title>
      </Head>

      <div className="min-h-screen bg-gray-50 dark:bg-gray-900 py-8 px-4">
        <div className="max-w-4xl mx-auto">
          {/* Header */}
          <div className="mb-6">
            <Link href="/">
              <Button variant="secondary" size="sm">← Back to Home</Button>
            </Link>
          </div>

          <Card>
            <h1 className="text-3xl font-bold text-gray-900 dark:text-white mb-2">
              Bulk CSV Upload
            </h1>
            <p className="text-gray-600 dark:text-gray-400 mb-6">
              Upload a CSV file with multiple numbers to create factorization jobs in bulk.
            </p>

            {/* Instructions */}
            <div className="bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-lg p-4 mb-6">
              <h3 className="text-sm font-semibold text-blue-900 dark:text-blue-200 mb-2">
                CSV Format
              </h3>
              <p className="text-sm text-blue-800 dark:text-blue-300 mb-2">
                Your CSV file should include the following columns:
              </p>
              <ul className="text-sm text-blue-800 dark:text-blue-300 list-disc list-inside space-y-1">
                <li><strong>n</strong> (required): The number to factor</li>
                <li><strong>mode</strong>: auto, equation_guided, or range_scan (default: auto)</li>
                <li><strong>lower_bound</strong>: Optional lower bound for search</li>
                <li><strong>upper_bound</strong>: Optional upper bound for search</li>
                <li><strong>use_equation</strong>: true/false (default: true)</li>
                <li><strong>use_trial_division</strong>: true/false (default: true)</li>
                <li><strong>trial_division_limit</strong>: Number (default: 10000000)</li>
                <li><strong>use_pollard_rho</strong>: true/false (default: true)</li>
                <li><strong>pollard_rho_iterations</strong>: Number (default: 1000000)</li>
                <li><strong>use_ecm</strong>: true/false (default: true)</li>
              </ul>
              <div className="mt-4">
                <button
                  onClick={downloadTemplate}
                  className="text-sm text-blue-600 dark:text-blue-400 hover:underline font-medium"
                >
                  Download CSV Template
                </button>
              </div>
            </div>

            {/* Drop Zone */}
            <div
              {...getRootProps()}
              className={`border-2 border-dashed rounded-lg p-12 text-center cursor-pointer transition-colors ${
                isDragActive
                  ? 'border-blue-500 bg-blue-50 dark:bg-blue-900/20'
                  : 'border-gray-300 dark:border-gray-600 hover:border-blue-400 dark:hover:border-blue-500'
              }`}
            >
              <input {...getInputProps()} />
              <div className="text-gray-600 dark:text-gray-400">
                {uploading ? (
                  <div className="flex flex-col items-center">
                    <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mb-4"></div>
                    <p className="text-lg font-medium">Uploading...</p>
                  </div>
                ) : isDragActive ? (
                  <div>
                    <p className="text-lg font-medium text-blue-600 dark:text-blue-400">
                      Drop the CSV file here
                    </p>
                  </div>
                ) : (
                  <div>
                    <svg
                      className="mx-auto h-12 w-12 text-gray-400 mb-4"
                      stroke="currentColor"
                      fill="none"
                      viewBox="0 0 48 48"
                      aria-hidden="true"
                    >
                      <path
                        d="M28 8H12a4 4 0 00-4 4v20m32-12v8m0 0v8a4 4 0 01-4 4H12a4 4 0 01-4-4v-4m32-4l-3.172-3.172a4 4 0 00-5.656 0L28 28M8 32l9.172-9.172a4 4 0 015.656 0L28 28m0 0l4 4m4-24h8m-4-4v8m-12 4h.02"
                        strokeWidth={2}
                        strokeLinecap="round"
                        strokeLinejoin="round"
                      />
                    </svg>
                    <p className="text-lg font-medium mb-1">
                      Drag and drop your CSV file here
                    </p>
                    <p className="text-sm">or click to browse</p>
                  </div>
                )}
              </div>
            </div>

            {/* Error Message */}
            {error && (
              <div className="mt-6 p-4 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded">
                <h3 className="text-sm font-medium text-red-800 dark:text-red-300 mb-1">
                  Upload Failed
                </h3>
                <p className="text-sm text-red-700 dark:text-red-400">{error}</p>
              </div>
            )}

            {/* Success Result */}
            {result && (
              <div className="mt-6">
                <div className="bg-green-50 dark:bg-green-900/20 border border-green-200 dark:border-green-800 rounded-lg p-4 mb-4">
                  <h3 className="text-lg font-semibold text-green-900 dark:text-green-200 mb-3">
                    Upload Successful!
                  </h3>
                  <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                    <div>
                      <p className="text-sm text-green-800 dark:text-green-300 mb-1">
                        Total Jobs
                      </p>
                      <p className="text-2xl font-bold text-green-900 dark:text-green-100">
                        {result.total_jobs}
                      </p>
                    </div>
                    <div>
                      <p className="text-sm text-green-800 dark:text-green-300 mb-1">
                        Created Successfully
                      </p>
                      <p className="text-2xl font-bold text-green-900 dark:text-green-100">
                        {result.created_jobs}
                      </p>
                    </div>
                    <div>
                      <p className="text-sm text-green-800 dark:text-green-300 mb-1">
                        Failed Rows
                      </p>
                      <p className="text-2xl font-bold text-red-600 dark:text-red-400">
                        {result.failed_rows}
                      </p>
                    </div>
                  </div>
                  <p className="text-sm text-green-800 dark:text-green-300 mt-3">
                    Upload ID: <span className="font-mono">{result.upload_id}</span>
                  </p>
                </div>

                {/* Errors List */}
                {result.errors && result.errors.length > 0 && (
                  <div className="bg-yellow-50 dark:bg-yellow-900/20 border border-yellow-200 dark:border-yellow-800 rounded-lg p-4 mb-4">
                    <h3 className="text-sm font-semibold text-yellow-900 dark:text-yellow-200 mb-2">
                      Errors ({result.errors.length})
                    </h3>
                    <div className="max-h-40 overflow-y-auto">
                      <ul className="text-sm text-yellow-800 dark:text-yellow-300 space-y-1">
                        {result.errors.map((err, idx) => (
                          <li key={idx} className="font-mono text-xs">
                            {err}
                          </li>
                        ))}
                      </ul>
                    </div>
                  </div>
                )}

                {/* Actions */}
                <div className="flex gap-3">
                  <Link href="/">
                    <Button variant="primary">View Jobs</Button>
                  </Link>
                  <Button
                    variant="secondary"
                    onClick={() => {
                      setResult(null)
                      setError(null)
                    }}
                  >
                    Upload Another File
                  </Button>
                </div>
              </div>
            )}
          </Card>

          {/* Example */}
          <Card className="mt-6">
            <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-3">
              Example CSV Content
            </h3>
            <div className="bg-gray-900 rounded-lg p-4 overflow-x-auto">
              <pre className="text-sm text-green-400 font-mono">
{`n,mode,lower_bound,upper_bound,use_equation,use_trial_division,trial_division_limit
123456789,auto,,,true,true,10000000
987654321,equation_guided,1e5,1e10,true,false,
15,auto,,,true,true,10000000`}
              </pre>
            </div>
          </Card>
        </div>
      </div>
    </>
  )
}
