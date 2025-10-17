import Badge from './Badge'

interface StatusBadgeProps {
  status: 'pending' | 'running' | 'paused' | 'completed' | 'failed' | 'cancelled'
}

export default function StatusBadge({ status }: StatusBadgeProps) {
  const statusConfig = {
    pending: { variant: 'default' as const, text: 'Pending', icon: '⏳' },
    running: { variant: 'info' as const, text: 'Running', icon: '▶' },
    paused: { variant: 'warning' as const, text: 'Paused', icon: '⏸' },
    completed: { variant: 'success' as const, text: 'Completed', icon: '✓' },
    failed: { variant: 'error' as const, text: 'Failed', icon: '✗' },
    cancelled: { variant: 'default' as const, text: 'Cancelled', icon: '⊘' },
  }

  const config = statusConfig[status]

  return (
    <Badge variant={config.variant}>
      <span className="mr-1">{config.icon}</span>
      {config.text}
    </Badge>
  )
}
