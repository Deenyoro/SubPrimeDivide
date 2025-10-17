import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, Cell } from 'recharts'

interface AlgorithmData {
  name: string
  timeSeconds: number
  factorsFound: number
}

interface AlgorithmPerformanceChartProps {
  data: AlgorithmData[]
  height?: number
}

const COLORS = ['#3b82f6', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6']

export default function AlgorithmPerformanceChart({ data, height = 300 }: AlgorithmPerformanceChartProps) {
  return (
    <ResponsiveContainer width="100%" height={height}>
      <BarChart data={data} margin={{ top: 5, right: 30, left: 20, bottom: 5 }}>
        <CartesianGrid strokeDasharray="3 3" className="stroke-gray-300 dark:stroke-gray-600" />
        <XAxis
          dataKey="name"
          className="text-xs fill-gray-600 dark:fill-gray-400"
          tick={{ fill: 'currentColor' }}
          angle={-45}
          textAnchor="end"
          height={80}
        />
        <YAxis
          className="text-xs fill-gray-600 dark:fill-gray-400"
          tick={{ fill: 'currentColor' }}
          label={{ value: 'Time (seconds)', angle: -90, position: 'insideLeft' }}
        />
        <Tooltip
          contentStyle={{
            backgroundColor: 'rgba(0, 0, 0, 0.8)',
            border: 'none',
            borderRadius: '8px',
            color: '#fff'
          }}
        />
        <Legend />
        <Bar dataKey="timeSeconds" name="Time (seconds)" radius={[8, 8, 0, 0]}>
          {data.map((entry, index) => (
            <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
          ))}
        </Bar>
      </BarChart>
    </ResponsiveContainer>
  )
}
