import { AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts'

interface TimeSeriesDataPoint {
  time: string
  value: number
  label?: string
}

interface TimeSeriesChartProps {
  data: TimeSeriesDataPoint[]
  dataKey?: string
  color?: string
  height?: number
  title?: string
  yLabel?: string
}

export default function TimeSeriesChart({
  data,
  dataKey = 'value',
  color = '#3b82f6',
  height = 300,
  title,
  yLabel
}: TimeSeriesChartProps) {
  return (
    <div>
      {title && (
        <h3 className="text-lg font-semibold mb-3 text-gray-900 dark:text-white">
          {title}
        </h3>
      )}
      <ResponsiveContainer width="100%" height={height}>
        <AreaChart data={data} margin={{ top: 10, right: 30, left: 0, bottom: 0 }}>
          <defs>
            <linearGradient id="colorValue" x1="0" y1="0" x2="0" y2="1">
              <stop offset="5%" stopColor={color} stopOpacity={0.8}/>
              <stop offset="95%" stopColor={color} stopOpacity={0}/>
            </linearGradient>
          </defs>
          <CartesianGrid strokeDasharray="3 3" className="stroke-gray-300 dark:stroke-gray-600" />
          <XAxis
            dataKey="time"
            className="text-xs fill-gray-600 dark:fill-gray-400"
            tick={{ fill: 'currentColor' }}
          />
          <YAxis
            className="text-xs fill-gray-600 dark:fill-gray-400"
            tick={{ fill: 'currentColor' }}
            label={yLabel ? { value: yLabel, angle: -90, position: 'insideLeft' } : undefined}
          />
          <Tooltip
            contentStyle={{
              backgroundColor: 'rgba(0, 0, 0, 0.8)',
              border: 'none',
              borderRadius: '8px',
              color: '#fff'
            }}
          />
          <Area
            type="monotone"
            dataKey={dataKey}
            stroke={color}
            fillOpacity={1}
            fill="url(#colorValue)"
          />
        </AreaChart>
      </ResponsiveContainer>
    </div>
  )
}
