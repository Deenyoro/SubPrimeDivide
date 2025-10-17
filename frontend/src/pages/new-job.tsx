import { useState } from 'react'
import Head from 'next/head'
import { useRouter } from 'next/router'
import Link from 'next/link'
import { api } from '@/lib/api'
import Card from '@/components/Card'
import Button from '@/components/Button'
import Badge from '@/components/Badge'

// RSA-260 example from the request
const RSA_260_EXAMPLE = "2211282552952966643528108525502623092761208950247001539441374831912882294140200198651272972656974659908590033003140005117074220456085927635795375718595442988389587092292384910067030341246205457845664136645406842143612930176940208463910658759147942514351444581992"

const EXAMPLES = [
  {
    name: 'Small Composite',
    n: '15',
    desc: 'Quick test (3 × 5)',
  },
  {
    name: 'Medium Semiprime',
    n: '123456789',
    desc: '9-digit number',
  },
  {
    name: 'RSA-260',
    n: RSA_260_EXAMPLE,
    desc: '260-digit RSA challenge',
    bounds: { lower: '1e90', upper: '1e130' },
  },
]

export default function NewJob() {
  const router = useRouter()
  const [loading, setLoading] = useState(false)
  const [errors, setErrors] = useState<Record<string, string>>({})
  const [formData, setFormData] = useState({
    n: '',
    mode: 'auto',
    lower_bound: '',
    upper_bound: '',
    use_equation: true,
    use_trial_division: true,
    trial_division_limit: '10000000',
    use_pollard_rho: true,
    pollard_rho_iterations: '1000000',
    use_ecm: true,
  })

  const validateForm = () => {
    const newErrors: Record<string, string> = {}

    if (!formData.n.trim()) {
      newErrors.n = 'Number is required'
    } else if (!/^\d+$/.test(formData.n.trim())) {
      newErrors.n = 'Number must contain only digits'
    }

    if (formData.use_trial_division && formData.trial_division_limit) {
      const limit = parseInt(formData.trial_division_limit)
      if (isNaN(limit) || limit < 1) {
        newErrors.trial_division_limit = 'Must be a positive number'
      }
    }

    if (formData.use_pollard_rho && formData.pollard_rho_iterations) {
      const iterations = parseInt(formData.pollard_rho_iterations)
      if (isNaN(iterations) || iterations < 1) {
        newErrors.pollard_rho_iterations = 'Must be a positive number'
      }
    }

    setErrors(newErrors)
    return Object.keys(newErrors).length === 0
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()

    if (!validateForm()) {
      return
    }

    setLoading(true)

    try {
      const job = await api.createJob({
        n: formData.n.trim(),
        mode: formData.mode,
        lower_bound: formData.lower_bound || null,
        upper_bound: formData.upper_bound || null,
        use_equation: formData.use_equation,
        algorithm_policy: {
          use_trial_division: formData.use_trial_division,
          trial_division_limit: parseInt(formData.trial_division_limit) || 10000000,
          use_pollard_rho: formData.use_pollard_rho,
          pollard_rho_iterations: parseInt(formData.pollard_rho_iterations) || 1000000,
          use_ecm: formData.use_ecm,
        },
      })

      router.push(`/job/${job.id}`)
    } catch (error: any) {
      alert(`Failed to create job: ${error.response?.data?.detail || error.message}`)
      setLoading(false)
    }
  }

  const loadExample = (example: typeof EXAMPLES[0]) => {
    setFormData({
      ...formData,
      n: example.n,
      lower_bound: example.bounds?.lower || '',
      upper_bound: example.bounds?.upper || '',
    })
  }

  return (
    <>
      <Head>
        <title>New Factorization Job - SemiPrime Factor</title>
      </Head>

      <div className="min-h-screen bg-gradient-to-br from-gray-50 to-gray-100 dark:from-gray-900 dark:to-gray-800 py-8 px-4">
        <div className="max-w-5xl mx-auto">
          <div className="mb-6">
            <Link href="/">
              <Button variant="secondary" size="sm">← Back to Home</Button>
            </Link>
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            {/* Main Form */}
            <div className="lg:col-span-2">
              <Card>
                <h1 className="text-3xl font-bold mb-2 text-gray-900 dark:text-white">
                  New Factorization Job
                </h1>
                <p className="text-gray-600 dark:text-gray-400 mb-6">
                  Configure and start a new integer factorization job
                </p>

                <form onSubmit={handleSubmit} className="space-y-6">
                  {/* Number Input */}
                  <div>
                    <label className="block text-sm font-medium mb-2 text-gray-900 dark:text-white">
                      Number to Factor (N) <span className="text-red-500">*</span>
                    </label>
                    <textarea
                      className={`input-field font-mono text-sm ${errors.n ? 'border-red-500' : ''}`}
                      rows={3}
                      value={formData.n}
                      onChange={(e) => {
                        setFormData({ ...formData, n: e.target.value })
                        if (errors.n) setErrors({ ...errors, n: '' })
                      }}
                      placeholder="Enter the number to factor (digits only)"
                    />
                    {errors.n && (
                      <p className="mt-1 text-sm text-red-600 dark:text-red-400">{errors.n}</p>
                    )}
                    {formData.n && (
                      <p className="mt-1 text-xs text-gray-500">
                        Length: {formData.n.length} digits
                      </p>
                    )}
                  </div>

                  {/* Mode Selection */}
                  <div>
                    <label className="block text-sm font-medium mb-2 text-gray-900 dark:text-white">
                      Factorization Mode
                    </label>
                    <select
                      className="input-field"
                      value={formData.mode}
                      onChange={(e) => setFormData({ ...formData, mode: e.target.value })}
                    >
                      <option value="auto">Auto (Use All Algorithms)</option>
                      <option value="equation_guided">Equation-Guided Only</option>
                      <option value="range_scan">Range Scan Only</option>
                    </select>
                    <p className="mt-1 text-xs text-gray-500">
                      Auto mode runs algorithms in sequence for best results
                    </p>
                  </div>

                  {/* Bounds */}
                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <label className="block text-sm font-medium mb-2 text-gray-900 dark:text-white">
                        Lower Bound (optional)
                      </label>
                      <input
                        type="text"
                        className="input-field font-mono"
                        value={formData.lower_bound}
                        onChange={(e) => setFormData({ ...formData, lower_bound: e.target.value })}
                        placeholder="e.g., 1e90"
                      />
                    </div>
                    <div>
                      <label className="block text-sm font-medium mb-2 text-gray-900 dark:text-white">
                        Upper Bound (optional)
                      </label>
                      <input
                        type="text"
                        className="input-field font-mono"
                        value={formData.upper_bound}
                        onChange={(e) => setFormData({ ...formData, upper_bound: e.target.value })}
                        placeholder="e.g., 1e130"
                      />
                    </div>
                  </div>

                  {/* Algorithm Toggles */}
                  <div className="border-t border-gray-200 dark:border-gray-700 pt-4">
                    <h3 className="text-lg font-semibold mb-4 text-gray-900 dark:text-white">
                      Algorithm Configuration
                    </h3>

                    <div className="space-y-4">
                      <div className="bg-blue-50 dark:bg-blue-900/20 p-3 rounded-lg">
                        <label className="flex items-start cursor-pointer">
                          <input
                            type="checkbox"
                            checked={formData.use_equation}
                            onChange={(e) => setFormData({ ...formData, use_equation: e.target.checked })}
                            className="mt-1 mr-3"
                          />
                          <div>
                            <span className="text-sm font-medium text-gray-900 dark:text-white">
                              Equation-Based Bounds (Trurl Method)
                            </span>
                            <p className="text-xs text-gray-600 dark:text-gray-400 mt-1">
                              Uses mathematical constraints to narrow search space
                            </p>
                          </div>
                        </label>
                      </div>

                      <div className="bg-green-50 dark:bg-green-900/20 p-3 rounded-lg">
                        <label className="flex items-start cursor-pointer">
                          <input
                            type="checkbox"
                            checked={formData.use_trial_division}
                            onChange={(e) => setFormData({ ...formData, use_trial_division: e.target.checked })}
                            className="mt-1 mr-3"
                          />
                          <div className="flex-1">
                            <span className="text-sm font-medium text-gray-900 dark:text-white">
                              Trial Division
                            </span>
                            <p className="text-xs text-gray-600 dark:text-gray-400 mt-1">
                              Fast for finding small factors
                            </p>
                          </div>
                        </label>
                        {formData.use_trial_division && (
                          <div className="mt-3 ml-6">
                            <label className="block text-xs font-medium mb-1 text-gray-700 dark:text-gray-300">
                              Limit
                            </label>
                            <input
                              type="text"
                              className={`input-field font-mono text-sm ${errors.trial_division_limit ? 'border-red-500' : ''}`}
                              value={formData.trial_division_limit}
                              onChange={(e) => {
                                setFormData({ ...formData, trial_division_limit: e.target.value })
                                if (errors.trial_division_limit) setErrors({ ...errors, trial_division_limit: '' })
                              }}
                              placeholder="10000000"
                            />
                            {errors.trial_division_limit && (
                              <p className="mt-1 text-xs text-red-600">{errors.trial_division_limit}</p>
                            )}
                          </div>
                        )}
                      </div>

                      <div className="bg-purple-50 dark:bg-purple-900/20 p-3 rounded-lg">
                        <label className="flex items-start cursor-pointer">
                          <input
                            type="checkbox"
                            checked={formData.use_pollard_rho}
                            onChange={(e) => setFormData({ ...formData, use_pollard_rho: e.target.checked })}
                            className="mt-1 mr-3"
                          />
                          <div className="flex-1">
                            <span className="text-sm font-medium text-gray-900 dark:text-white">
                              Pollard-Rho Algorithm
                            </span>
                            <p className="text-xs text-gray-600 dark:text-gray-400 mt-1">
                              Probabilistic method for medium factors
                            </p>
                          </div>
                        </label>
                        {formData.use_pollard_rho && (
                          <div className="mt-3 ml-6">
                            <label className="block text-xs font-medium mb-1 text-gray-700 dark:text-gray-300">
                              Iterations
                            </label>
                            <input
                              type="text"
                              className={`input-field font-mono text-sm ${errors.pollard_rho_iterations ? 'border-red-500' : ''}`}
                              value={formData.pollard_rho_iterations}
                              onChange={(e) => {
                                setFormData({ ...formData, pollard_rho_iterations: e.target.value })
                                if (errors.pollard_rho_iterations) setErrors({ ...errors, pollard_rho_iterations: '' })
                              }}
                              placeholder="1000000"
                            />
                            {errors.pollard_rho_iterations && (
                              <p className="mt-1 text-xs text-red-600">{errors.pollard_rho_iterations}</p>
                            )}
                          </div>
                        )}
                      </div>

                      <div className="bg-yellow-50 dark:bg-yellow-900/20 p-3 rounded-lg">
                        <label className="flex items-start cursor-pointer">
                          <input
                            type="checkbox"
                            checked={formData.use_ecm}
                            onChange={(e) => setFormData({ ...formData, use_ecm: e.target.checked })}
                            className="mt-1 mr-3"
                          />
                          <div>
                            <span className="text-sm font-medium text-gray-900 dark:text-white">
                              Elliptic Curve Method (ECM)
                            </span>
                            <p className="text-xs text-gray-600 dark:text-gray-400 mt-1">
                              Powerful for 30-40 digit factors
                            </p>
                          </div>
                        </label>
                      </div>
                    </div>
                  </div>

                  {/* Submit Buttons */}
                  <div className="flex gap-4 pt-4">
                    <Button
                      type="submit"
                      variant="primary"
                      size="lg"
                      loading={loading}
                      className="flex-1"
                    >
                      Start Factorization
                    </Button>
                    <Link href="/">
                      <Button variant="secondary" size="lg">
                        Cancel
                      </Button>
                    </Link>
                  </div>
                </form>
              </Card>
            </div>

            {/* Sidebar */}
            <div className="lg:col-span-1 space-y-6">
              {/* Examples */}
              <Card>
                <h3 className="text-lg font-semibold mb-3 text-gray-900 dark:text-white">
                  Quick Examples
                </h3>
                <div className="space-y-2">
                  {EXAMPLES.map((example, idx) => (
                    <button
                      key={idx}
                      type="button"
                      onClick={() => loadExample(example)}
                      className="w-full text-left p-3 rounded-lg border border-gray-200 dark:border-gray-700 hover:border-blue-500 dark:hover:border-blue-500 hover:bg-blue-50 dark:hover:bg-blue-900/20 transition-colors"
                    >
                      <div className="font-medium text-sm text-gray-900 dark:text-white">
                        {example.name}
                      </div>
                      <div className="text-xs text-gray-500 mt-1">{example.desc}</div>
                    </button>
                  ))}
                </div>
              </Card>

              {/* Tips */}
              <Card>
                <h3 className="text-lg font-semibold mb-3 text-gray-900 dark:text-white">
                  Tips
                </h3>
                <div className="space-y-3 text-sm text-gray-600 dark:text-gray-400">
                  <div className="flex items-start">
                    <span className="mr-2">💡</span>
                    <p>Use Auto mode for best results across all number sizes</p>
                  </div>
                  <div className="flex items-start">
                    <span className="mr-2">⚡</span>
                    <p>Trial Division is fastest for numbers with small factors</p>
                  </div>
                  <div className="flex items-start">
                    <span className="mr-2">🎯</span>
                    <p>Equation-guided search excels with large semiprimes</p>
                  </div>
                  <div className="flex items-start">
                    <span className="mr-2">📊</span>
                    <p>Monitor progress in real-time via WebSocket logs</p>
                  </div>
                </div>
              </Card>

              {/* Algorithm Info */}
              <Card className="bg-gradient-to-br from-blue-50 to-purple-50 dark:from-blue-900/20 dark:to-purple-900/20">
                <h3 className="text-sm font-semibold mb-2 text-gray-900 dark:text-white">
                  About the Algorithms
                </h3>
                <p className="text-xs text-gray-600 dark:text-gray-400">
                  Our system combines traditional methods (Trial Division, Pollard-rho, ECM)
                  with the innovative Trurl equation-guided approach to efficiently factor
                  integers of varying sizes.
                </p>
              </Card>
            </div>
          </div>
        </div>
      </div>
    </>
  )
}
