import { useState, useEffect } from 'react'
import { logsApi } from '@/lib/api'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table'
import { useToast } from '@/components/ui/use-toast'
import { formatRelativeTime } from '@/lib/utils'
import { Search, Download, ChevronLeft, ChevronRight, AlertCircle, Info, AlertTriangle } from 'lucide-react'

const LOG_LEVELS = ['debug', 'info', 'warning', 'error']

export default function Logs() {
  const [logs, setLogs] = useState<any[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [search, setSearch] = useState('')
  const [level, setLevel] = useState('')
  const [page, setPage] = useState(1)
  const [totalPages, setTotalPages] = useState(1)
  const { toast } = useToast()

  useEffect(() => {
    fetchLogs()
  }, [page, search, level])

  const fetchLogs = async () => {
    setIsLoading(true)
    try {
      const response = await logsApi.list({
        page,
        page_size: 50,
        search: search || undefined,
        level: level || undefined,
      })
      setLogs(response.items)
      setTotalPages(response.total_pages)
    } catch (error) {
      toast({
        variant: 'destructive',
        title: 'Failed to load logs',
      })
    } finally {
      setIsLoading(false)
    }
  }

  const handleExport = async () => {
    try {
      const blob = await logsApi.export({ search, level })
      const url = window.URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = `continuum-logs-${Date.now()}.json`
      a.click()
      window.URL.revokeObjectURL(url)
    } catch (error) {
      toast({
        variant: 'destructive',
        title: 'Failed to export logs',
      })
    }
  }

  const getLevelIcon = (logLevel: string) => {
    switch (logLevel) {
      case 'error':
        return <AlertCircle className="h-4 w-4 text-red-400" />
      case 'warning':
        return <AlertTriangle className="h-4 w-4 text-yellow-400" />
      case 'info':
        return <Info className="h-4 w-4 text-blue-400" />
      default:
        return <Info className="h-4 w-4 text-gray-400" />
    }
  }

  const getLevelColor = (logLevel: string) => {
    switch (logLevel) {
      case 'error':
        return 'text-red-400'
      case 'warning':
        return 'text-yellow-400'
      case 'info':
        return 'text-blue-400'
      default:
        return 'text-gray-400'
    }
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-white">Audit Logs</h1>
          <p className="text-gray-400 mt-1">System activity and error logs</p>
        </div>
        <Button variant="outline" onClick={handleExport}>
          <Download className="mr-2 h-4 w-4" />
          Export
        </Button>
      </div>

      {/* Search and Filters */}
      <Card className="border-twilight-purple/20 bg-twilight-dark/50">
        <CardContent className="pt-6">
          <div className="flex items-center space-x-2">
            <div className="relative flex-1">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-gray-400" />
              <Input
                placeholder="Search logs..."
                value={search}
                onChange={(e) => setSearch(e.target.value)}
                className="pl-10 bg-twilight-medium border-twilight-purple/20"
              />
            </div>
            <div className="flex space-x-2">
              <Button
                variant={level === '' ? 'default' : 'outline'}
                onClick={() => setLevel('')}
              >
                All
              </Button>
              {LOG_LEVELS.map((l) => (
                <Button
                  key={l}
                  variant={level === l ? 'default' : 'outline'}
                  onClick={() => setLevel(l)}
                >
                  {l}
                </Button>
              ))}
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Logs Table */}
      <Card className="border-twilight-purple/20 bg-twilight-dark/50">
        <CardHeader>
          <CardTitle>Recent Logs ({logs.length})</CardTitle>
        </CardHeader>
        <CardContent>
          {isLoading ? (
            <div className="space-y-2">
              {[...Array(10)].map((_, i) => (
                <div key={i} className="h-12 skeleton rounded" />
              ))}
            </div>
          ) : (
            <>
              <div className="space-y-2">
                {logs.map((log, index) => (
                  <div
                    key={index}
                    className="flex items-start space-x-3 p-3 rounded bg-twilight-medium/30 hover:bg-twilight-medium/50 transition-colors"
                  >
                    <div className="mt-1">{getLevelIcon(log.level)}</div>
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center space-x-2">
                        <span className={`text-sm font-medium ${getLevelColor(log.level)}`}>
                          {log.level.toUpperCase()}
                        </span>
                        <span className="text-xs text-gray-500">
                          {formatRelativeTime(log.timestamp)}
                        </span>
                      </div>
                      <p className="text-sm mt-1">{log.message}</p>
                      {log.metadata && (
                        <details className="mt-2">
                          <summary className="text-xs text-gray-400 cursor-pointer">
                            Show details
                          </summary>
                          <pre className="text-xs text-gray-400 mt-2 p-2 bg-twilight-dark rounded overflow-x-auto">
                            {JSON.stringify(log.metadata, null, 2)}
                          </pre>
                        </details>
                      )}
                    </div>
                  </div>
                ))}
              </div>

              {/* Pagination */}
              <div className="flex items-center justify-between mt-4">
                <p className="text-sm text-gray-400">
                  Page {page} of {totalPages}
                </p>
                <div className="flex space-x-2">
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => setPage(page - 1)}
                    disabled={page === 1}
                  >
                    <ChevronLeft className="h-4 w-4" />
                  </Button>
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => setPage(page + 1)}
                    disabled={page === totalPages}
                  >
                    <ChevronRight className="h-4 w-4" />
                  </Button>
                </div>
              </div>
            </>
          )}
        </CardContent>
      </Card>
    </div>
  )
}
