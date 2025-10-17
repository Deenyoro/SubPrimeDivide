interface ProgressBarProps {
  percent: number
  showLabel?: boolean
  size?: 'sm' | 'md' | 'lg'
  color?: 'blue' | 'green' | 'yellow' | 'red'
}

export default function ProgressBar({
  percent,
  showLabel = true,
  size = 'md',
  color = 'blue',
}: ProgressBarProps) {
  const heights = {
    sm: 'h-1',
    md: 'h-2',
    lg: 'h-3',
  }

  const colors = {
    blue: 'bg-blue-600',
    green: 'bg-green-600',
    yellow: 'bg-yellow-600',
    red: 'bg-red-600',
  }

  return (
    <div className="flex items-center gap-2 w-full">
      <div className={`flex-1 bg-gray-200 dark:bg-gray-700 rounded-full ${heights[size]}`}>
        <div
          className={`${colors[color]} ${heights[size]} rounded-full transition-all duration-300`}
          style={{ width: `${Math.min(100, Math.max(0, percent))}%` }}
        ></div>
      </div>
      {showLabel && (
        <span className="text-xs text-gray-600 dark:text-gray-400 min-w-[3rem] text-right">
          {percent.toFixed(1)}%
        </span>
      )}
    </div>
  )
}
