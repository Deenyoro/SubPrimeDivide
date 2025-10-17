import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts'

interface ProgressDataPoint {
  timestamp: string
  progress: number
}

interface ProgressChartProps {
  data: ProgressDataPoint[]
  height?: number
}

export default function ProgressChart({ data, height = 300 }: ProgressChartProps) {
  return (
    <ResponsiveContainer width="100%" height={height}>
      <LineChart data={data} margin={{ top: 5, right: 30, left: 20, bottom: 5 }}>
        <CartesianGrid strokeDasharray="3 3" className="stroke-gray-300 dark:stroke-gray-600" />
        <XAxis
          dataKey="timestamp"
          className="text-xs fill-gray-600 dark:fill-gray-400"
          tick={{ fill: 'currentColor' }}
        />
        <YAxis
          className="text-xs fill-gray-600 dark:fill-gray-400"
          tick={{ fill: 'currentColor' }}
          domain={[0, 100]}
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
        <Line
          type="monotone"
          dataKey="progress"
          stroke="#3b82f6"
          strokeWidth={2}
          dot={{ fill: '#3b82f6', r: 4 }}
          activeDot={{ r: 6 }}
          name="Progress (%)"
        />
      </LineChart>
    </ResponsiveContainer>
  )
}
