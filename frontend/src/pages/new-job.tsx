import { useState } from 'react'
import Head from 'next/head'
import { useRouter } from 'next/router'
import Link from 'next/link'
import { api } from '@/lib/api'
import Card from '@/components/Card'
import Button from '@/components/Button'
import Badge from '@/components/Badge'

// Miller-Rabin primality test
function isProbablyPrime(n: bigint, k = 5): boolean {
  if (n < 2n) return false
  if (n === 2n || n === 3n) return true
  if (n % 2n === 0n) return false

  // Write n-1 as 2^r * d
  let d = n - 1n
  let r = 0n
  while (d % 2n === 0n) {
    d /= 2n
    r++
  }

  // Witness loop
  witnessLoop: for (let i = 0; i < k; i++) {
    const a = 2n + BigInt(Math.floor(Math.random() * Number(n - 4n)))
    let x = modPow(a, d, n)

    if (x === 1n || x === n - 1n) continue

    for (let j = 0n; j < r - 1n; j++) {
      x = modPow(x, 2n, n)
      if (x === n - 1n) continue witnessLoop
    }
    return false
  }
  return true
}

function modPow(base: bigint, exp: bigint, mod: bigint): bigint {
  let result = 1n
  base = base % mod
  while (exp > 0n) {
    if (exp % 2n === 1n) result = (result * base) % mod
    exp = exp / 2n
    base = (base * base) % mod
  }
  return result
}

function randomBigInt(min: bigint, max: bigint): bigint {
  const range = max - min
  const rangeStr = range.toString()
  const digits = rangeStr.length

  let result: bigint
  do {
    let numStr = ''
    for (let i = 0; i < digits; i++) {
      numStr += Math.floor(Math.random() * 10)
    }
    result = BigInt(numStr)
  } while (result > range)

  return min + result
}

function generateRandomPrime(digitCount: number): bigint {
  const min = 10n ** BigInt(digitCount - 1)
  const max = 10n ** BigInt(digitCount) - 1n

  let attempts = 0
  while (attempts < 1000) {
    let candidate = randomBigInt(min, max)
    // Make sure it's odd
    if (candidate % 2n === 0n) candidate += 1n

    if (isProbablyPrime(candidate)) {
      return candidate
    }
    attempts++
  }

  throw new Error('Failed to generate prime')
}

function generateSemiprime(totalDigits: number): string {
  // For balanced semiprime, each prime should be roughly half the digits
  const primeDigits = Math.floor(totalDigits / 2)

  const p1 = generateRandomPrime(primeDigits)
  const p2 = generateRandomPrime(primeDigits)

  const semiprime = p1 * p2
  return semiprime.toString()
}

const DIFFICULTY_LEVELS = [
  {
    name: '15-Digit Challenge',
    digits: 15,
    desc: 'Prime search (~10-30 min)',
    icon: '🔥',
    color: 'yellow',
    mode: 'equation_guided',
    algorithms: { trial: false, rho: false, ecm: false, equation: true }
  },
  {
    name: '18-Digit Semiprime',
    digits: 18,
    desc: 'Prime iteration (~1-6 hours)',
    icon: '⚡',
    color: 'orange',
    mode: 'equation_guided',
    algorithms: { trial: false, rho: false, ecm: false, equation: true }
  },
  {
    name: '20-Digit Balanced',
    digits: 20,
    desc: 'Trurl search (~12-48 hours)',
    icon: '💪',
    color: 'red',
    mode: 'equation_guided',
    algorithms: { trial: false, rho: false, ecm: false, equation: true }
  },
  {
    name: '25-Digit Monster',
    digits: 25,
    desc: 'Long grind (~3-7 days)',
    icon: '🌋',
    color: 'purple',
    mode: 'equation_guided',
    algorithms: { trial: false, rho: false, ecm: false, equation: true }
  },
  {
    name: '30-Digit Beast',
    digits: 30,
    desc: 'Epic quest (~1-3 weeks)',
    icon: '🏔️',
    color: 'indigo',
    mode: 'equation_guided',
    algorithms: { trial: false, rho: false, ecm: false, equation: true }
  },
  {
    name: '40-Digit Titan',
    digits: 40,
    desc: 'Legendary (~months)',
    icon: '🌌',
    color: 'blue',
    mode: 'equation_guided',
    algorithms: { trial: false, rho: false, ecm: false, equation: true }
  },
  {
    name: '60-Digit ECM Target',
    digits: 60,
    desc: 'ECM algorithm (days-weeks)',
    icon: '🚀',
    color: 'cyan',
    mode: 'full',
    algorithms: { trial: true, rho: true, ecm: true, equation: true }
  },
  {
    name: '80-Digit Challenge',
    digits: 80,
    desc: 'ECM intensive (weeks-months)',
    icon: '🌠',
    color: 'teal',
    mode: 'full',
    algorithms: { trial: true, rho: true, ecm: true, equation: true }
  },
  {
    name: '100-Digit Extreme',
    digits: 100,
    desc: 'Advanced ECM (months)',
    icon: '💫',
    color: 'violet',
    mode: 'full',
    algorithms: { trial: true, rho: true, ecm: true, equation: true }
  },
  {
    name: '150-Digit GNFS',
    digits: 150,
    desc: 'CADO-NFS required (months)',
    icon: '🔮',
    color: 'fuchsia',
    mode: 'full',
    algorithms: { trial: true, rho: true, ecm: true, equation: true }
  },
  {
    name: '200-Digit Ultimate',
    digits: 200,
    desc: 'CADO-NFS extreme (years)',
    icon: '🌟',
    color: 'rose',
    mode: 'full',
    algorithms: { trial: true, rho: true, ecm: true, equation: true }
  },
]

export default function NewJob() {
  const router = useRouter()
  const [loading, setLoading] = useState(false)
  const [errors, setErrors] = useState<Record<string, string>>({})
  const [showCustomGenerator, setShowCustomGenerator] = useState(false)
  const [customDigits, setCustomDigits] = useState('20')
  const [generating, setGenerating] = useState(false)
  const [formData, setFormData] = useState({
    n: '',
    mode: 'equation_guided',
    lower_bound: '',
    upper_bound: '',
    use_equation: true,
    use_trial_division: false,
    trial_division_limit: '10000000',
    use_pollard_rho: false,
    pollard_rho_iterations: '1000000',
    use_shor_classical: false,
    use_ecm: false,
    force_cado_nfs: false,
    use_bpsw: true,
    generate_certificates: false,
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
          use_shor_classical: formData.use_shor_classical,
          use_ecm: formData.use_ecm,
          force_cado_nfs: formData.force_cado_nfs,
          use_bpsw: formData.use_bpsw,
          generate_certificates: formData.generate_certificates,
        },
      })

      router.push(`/job/${job.id}`)
    } catch (error: any) {
      alert(`Failed to create job: ${error.response?.data?.detail || error.message}`)
      setLoading(false)
    }
  }

  const loadExample = (difficulty: typeof DIFFICULTY_LEVELS[0]) => {
    try {
      // Generate a fresh random semiprime
      const semiprime = generateSemiprime(difficulty.digits)

      // Only fill in the number - preserve user's algorithm selections
      setFormData({
        ...formData,
        n: semiprime,
      })
    } catch (error) {
      alert('Failed to generate random semiprime. Please try again.')
      console.error(error)
    }
  }

  const generateCustom = () => {
    const digits = parseInt(customDigits)
    if (isNaN(digits) || digits < 10 || digits > 300) {
      alert('Please enter a digit count between 10 and 300')
      return
    }

    setGenerating(true)
    try {
      const semiprime = generateSemiprime(digits)
      // Only fill in the number - preserve user's algorithm selections
      setFormData({
        ...formData,
        n: semiprime,
      })
      setShowCustomGenerator(false)
    } catch (error) {
      alert('Failed to generate random semiprime. Please try again.')
      console.error(error)
    } finally {
      setGenerating(false)
    }
  }

  const getDifficultyWarning = (digits: number) => {
    if (digits < 15) return { level: 'easy', text: 'Prime search (~minutes to hours)', color: 'text-green-600 dark:text-green-400' }
    if (digits < 20) return { level: 'medium', text: 'Equation-guided (~hours to half-day)', color: 'text-yellow-600 dark:text-yellow-400' }
    if (digits < 25) return { level: 'hard', text: 'Long search (~1-3 days)', color: 'text-orange-600 dark:text-orange-400' }
    if (digits < 35) return { level: 'very-hard', text: 'Epic grind (~weeks)', color: 'text-red-600 dark:text-red-400' }
    if (digits < 50) return { level: 'extreme', text: 'Legendary quest (~months)', color: 'text-purple-600 dark:text-purple-400' }
    if (digits < 80) return { level: 'ecm', text: 'ECM algorithm required (~weeks to months)', color: 'text-cyan-600 dark:text-cyan-400' }
    if (digits < 120) return { level: 'advanced-ecm', text: 'Advanced ECM (~months)', color: 'text-violet-600 dark:text-violet-400' }
    if (digits < 180) return { level: 'gnfs', text: 'CADO-NFS GNFS required (~months to year)', color: 'text-fuchsia-600 dark:text-fuchsia-400' }
    return { level: 'ultimate', text: 'CADO-NFS extreme factorization (~years)', color: 'text-rose-600 dark:text-rose-400' }
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

                      <div className="bg-cyan-50 dark:bg-cyan-900/20 p-3 rounded-lg">
                        <label className="flex items-start cursor-pointer">
                          <input
                            type="checkbox"
                            checked={formData.use_shor_classical}
                            onChange={(e) => setFormData({ ...formData, use_shor_classical: e.target.checked })}
                            className="mt-1 mr-3"
                          />
                          <div>
                            <span className="text-sm font-medium text-gray-900 dark:text-white">
                              Shor's Algorithm (Classical Emulation)
                            </span>
                            <p className="text-xs text-gray-600 dark:text-gray-400 mt-1">
                              Classical order-finding for smooth orders (research/educational)
                            </p>
                          </div>
                        </label>
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

                      <div className="bg-fuchsia-50 dark:bg-fuchsia-900/20 p-3 rounded-lg">
                        <label className="flex items-start cursor-pointer">
                          <input
                            type="checkbox"
                            checked={formData.force_cado_nfs}
                            onChange={(e) => setFormData({ ...formData, force_cado_nfs: e.target.checked })}
                            className="mt-1 mr-3"
                          />
                          <div>
                            <span className="text-sm font-medium text-gray-900 dark:text-white">
                              Force CADO-NFS (GNFS)
                            </span>
                            <p className="text-xs text-gray-600 dark:text-gray-400 mt-1">
                              Force General Number Field Sieve for numbers &lt; 200 digits (extremely intensive)
                            </p>
                          </div>
                        </label>
                      </div>

                      <div className="bg-indigo-50 dark:bg-indigo-900/20 p-3 rounded-lg">
                        <label className="flex items-start cursor-pointer">
                          <input
                            type="checkbox"
                            checked={formData.use_bpsw}
                            onChange={(e) => setFormData({ ...formData, use_bpsw: e.target.checked })}
                            className="mt-1 mr-3"
                          />
                          <div>
                            <span className="text-sm font-medium text-gray-900 dark:text-white">
                              BPSW Primality Test
                            </span>
                            <p className="text-xs text-gray-600 dark:text-gray-400 mt-1">
                              More rigorous primality testing (recommended for large numbers)
                            </p>
                          </div>
                        </label>
                      </div>

                      <div className="bg-pink-50 dark:bg-pink-900/20 p-3 rounded-lg">
                        <label className="flex items-start cursor-pointer">
                          <input
                            type="checkbox"
                            checked={formData.generate_certificates}
                            onChange={(e) => setFormData({ ...formData, generate_certificates: e.target.checked })}
                            className="mt-1 mr-3"
                          />
                          <div>
                            <span className="text-sm font-medium text-gray-900 dark:text-white">
                              Generate Primality Certificates
                            </span>
                            <p className="text-xs text-gray-600 dark:text-gray-400 mt-1">
                              Create verifiable proofs for prime factors (slower but provides cryptographic proof)
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
                <h3 className="text-lg font-semibold mb-3 text-gray-900 dark:text-white flex items-center gap-2">
                  <span className="text-2xl">🚀</span>
                  Quick Examples
                </h3>
                <p className="text-xs text-gray-500 dark:text-gray-400 mb-4">
                  Click any example to auto-fill the form
                </p>

                {/* Custom Generator Button */}
                <button
                  type="button"
                  onClick={() => setShowCustomGenerator(true)}
                  className="w-full mb-4 p-3 rounded-lg border-2 border-dashed border-purple-400 dark:border-purple-600 bg-purple-50 dark:bg-purple-900/20 hover:bg-purple-100 dark:hover:bg-purple-900/30 transition-all duration-200 hover:shadow-md group"
                >
                  <div className="flex items-center justify-center gap-2">
                    <span className="text-2xl group-hover:scale-110 transition-transform">🎲</span>
                    <div className="font-medium text-purple-700 dark:text-purple-300">
                      Custom Random Generator
                    </div>
                  </div>
                  <div className="text-xs text-purple-600 dark:text-purple-400 mt-1">
                    Choose your own digit count
                  </div>
                </button>
                <div className="space-y-2 max-h-96 overflow-y-auto">
                  {DIFFICULTY_LEVELS.map((difficulty, idx) => (
                    <button
                      key={idx}
                      type="button"
                      onClick={() => loadExample(difficulty)}
                      className={`w-full text-left p-3 rounded-lg border-2 border-gray-200 dark:border-gray-700 hover:border-${difficulty.color}-500 dark:hover:border-${difficulty.color}-500 hover:bg-${difficulty.color}-50 dark:hover:bg-${difficulty.color}-900/20 transition-all duration-200 hover:shadow-md hover:scale-102 group`}
                    >
                      <div className="flex items-center gap-2">
                        <span className="text-xl group-hover:scale-110 transition-transform">{difficulty.icon}</span>
                        <div className="flex-1">
                          <div className="flex items-center gap-2 mb-1">
                            <div className="font-medium text-sm text-gray-900 dark:text-white">
                              {difficulty.name}
                            </div>
                            <span className="text-xs bg-purple-500 text-white px-1.5 py-0.5 rounded font-medium">
                              Random
                            </span>
                          </div>
                          <div className="text-xs text-gray-500 dark:text-gray-400">{difficulty.desc}</div>
                        </div>
                      </div>
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
                    <span className="mr-2">🎲</span>
                    <p>Challenges generate <strong className="text-gray-900 dark:text-white">random balanced semiprimes</strong> - click again for a different number</p>
                  </div>
                  <div className="flex items-start">
                    <span className="mr-2">⏱️</span>
                    <p><strong className="text-gray-900 dark:text-white">Default: Trurl equation-guided only</strong> - designed for multi-day computational runs</p>
                  </div>
                  <div className="flex items-start">
                    <span className="mr-2">⚡</span>
                    <p><strong className="text-gray-900 dark:text-white">Want instant results?</strong> Enable fast algorithms (Trial Division, Pollard-rho, ECM) below</p>
                  </div>
                  <div className="flex items-start">
                    <span className="mr-2">🎛️</span>
                    <p><strong className="text-gray-900 dark:text-white">YOU control which algorithms run</strong> - toggle checkboxes to enable/disable methods</p>
                  </div>
                  <div className="flex items-start">
                    <span className="mr-2">📊</span>
                    <p>Check individual algorithm progress in job logs - see which methods found factors and when</p>
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
                  with cutting-edge approaches like Shor's algorithm (classical emulation) and
                  the innovative Trurl equation-guided method to efficiently factor integers
                  of varying sizes.
                </p>
              </Card>
            </div>
          </div>
        </div>
      </div>

      {/* Custom Generator Modal */}
      {showCustomGenerator && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
          <div className="bg-white dark:bg-gray-800 rounded-xl shadow-2xl max-w-md w-full p-6 animate-scale-in">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-2xl font-bold text-gray-900 dark:text-white flex items-center gap-2">
                <span className="text-3xl">🎲</span>
                Custom Generator
              </h2>
              <button
                onClick={() => setShowCustomGenerator(false)}
                className="text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-200"
              >
                <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            </div>

            <p className="text-sm text-gray-600 dark:text-gray-400 mb-6">
              Generate a random balanced semiprime with custom digit count
            </p>

            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium mb-2 text-gray-900 dark:text-white">
                  Digit Count
                </label>
                <input
                  type="number"
                  min="10"
                  max="300"
                  value={customDigits}
                  onChange={(e) => setCustomDigits(e.target.value)}
                  className="input-field w-full text-center text-2xl font-bold"
                  placeholder="20"
                />
                <p className="mt-1 text-xs text-gray-500 dark:text-gray-400">
                  Range: 10-300 digits
                </p>
              </div>

              {/* Difficulty Warning */}
              {customDigits && !isNaN(parseInt(customDigits)) && (
                <div className={`p-4 rounded-lg border-2 ${
                  parseInt(customDigits) < 15 ? 'bg-green-50 dark:bg-green-900/20 border-green-300 dark:border-green-700' :
                  parseInt(customDigits) < 20 ? 'bg-yellow-50 dark:bg-yellow-900/20 border-yellow-300 dark:border-yellow-700' :
                  parseInt(customDigits) < 25 ? 'bg-orange-50 dark:bg-orange-900/20 border-orange-300 dark:border-orange-700' :
                  parseInt(customDigits) < 35 ? 'bg-red-50 dark:bg-red-900/20 border-red-300 dark:border-red-700' :
                  parseInt(customDigits) < 50 ? 'bg-purple-50 dark:bg-purple-900/20 border-purple-300 dark:border-purple-700' :
                  parseInt(customDigits) < 80 ? 'bg-cyan-50 dark:bg-cyan-900/20 border-cyan-300 dark:border-cyan-700' :
                  parseInt(customDigits) < 120 ? 'bg-violet-50 dark:bg-violet-900/20 border-violet-300 dark:border-violet-700' :
                  parseInt(customDigits) < 180 ? 'bg-fuchsia-50 dark:bg-fuchsia-900/20 border-fuchsia-300 dark:border-fuchsia-700' :
                  'bg-rose-50 dark:bg-rose-900/20 border-rose-300 dark:border-rose-700'
                }`}>
                  <div className="flex items-start gap-2">
                    <span className="text-xl">
                      {parseInt(customDigits) < 15 ? '✅' :
                       parseInt(customDigits) < 20 ? '⚠️' :
                       parseInt(customDigits) < 25 ? '🔥' :
                       parseInt(customDigits) < 35 ? '💀' :
                       parseInt(customDigits) < 50 ? '🌋' :
                       parseInt(customDigits) < 80 ? '🚀' :
                       parseInt(customDigits) < 120 ? '💫' :
                       parseInt(customDigits) < 180 ? '🔮' : '🌟'}
                    </span>
                    <div>
                      <div className={`font-semibold text-sm ${getDifficultyWarning(parseInt(customDigits)).color}`}>
                        {getDifficultyWarning(parseInt(customDigits)).level.toUpperCase().replace('-', ' ')}
                      </div>
                      <div className="text-xs text-gray-600 dark:text-gray-400 mt-1">
                        {getDifficultyWarning(parseInt(customDigits)).text}
                      </div>
                    </div>
                  </div>
                </div>
              )}

              <div className="bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-lg p-3">
                <div className="text-xs text-blue-800 dark:text-blue-300 space-y-1">
                  <div className="flex items-start gap-2">
                    <span>•</span>
                    <span>Generates two random primes of equal size</span>
                  </div>
                  <div className="flex items-start gap-2">
                    <span>•</span>
                    <span>Multiplies them to create a balanced semiprime</span>
                  </div>
                  <div className="flex items-start gap-2">
                    <span>•</span>
                    <span>Auto-configures optimal algorithms for difficulty</span>
                  </div>
                </div>
              </div>

              <div className="flex gap-3 pt-2">
                <Button
                  onClick={generateCustom}
                  variant="primary"
                  className="flex-1"
                  loading={generating}
                  disabled={generating || parseInt(customDigits) < 10 || parseInt(customDigits) > 300 || isNaN(parseInt(customDigits))}
                >
                  {generating ? 'Generating...' : 'Generate & Fill Form'}
                </Button>
                <Button
                  onClick={() => setShowCustomGenerator(false)}
                  variant="secondary"
                  disabled={generating}
                >
                  Cancel
                </Button>
              </div>
            </div>
          </div>
        </div>
      )}
    </>
  )
}
