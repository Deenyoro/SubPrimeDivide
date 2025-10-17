import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, ReferenceLine } from 'recharts'

interface EquationPoint {
  x: number
  y: number
  label?: string
}

interface EquationCurveChartProps {
  data: EquationPoint[]
  xWhenYEquals1?: number
  actualFactor?: number
  height?: number
  title?: string
}

export default function EquationCurveChart({
  data,
  xWhenYEquals1,
  actualFactor,
  height = 400,
  title = "Trurl Equation Curve"
}: EquationCurveChartProps) {
  return (
    <div>
      {title && (
        <h3 className="text-lg font-semibold mb-3 text-gray-900 dark:text-white text-center">
          {title}
        </h3>
      )}
      <ResponsiveContainer width="100%" height={height}>
        <LineChart data={data} margin={{ top: 5, right: 30, left: 20, bottom: 5 }}>
          <CartesianGrid strokeDasharray="3 3" className="stroke-gray-300 dark:stroke-gray-600" />
          <XAxis
            dataKey="x"
            className="text-xs fill-gray-600 dark:fill-gray-400"
            tick={{ fill: 'currentColor' }}
            label={{ value: 'x (potential factor)', position: 'insideBottom', offset: -5 }}
            type="number"
            domain={['dataMin', 'dataMax']}
          />
          <YAxis
            dataKey="y"
            className="text-xs fill-gray-600 dark:fill-gray-400"
            tick={{ fill: 'currentColor' }}
            label={{ value: 'y = f(x)', angle: -90, position: 'insideLeft' }}
            type="number"
            domain={['auto', 'auto']}
          />
          <Tooltip
            contentStyle={{
              backgroundColor: 'rgba(0, 0, 0, 0.8)',
              border: 'none',
              borderRadius: '8px',
              color: '#fff'
            }}
            formatter={(value: any) => {
              if (typeof value === 'number') {
                return value.toExponential(4)
              }
              return value
            }}
          />
          <Legend />

          {/* Main equation curve */}
          <Line
            type="monotone"
            dataKey="y"
            stroke="#3b82f6"
            strokeWidth={2}
            dot={false}
            name="Equation Curve"
          />

          {/* Reference line where y = 1 */}
          <ReferenceLine y={1} stroke="#ef4444" strokeDasharray="5 5" label="y = 1" />

          {/* X value where y = 1 */}
          {xWhenYEquals1 && (
            <ReferenceLine
              x={xWhenYEquals1}
              stroke="#10b981"
              strokeDasharray="5 5"
              label={{ value: `x = ${xWhenYEquals1.toExponential(2)}`, position: 'top' }}
            />
          )}

          {/* Actual factor if known */}
          {actualFactor && (
            <ReferenceLine
              x={actualFactor}
              stroke="#f59e0b"
              strokeDasharray="3 3"
              label={{ value: `Actual: ${actualFactor}`, position: 'top' }}
            />
          )}
        </LineChart>
      </ResponsiveContainer>

      {/* Legend explanation */}
      <div className="mt-4 text-sm text-gray-600 dark:text-gray-400 space-y-1">
        <p><span className="text-blue-600 dark:text-blue-400">Blue curve</span>: Trurl equation y = (((pnp²/x) + x²) / pnp)</p>
        {xWhenYEquals1 && (
          <p><span className="text-green-600 dark:text-green-400">Green line</span>: x where y = 1 (search starting point)</p>
        )}
        {actualFactor && (
          <p><span className="text-yellow-600 dark:text-yellow-400">Orange line</span>: Actual factor location</p>
        )}
      </div>
    </div>
  )
}
