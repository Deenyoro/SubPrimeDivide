import { useEffect, useRef, useState } from 'react'
import { JobLog } from '@/lib/api'

interface LogViewerProps {
  logs: JobLog[]
  autoScroll?: boolean
  maxHeight?: string
}

export default function LogViewer({ logs, autoScroll = true, maxHeight = '600px' }: LogViewerProps) {
  const containerRef = useRef<HTMLDivElement>(null)
  const [searchTerm, setSearchTerm] = useState('')
  const [levelFilter, setLevelFilter] = useState<string>('ALL')
  const [isAutoScroll, setIsAutoScroll] = useState(autoScroll)

  useEffect(() => {
    if (isAutoScroll && containerRef.current) {
      containerRef.current.scrollTop = containerRef.current.scrollHeight
    }
  }, [logs, isAutoScroll])

  const getLevelColor = (level: string) => {
    switch (level) {
      case 'ERROR':
        return 'text-red-500'
      case 'WARNING':
        return 'text-yellow-400'
      case 'INFO':
      default:
        return 'text-green-400'
    }
  }

  const getLevelBg = (level: string) => {
    switch (level) {
      case 'ERROR':
        return 'bg-red-900/30 border-l-2 border-red-500'
      case 'WARNING':
        return 'bg-yellow-900/30 border-l-2 border-yellow-500'
      case 'INFO':
      default:
        return 'hover:bg-gray-800/50'
    }
  }

  const getLevelIcon = (level: string) => {
    switch (level) {
      case 'ERROR':
        return (
          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
        )
      case 'WARNING':
        return (
          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
          </svg>
        )
      case 'INFO':
      default:
        return (
          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
        )
    }
  }

  const filteredLogs = logs.filter(log => {
    // Filter out logs with no message
    if (!log.message || log.message.trim() === '') return false

    const matchesSearch = searchTerm === '' ||
      log.message.toLowerCase().includes(searchTerm.toLowerCase()) ||
      (log.stage && log.stage.toLowerCase().includes(searchTerm.toLowerCase()))

    const matchesLevel = levelFilter === 'ALL' || log.level === levelFilter

    return matchesSearch && matchesLevel
  })

  return (
    <div className="space-y-3">
      {/* Controls */}
      <div className="flex flex-wrap gap-3 items-center justify-between bg-gray-800 rounded-lg p-3">
        <div className="flex-1 min-w-[200px]">
          <div className="relative">
            <input
              type="text"
              placeholder="Search logs..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="w-full bg-gray-900 text-gray-100 border border-gray-700 rounded-lg px-3 py-2 pl-10 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 transition-all"
            />
            <svg className="absolute left-3 top-2.5 w-4 h-4 text-gray-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
            </svg>
          </div>
        </div>

        <div className="flex gap-2 items-center">
          <select
            value={levelFilter}
            onChange={(e) => setLevelFilter(e.target.value)}
            className="bg-gray-900 text-gray-100 border border-gray-700 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            <option value="ALL">All Levels</option>
            <option value="INFO">Info</option>
            <option value="WARNING">Warning</option>
            <option value="ERROR">Error</option>
          </select>

          <button
            onClick={() => setIsAutoScroll(!isAutoScroll)}
            className={`px-3 py-2 rounded-lg text-sm font-medium transition-all ${
              isAutoScroll
                ? 'bg-blue-600 text-white'
                : 'bg-gray-700 text-gray-300 hover:bg-gray-600'
            }`}
          >
            <svg className="w-4 h-4 inline-block mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 14l-7 7m0 0l-7-7m7 7V3" />
            </svg>
            Auto-scroll
          </button>
        </div>
      </div>

      {/* Log Content */}
      <div
        ref={containerRef}
        className="bg-gray-900 text-gray-100 rounded-lg p-4 font-mono text-sm overflow-y-auto custom-scrollbar shadow-inner"
        style={{ maxHeight }}
      >
        {filteredLogs.length === 0 ? (
          <div className="text-center py-12">
            <div className="inline-flex items-center justify-center w-16 h-16 bg-gray-800 rounded-full mb-3">
              <svg className="w-8 h-8 text-gray-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
              </svg>
            </div>
            <p className="text-gray-500">
              {logs.length === 0 ? 'No logs yet...' : 'No logs match your filters'}
            </p>
            {searchTerm && (
              <button
                onClick={() => setSearchTerm('')}
                className="mt-2 text-blue-400 hover:text-blue-300 text-sm"
              >
                Clear search
              </button>
            )}
          </div>
        ) : (
          <div className="space-y-1">
            {filteredLogs.map((log, index) => (
              <div
                key={log.id || index}
                className={`py-2 px-3 rounded transition-all duration-150 ${getLevelBg(log.level)}`}
              >
                <div className="flex items-start gap-2">
                  <span className={`mt-0.5 ${getLevelColor(log.level)}`}>
                    {getLevelIcon(log.level)}
                  </span>
                  <div className="flex-1 min-w-0">
                    <div className="flex flex-wrap items-baseline gap-2">
                      <span className="text-gray-500 text-xs whitespace-nowrap">
                        {log.created_at ? new Date(log.created_at).toLocaleTimeString() : 'N/A'}
                      </span>
                      <span className={`font-semibold text-xs ${getLevelColor(log.level)}`}>
                        {log.level || 'INFO'}
                      </span>
                      {log.stage && (
                        <span className="text-blue-400 text-xs bg-blue-900/30 px-2 py-0.5 rounded">
                          {log.stage}
                        </span>
                      )}
                    </div>
                    <div className="text-gray-200 mt-1 break-words">{log.message || '(no message)'}</div>
                    {log.payload && (
                      <details className="mt-2">
                        <summary className="text-gray-400 text-xs cursor-pointer hover:text-gray-300">
                          View payload
                        </summary>
                        <pre className="mt-2 text-xs text-gray-400 bg-gray-950/50 p-2 rounded overflow-x-auto">
                          {JSON.stringify(log.payload, null, 2)}
                        </pre>
                      </details>
                    )}
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Stats */}
      <div className="flex justify-between items-center text-xs text-gray-500 px-2">
        <span>{filteredLogs.length} of {logs.length} logs</span>
        {searchTerm && (
          <span className="text-blue-400">Filtered by: "{searchTerm}"</span>
        )}
      </div>
    </div>
  )
}
